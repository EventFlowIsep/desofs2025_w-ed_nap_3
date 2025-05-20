import streamlit as st
import requests
import os
from pathlib import Path
from PIL import Image
import streamlit.components.v1 as components
import streamlit.web.cli as stcli
import sys
from modules import create_event, cancel_events, users_and_events, view_events
from dotenv import load_dotenv

st.set_page_config(
    page_title="EventFlow",
    page_icon="🎉",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Session state setup
if "trigger_google_redirect" not in st.session_state:
    st.session_state.trigger_google_redirect = False
if "token" not in st.session_state:
    st.session_state.token = None
if "user_role" not in st.session_state:
    st.session_state.user_role = ""
if "page" not in st.session_state:
    st.session_state.page = "auth"
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = ""

DEFAULT_TIMEOUT = 10

def get_user_role(token):
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"{API_URL}/verify-token", headers=headers, timeout=DEFAULT_TIMEOUT)
    if res.status_code == 200:
        return res.json().get("role", "client")
    return "client"

# Auto-login from Google redirect
token_param = st.query_params.get("token")
if token_param and not st.session_state.token:
    st.session_state.token = token_param
    st.session_state.user_role = get_user_role(token_param)
    st.session_state.page = "main"
    st.query_params.clear()
    st.rerun()

def firebase_register(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    return requests.post(url, json={"email": email, "password": password, "returnSecureToken": True}, timeout=DEFAULT_TIMEOUT)

def firebase_login(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    return requests.post(url, json={"email": email, "password": password, "returnSecureToken": True}, timeout=DEFAULT_TIMEOUT)

# Redirect after login
if st.session_state.page == "main":
    st.sidebar.title("📂 Menu")
    if st.session_state.user_role:
        st.sidebar.markdown(f"🧑 Logged in as: **{st.session_state.user_role.capitalize()}**")
    
    st.write("DEBUG – role:", st.session_state.user_role)

    if "token" in st.session_state and st.session_state.token:
    # 📋 Menu based on role
        menu_options = ["View Events"]  # all have access

        if st.session_state.user_role in ["admin", "event_manager"]:
            menu_options.append("Create Event")
            menu_options.append("Cancel Event")

        if st.session_state.user_role == "admin":
            menu_options.append("Manage Users")

        selected = st.sidebar.selectbox("Choose an action", menu_options)

    # 🔁 Routing
        if selected == "View Events":
            view_events.show()

        elif selected == "Create Event":
            if st.session_state.user_role in ["admin", "event_manager"]:
                create_event.show()
            else:
                st.warning("❌ You do not have permission to create events.")

        elif selected == "Cancel Event":
            if st.session_state.user_role in ["admin", "event_manager"]:
                cancel_event.show()
            else:
                st.warning("❌ You do not have permission to cancel events.")

        elif selected == "Manage Users":
            if st.session_state.user_role == "admin":
                users_and_events.show()
            else:
                st.warning("❌ You do not have permission to manage users.")

    else:
        st.sidebar.warning("🔐 Please log in to access features.")
        st.write("Welcome to EventFlow. Log in to get started.")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Log out"):
        st.session_state.token = None
        st.session_state.user_role = None
        st.session_state.page = "auth"
        st.query_params.clear()
        st.rerun()

elif st.session_state.page == "auth":
    st.title("Login 🔐")
    st.markdown("<h1 style='text-align: center;'>👋 Welcome to EventFlow 👋</h1>", unsafe_allow_html=True)

    st.sidebar.title("🔐 Login")
    option = st.sidebar.selectbox("Login method", ["Email", "Google"], index=0)

    if option == "Email":
        st.sidebar.text_input("Email", key="log_email")
        st.sidebar.text_input("Password", type="password", key="log_pass")
        if st.sidebar.button("Login"):
            res = firebase_login(st.session_state.log_email, st.session_state.log_pass)
            if res.status_code == 200:
                token = res.json()["idToken"]
                st.session_state.token = token
                st.session_state.user_role = get_user_role(token)
                st.success("Login successful!")
                st.session_state.page = "main"
                st.rerun()
            else:
                st.sidebar.error("Login failed: " + res.json().get("error", {}).get("message", "Unknown error"))

    elif option == "Google":
        if st.sidebar.button("🔓 Sign in with Google"):
            st.session_state.trigger_google_redirect = True
            st.rerun()

        if st.session_state.trigger_google_redirect:
            st.markdown(
                """
                    <meta http-equiv="refresh" content="0; url='http://localhost:8000/auth/google_login.html'" />
                """,
                unsafe_allow_html=True
            )

            st.session_state.trigger_google_redirect = False

        st.sidebar.info("You will be redirected and logged in automatically.")

    st.sidebar.markdown("---")
    if st.sidebar.button("Register"):
        st.session_state.page = "register"
        st.rerun()

elif st.session_state.page == "register":
    st.title("Register 📝")
    st.title("📝 Create a New Account")
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_pass")
    if st.button("Register"):
        res = firebase_register(email, password)
        if res.status_code == 200:
            st.success("✅ Registered! You can now log in.")
            st.session_state.page = "auth"
            st.session_state.auth_mode = "Email"
            st.rerun()
        else:
            st.error("Registration failed: " + res.json().get("error", {}).get("message", "Unknown error"))

    st.markdown("---")
    st.markdown("Already have an account?")
    if st.button("Login"):
        st.session_state.page = "auth"
        st.rerun()
