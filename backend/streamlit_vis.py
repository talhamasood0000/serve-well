import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime, timedelta

def login(username, password):
    """Authenticate user and get JWT tokens"""
    try:
        response = requests.post(
            "http://localhost:8000/api/token/",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None

def refresh_token(refresh_token):
    """Refresh access token using refresh token"""
    try:
        response = requests.post(
            "http://localhost:8000/api/token/refresh/",
            json={"refresh": refresh_token}
        )
        response.raise_for_status()
        return response.json().get("access")
    except:
        return None

def main():
    st.set_page_config(page_title="SQL Chat Assistant", layout="centered")
    
    # Initialize session state variables
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    if "refresh_token" not in st.session_state:
        st.session_state.refresh_token = None
    if "token_expiry" not in st.session_state:
        st.session_state.token_expiry = None
    if "history" not in st.session_state:
        st.session_state.history = []

    # Login page
    if not st.session_state.authenticated:
        st.title("🔐 Login")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                auth_response = login(username, password)
                if auth_response:
                    st.session_state.access_token = auth_response.get("access")
                    st.session_state.refresh_token = auth_response.get("refresh")
                    # Set token expiry time (typically 5 minutes for access tokens)
                    st.session_state.token_expiry = datetime.now() + timedelta(minutes=5)
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    
    # Main app after authentication
    else:
        st.title("📊 SQL Agent Chat")
        
        # Add logout button in sidebar
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.access_token = None
            st.session_state.refresh_token = None
            st.session_state.token_expiry = None
            st.rerun()
            
        # Check if token needs refresh
        if st.session_state.token_expiry and datetime.now() > st.session_state.token_expiry:
            new_access_token = refresh_token(st.session_state.refresh_token)
            if new_access_token:
                st.session_state.access_token = new_access_token
                st.session_state.token_expiry = datetime.now() + timedelta(minutes=5)
            else:
                st.warning("Your session has expired. Please login again.")
                st.session_state.authenticated = False
                time.sleep(2)
                st.rerun()

        # Chat interface
        if prompt := st.chat_input("Ask a question about your data:"):
            st.session_state.history.append({"role": "user", "content": prompt})

            with st.spinner("Processing..."):
                try:
                    # Make authenticated API request
                    headers = {
                        "Authorization": f"Bearer {st.session_state.access_token}",
                        "Content-Type": "application/json"
                    }
                    
                    response = requests.post(
                        "http://localhost:8000/api/generate_sql/",
                        json={"query": prompt},
                        headers=headers
                    )
                    
                    if response.status_code == 401:
                        # Try token refresh if unauthorized
                        new_access_token = refresh_token(st.session_state.refresh_token)
                        if new_access_token:
                            st.session_state.access_token = new_access_token
                            st.session_state.token_expiry = datetime.now() + timedelta(minutes=5)
                            
                            # Retry with new token
                            headers["Authorization"] = f"Bearer {new_access_token}"
                            response = requests.post(
                                "http://localhost:8000/generate_sql/",
                                json={"query": prompt},
                                headers=headers
                            )
                        else:
                            st.warning("Your session has expired. Please login again.")
                            st.session_state.authenticated = False
                            time.sleep(2)
                            st.rerun()
                    
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

        # Display chat history
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
