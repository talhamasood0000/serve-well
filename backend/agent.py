import os
import json
import re
import pandas as pd
import ast
import base64
from io import BytesIO, StringIO
import contextlib
import warnings
import io
import sys
import textwrap
from typing import Optional, List, Dict, Any, Tuple
from together import Together
from e2b_code_interpreter import Sandbox

AGENTS = """
SQL Generator
SQL Evaluator
Writer Agent
Visualization Agent

"""

# Constants
MODEL_OPTIONS = {
    "Meta-Llama 3.1 405B": "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
    "DeepSeek V3": "deepseek-ai/DeepSeek-V3",
    "Qwen 2.5 7B": "Qwen/Qwen2.5-7B-Instruct-Turbo",
    "Meta-Llama 3.3 70B": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
}

# Schema description for the review analysis dataset
SCHEMA_DESCRIPTION = """
This dataset contains fast food order details with customer review analysis:

- order: Foreign Key to Order Model.
- sentiment_label: Sentiment classification of the review (positive, negative).
- emotions: Detected emotions in the review (e.g., frustration, joy), stored as a list of strings.
- extracted_keywords: Key points extracted from the review (e.g., "long wait time"), stored as a list of strings.
- products: Products mentioned in the review, stored as a list of strings.
- created_at: Timestamp of when the review was created.
- updated_at: Timestamp of when the review was last updated.
"""

# Visualization types mapping
VIZ_TYPES = {
    "bar_chart": "BarChart",
    "line_chart": "LineChart",
    "pie_chart": "PieChart",
    "donut_chart": "PieChart with innerRadius",
    "area_chart": "AreaChart",
    "scatter_plot": "ScatterChart",
    "bubble_chart": "ScatterChart with variable point sizes",
    "radar_chart": "RadarChart",
    "polar_chart": "PolarChart",
    "heat_map": "Heatmap",
    "tree_map": "Treemap",
    "word_cloud": "WordCloud",
    "sankey_diagram": "Sankey",
    "network_graph": "NetworkGraph",
    "funnel_chart": "FunnelChart",
    "gauge_chart": "GaugeChart",
    "calendar_heatmap": "CalendarHeatmap",
    "boxplot": "BoxPlot",
    "violin_plot": "ViolinPlot",
    "histogram": "Histogram",
    "stacked_bar": "StackedBarChart",
    "grouped_bar": "GroupedBarChart",
    "table": "Table",
    "data_grid": "DataGrid",
    "composite_chart": "CompositeChart",
}


def code_interpret(e2b_code_interpreter: Sandbox, code: str) -> Optional[List[Any]]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exec = e2b_code_interpreter.run_code(code)
        if exec.error:
            print(f"[Code Interpreter ERROR] {exec.error}", file=sys.stderr)
            return None
        return exec.results


def match_code_blocks(text: str, language: str = "sql") -> str:
    m = re.search(rf"```{language}\s*([\s\S]*?)```", text, re.DOTALL)
    return m.group(1).strip() if m else ""


class SQLGeneratorAgent:
    def __init__(self, llm_client: Together, dataset_schema: str, model_name: str):
        self.llm = llm_client
        self.schema = dataset_schema
        self.model = model_name

    def generate_sql(self, query: str) -> str:
        prompt = f"""
            Role: Expert SQL generator for customer feedback.
            Schema:
            {self.schema}
            User Query:
            {query}
            Instructions:
            - Understand the semantic nature of the user query and based on the requirements, return only executable SQL without comments (`--`).
        """
        resp = self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert SQL developer."},
                {"role": "user", "content": prompt},
            ],
        )
        code_sql = match_code_blocks(resp.choices[0].message.content, "sql")
        cleaned_sql = re.sub(r"--.*$", "", code_sql).strip()
        cleaned_sql = re.sub(r"^\s*", "", cleaned_sql)
        cleaned_sql = re.sub(r"\s*$", "", cleaned_sql)
        if not cleaned_sql.endswith(";"):
            cleaned_sql += ";"
        return cleaned_sql


