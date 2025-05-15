import base64
import contextlib
import io
import os
import re
import json
import warnings
import sys
import pandas as pd

from PIL import Image
from groq import Groq
from sqlalchemy import create_engine
from e2b_code_interpreter import Sandbox

from django.conf import settings


GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

DATABASE_CONNECTION = {
    "host": settings.DATABASES["default"]["HOST"],
    "database": settings.DATABASES["default"]["NAME"],
    "user": settings.DATABASES["default"]["USER"],
    "password": settings.DATABASES["default"]["PASSWORD"],
    "port": settings.DATABASES["default"]["PORT"],
}


SCHEMA_DESCRIPTION = """
This postgres database Schema is as follows:

Model: backend_company
- id: Primary key of Company model.
- name: Company name.
- phone_number: Company phone number.
- api_token: Company API token.
- instance_id: Company instance id.
- webhook_token: Company webhook token.

Model: backend_order
- id: Primary key of Order model.
- company_id Foreign key to Company model.
- branch_name: Branch name.
- number: Order number.
- details: Order details.
- order_at: Order date and time.
- customer_name: Customer name.
- customer_phone_number: Customer phone number.
- order_details: Order details in JSON format.
- created_at: Order creation date and time.
- updated_at: Order update date and time.

Model: backend_questiontemplate
- id: Primary key of QuestionTemplate model.
- order_id: Foreign key to Order model.
- question: Question text.
- priority: Question priority.
- answer: Answer text.
- audio: Link to audio file.
- created_at: Question creation date and time.
- updated_at: Question update date and time.

Model: backend_analytics
- id: Primary key of Analytics model.
- order_id: Foreign key to Order model.
- sentiment_label: Sentiment label.
- emotions: List of emotions detected.
- products: List of products detected.
- created_at: Analytics creation date and time.
- updated_at: Analytics update date and time.
"""


