import streamlit as st
import pandas as pd
import requests

def main():
    st.set_page_config(page_title="SQL Chat Assistant", layout="centered")
    st.title("📊 SQL Agent Chat")

    if "history" not in st.session_state:
        st.session_state.history = []

    if prompt := st.chat_input("Ask a question about your data:"):
        st.session_state.history.append({"role": "user", "content": prompt})

        with st.spinner("Processing..."):
            try:

                response = requests.post(
                    "http://localhost:8000/api/generate_sql/",
                    json={"query": prompt}
                )
                response.raise_for_status()
                data = response.json()

                old_data, image = data.get("data"), data.get("visualization")
                df = pd.DataFrame(old_data)
                sql_query = data.get("sql_query")

                assistant_response = f"**SQL Query:**\n```sql\n{sql_query}\n```"
                st.session_state.history.append({
                    "role": "assistant",
                    "content": assistant_response,
                    "df": df,
                    "image": image
                })
            except Exception as e:
                st.session_state.history.append({
                    "role": "assistant",
                    "content": f"Error: {str(e)}"
                })
                st.error(f"Error: {str(e)}")

    for msg in st.session_state.history:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        elif msg["role"] == "assistant":
            with st.chat_message("assistant"):
                st.markdown(msg["content"])
                if "df" in msg:
                    st.dataframe(msg["df"])
                if "image" in msg and msg["image"]:
                    st.image(msg["image"])


if __name__ == "__main__":
    main()