class QueryEvaluatorAgent:
    def __init__(self, llm_client: Together, dataset_schema: str, model_name: str):
        self.llm = llm_client
        self.schema = dataset_schema
        self.model = model_name

    def evaluate_query(self, original_query: str, sql_query: str) -> Dict[str, Any]:
        prompt = f"""
        Role: SQL evaluator using ReAct.
        Schema:
        {self.schema}
        Original Query:
        {original_query}
        SQL Query:
        {sql_query}
        Return JSON: {{"evaluation","reasoning","suggestions","revised_query"}}
        """
        resp = self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert SQL evaluator."},
                {"role": "user", "content": prompt},
            ],
        )
        text = resp.choices[0].message.content
        m = re.search(r"({.*})", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        return {
            "evaluation": "REVISE",
            "reasoning": "JSON parse failed",
            "suggestions": "",
            "revised_query": None,
        }


class WriterAgent:
    def __init__(
        self, sandbox: Sandbox, path: str, llm_client: Together, model_name: str
    ):
        self.sandbox = sandbox
        self.path = path
        self.llm = llm_client
        self.model = model_name

    def execute_query(self, sql: str) -> Dict[str, Any]:
        # Prepare DataFrame loader and parser
        import psycopg2

        connection = psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password="password",
            port=5432
        )
        query = sql
        df = pd.read_sql(query, connection)
        return {"success": True, "data": df}