class SQLGeneratorAgent:
    def __init__(self):

        self.schema = SCHEMA_DESCRIPTION
        self.connection_url = self.build_sqlalchemy_url()
        self.llm = Groq(api_key=GROQ_API_KEY)
        self.model = "compound-beta-mini"

        self.iter = 2
        self.sql_query = None
        self.evaluation_status = {
            "evaluation": "REJECT",
            "reasoning": "",
            "suggestions": "",
            "revised_query": None,
        }
    
    def build_sqlalchemy_url(self) -> str:
        return (
            f"postgresql+psycopg2://{os.environ.get('POSTGRES_USER')}:"
            f"{os.environ.get('POSTGRES_PASSWORD')}@"
            f"{os.environ.get('POSTGRES_HOST')}:"
            f"{os.environ.get('POSTGRES_PORT')}/"
            f"{os.environ.get('POSTGRES_DB')}"
        )

    def clean_query(self, query: str) -> str:
        # Remove any leading or trailing whitespace
        query = query.strip()

        # Remove any comments
        query = re.sub(r"--.*?$", "", query, flags=re.MULTILINE)
        query = re.sub(r"/\*.*?\*/", "", query, flags=re.DOTALL)

        # Remove <think> and </think>
        query = re.sub(r"<think>.*?</think>", "", query, flags=re.DOTALL)

        # Remove any extra spaces
        query = re.sub(r"\s+", " ", query)
        return query
    
    def filter_code(self, code: str) -> str:
        # Remove any leading or trailing whitespace
        code = code.strip()

        # Remove any comments
        code = re.sub(r"#.*?$", "", code, flags=re.MULTILINE)
        code = re.sub(r"\"\"\".*?\"\"\"", "", code, flags=re.DOTALL)
    
        # Remove ```python
        code = re.sub(r"```python", "", code)
        code = re.sub(r"```", "", code)

        return code

    def generate_sql_query(self, plain_query: str) -> str:
        prompt = f"""
            You are an expert SQL generator for PostgreSQL. Given a database schema and a user query, generate the appropriate SQL command.

            Schema:
            {self.schema}

            User Query:
            {plain_query}

            Instructions:
            - Understand the user's intent and generate only the SQL command.
            - Return executable SQL compatible with PostgreSQL.
            - Don't include thinking process or any help text.
            - Do not include comments, explanations, or any extra text.
            - Output only the SQL in a single line (no line breaks or formatting).
            - If the query is unrelated to the schema, return: "The query is outside my scope".
            - If the query is unclear, return: "I don't understand the query".
            - If the topic is not SQL-related, return: "I am not able to help you with that".
        """
        response = self.llm.chat.completions.create(
            model=self.model,
            temperature=0.1,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert query generator for Postgres Database. You provide with SQL queries based on the user query.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        content = response.choices[0].message.content
        query = self.clean_query(content)

        if not query.endswith(";"):
            query += ";"
        
        query = query.replace('%', '%%')
        self.sql_query = query

    def evaluate_sql_query(self, original_query: str) -> str:
        prompt = f"""
            You are an expert SQL evaluator. Given a database schema, a user query, and a generated SQL query, evaluate the SQL's correctness and relevance.

            Schema:
            {self.schema}

            User Query:
            {original_query}

            SQL Query:
            {self.sql_query}

            Instructions:
            - Evaluate the SQL against the schema and the user query.
            - Respond only in the following JSON format:

            {{
            "evaluation": "APPROVE" | "REVISE" | "REJECT",
            "reasoning": "Brief explanation of the evaluation decision.",
            "suggestions": "Suggestions to improve or correct the SQL, if any.",
            "revised_query": "Rewritten SQL query, or null if not applicable."
            }}
        """
        response = self.llm.chat.completions.create(
            model=self.model,
            temperature=0.1,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert SQL evaluator using ReAct framework. Given the user query and the generated SQL query, evaluate the SQL query based on the schema provided.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        response = response.choices[0].message.content
        match = re.search(r"{.*}", response, re.DOTALL)
        if match:
            try:
                self.evaluation_status = json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return {
            "evaluation": "REVISE",
            "reasoning": "JSON parse failed",
            "suggestions": "",
            "revised_query": None,
        }

    def validate_evaluation_status(self):
        if self.evaluation_status["evaluation"] != "APPROVE":
            for _ in range(self.iter):
                self.evaluate_sql_query(self.sql_query)
                if self.evaluation_status["evaluation"] == "APPROVE":
                    break
                revised_sql = self.evaluation_status["revised_query"]
                if not revised_sql:
                    break

                suggestions = self.evaluation_status["suggestions"]
                feedback_prompt = (
                    f"Refine the following SQL based on these suggestions: {suggestions}"
                    f"Original SQL: {revised_sql}"
                )

                self.generate_sql_query(feedback_prompt)

    def execute_sql_query(
        self,
    ) -> dict:
        engine = create_engine(self.connection_url)

        try:
            return pd.read_sql(self.sql_query, engine)
        except Exception as e:
            print(f"Error executing SQL query: {e}")
            raise e
    

    def interpret_code(self, e2b_code_interpreter: Sandbox, code: str):
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                exec = e2b_code_interpreter.run_code(code)

        if stderr_capture.getvalue():
            print("[Code Interpreter Warnings/Errors]", file=sys.stderr)
            print(stderr_capture.getvalue(), file=sys.stderr)

        if stdout_capture.getvalue():
            print("[Code Interpreter Output]", file=sys.stdout)
            print(stdout_capture.getvalue(), file=sys.stdout)

        if exec.error:
            print(f"[Code Interpreter ERROR] {exec.error}", file=sys.stderr)
            return None
        return exec.results

    def generate_appropriate_visualization(self, pd_df: pd.DataFrame, user_query: str):
        head_str = pd_df.head(5).to_string()
        columns_str = ', '.join(pd_df.columns)
        dtypes_str = pd_df.dtypes.to_string()
        describe_str = pd_df.describe(include='all').to_string()

        user_prompt = f"""
            You are a Python data scientist and data visualization expert. 
            You are provided with:
            1. The user's query
            2. The resultant dataframe from the SQL query
            3. Dataframe analytics

            Analyze both and generate **only** valid Python code based on the dataframe to produce an appropriate data visualization.

            # DataFrame Preview:
            USER QUERY:
            {user_query}
            
            HEAD:
            {head_str}

            COLUMNS:
            {columns_str}

            DTYPES:
            {dtypes_str}

            DESCRIBE:
            {describe_str}

            # Instructions:
            - Understand the structure and semantics of the data.
            - Assume there is no library imported before this code. Add all the library imports required for the code to run.
            - Assume you are provided the data directly and you need to convert it into dataframe.
            - Output clean, correct Python code to produce a relevant visualization using libraries like matplotlib or seaborn.
            - If required, update dataframe to appropriate visualization.
            - Ensure the code is executable and does not require any additional context.
            - Do not include explanations or markdown. Just output the raw code.
            - Use the provided CSV file path to read the data.
            - Use ReAct thinking: pause and revise your code before finalizing.
            - Make sure the code is compatible to dataframe always.
        """

        response = self.llm.chat.completions.create(
            model=self.model,
            temperature=0.1,
            messages=[
                {"role": "system", "content": "You are a Python data scientist and data visualization expert."},
                {"role": "user", "content": user_prompt},
            ],
        )
        response = response.choices[0].message.content

        print("response", response)
        code = self.filter_code(response)

        with Sandbox(api_key=settings.E2B_API_KEY) as code_interpreter:
            code_results = self.interpret_code(code_interpreter, code)
            if code_results:
                for result in code_results:
                    if hasattr(result, 'png') and result.png:
                        png_data = base64.b64decode(result.png)
                        image = Image.open(io.BytesIO(png_data))
                        return image
                    elif hasattr(result, 'figure'):
                        return result.figure
                    elif hasattr(result, 'show'):
                        return result
    
    def convert_image_to_base64(self, image):
        if image is None:
            return None
            
        buffer = io.BytesIO()
        
        image.save(buffer, format='PNG')
        buffer.seek(0)        
        img_str = base64.b64encode(buffer.read()).decode('utf-8')
        
        return f"data:image/png;base64,{img_str}"

    def run_pipeline(self, user_query: str) -> dict:
        # Step 1: Generate SQL query
        self.generate_sql_query(user_query)

        # Step 2: Check and evaluate query
        self.validate_evaluation_status()

        print("SQL Query:", self.sql_query)
        # Step 3: Execute query
        pandas_data_frame = self.execute_sql_query()

        # Step 4: Create appropriate visualization
        image = self.generate_appropriate_visualization(pandas_data_frame, user_query)

        # Step 5: Convert image to base64
        image_base64 = self.convert_image_to_base64(image)


        return pandas_data_frame, image_base64