class VisualizationAgent:
    def __init__(
        self, llm_client: Together, viz_types: Dict[str, str], model_name: str
    ):
        self.llm = llm_client
        self.viz_types = viz_types
        self.model = model_name

    def recommend_visualization(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """
        Recommend the best visualization type for df based on the query.
        Returns the DataFrame and chosen viz_type.
        """
        col_types = {col: str(dtype) for col, dtype in df.dtypes.items()}

        prompt = f"""
            You are a visualization expert. Given a DataFrame with column types {col_types} and the user query: {query},
            select the most appropriate visualization type from {list(self.viz_types.keys())}.
            Return only the key of the chosen visualization."""
        resp = self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert data visualization advisor.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        viz_type = resp.choices[0].message.content.strip().strip('"')

        if viz_type not in self.viz_types:
            viz_type = "table"

        return {"df": df, "viz_type": viz_type}


class DataVisualizationOrchestrator:
    def __init__(self, sandbox: Sandbox, path: str, api_key: str, model_name: str):
        self.sandbox = sandbox
        self.path = path
        self.llm = Together(api_key=api_key)
        self.model = model_name
        self.max_iterations = 1
        self.sql_gen = SQLGeneratorAgent(self.llm, SCHEMA_DESCRIPTION, model_name)
        self.eval = QueryEvaluatorAgent(self.llm, SCHEMA_DESCRIPTION, model_name)
        self.writer = WriterAgent(self.sandbox, path, self.llm, model_name)
        self.viz = VisualizationAgent(self.llm, VIZ_TYPES, model_name)

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Iteratively generate and evaluate SQL until PASS or max_iterations reached.
        Flow: SQLGenerator -> QueryEvaluator -> (refine via SQLGenerator if REVISE) -> ... -> WriterAgent
        """
        current_sql = self.sql_gen.generate_sql(query)
        evaluation = None

        for iteration in range(1, self.max_iterations + 1):
            evaluation = self.eval.evaluate_query(query, current_sql)
            if evaluation.get("evaluation") == "PASS":
                # SQL is approved
                break
            revised_sql = evaluation.get("revised_query")
            if not revised_sql:
                break
            feedback_prompt = (
                f"Refine the following SQL based on these suggestions: {evaluation.get('suggestions')}"
                f"Original SQL: {revised_sql}"
            )
            current_sql = self.sql_gen.generate_sql(feedback_prompt)
        else:
            pass

        final_sql = current_sql
        print(f"Final SQL: {final_sql}")
        qr = self.writer.execute_query(final_sql)
        if not qr.get("success"):
            return {"success": False, "error": qr.get("error")}
        viz_rec = self.viz.recommend_visualization(qr.get("data", []), query)
        return {"data": qr.get("data"), "visualization": viz_rec}


def upload_dataset(sandbox: Sandbox, uploaded_file) -> str:
    path = f"./{uploaded_file.name}"
    sandbox.files.write(path, uploaded_file)
    return path


import streamlit as st


def main():
    """Main function to run the data visualization system."""
    import streamlit as st

    st.title("📊 AI Data Visualization Agent")
    st.write("Upload your dataset and ask questions about it!")

    # Initialize session state variables
    if "together_api_key" not in st.session_state:
        st.session_state.together_api_key = ""
    if "e2b_api_key" not in st.session_state:
        st.session_state.e2b_api_key = ""
    if "model_name" not in st.session_state:
        st.session_state.model_name = ""

    with st.sidebar:
        st.header("API Keys and Model Configuration")
        st.session_state.together_api_key = st.sidebar.text_input(
            "Together AI API Key", type="password"
        )
        st.sidebar.info(
            "💡 Everyone gets a free $1 credit by Together AI - AI Acceleration Cloud platform"
        )
        st.sidebar.markdown("[Get Together AI API Key](https://api.together.ai/signin)")

        st.session_state.e2b_api_key = st.sidebar.text_input(
            "Enter E2B API Key", type="password"
        )
        st.sidebar.markdown(
            "[Get E2B API Key](https://e2b.dev/docs/legacy/getting-started/api-key)"
        )

        # Add model selection dropdown
        model_options = list(MODEL_OPTIONS.keys())
        selected_model = st.selectbox(
            "Select Model", options=model_options, index=0  # Default to first option
        )
        st.session_state.model_name = MODEL_OPTIONS[selected_model]

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file is not None:
        # Display dataset with toggle
        df = pd.read_csv(uploaded_file)
        st.write("Dataset:")
        show_full = st.checkbox("Show full dataset")
        if show_full:
            st.dataframe(df)
        else:
            st.write("Preview (first 5 rows):")
            st.dataframe(df.head())

        # Query input
        query = st.text_area(
            "What would you like to know about your data?",
            "What are the top pain points mentioned by customers with negative sentiment?",
        )
        if st.button("Analyze"):
            if (
                not st.session_state.together_api_key
                or not st.session_state.e2b_api_key
            ):
                st.session_state.together_api_key = (
                    "6db1f14e1dc613500a2f33aa429d5dd0836a4d45b4cfb992fce58740f55ee46a"
                )
                st.session_state.e2b_api_key = (
                    "e2b_ca3211d2c32647f6abc4f20ae408efc92645b740"
                )
                with Sandbox(api_key=st.session_state.e2b_api_key) as code_interpreter:
                    # Upload the dataset
                    dataset_path = upload_dataset(code_interpreter, uploaded_file)

                    # Create orchestrator
                    MODEL_NAME = st.session_state.model_name
                    orchestrator = DataVisualizationOrchestrator(
                        code_interpreter,
                        dataset_path,
                        st.session_state.together_api_key,
                        MODEL_NAME,
                    )

                    # Process query
                    with st.spinner("Processing your query..."):
                        result = orchestrator.process_query(query)

                    if result["success"]:
                        # Display data
                        st.subheader("Results")
                        st.dataframe(pd.DataFrame(result["data"]))

                        # Display visualization recommendation
                        st.subheader("Recommended Visualization")
                        st.json(result["visualization"])

                        # Display the full JSON response
                        st.subheader("JSON Response (for API/Frontend)")
                        json_result = {
                            "data": result["data"],
                            "visualization": result["visualization"],
                            # "csv": result["csv"]
                        }
                        st.json(json_result)
                    else:
                        st.error(f"Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
