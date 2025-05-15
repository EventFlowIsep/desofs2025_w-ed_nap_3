import streamlit as st
import requests
import os
from pathlib import Path
from PIL import Image

FIREBASE_API_KEY = "AIzaSyAHeLl9iaCku3LpBr0L-6Q3vMHQevgIw8c"
API_URL = os.getenv("API_URL", "http://localhost:8000")
image_path = Path(__file__).resolve().parent.parent / "images" / "EventFlow.png"

# Session state
if "token" not in st.session_state:
    st.session_state.token = None
if "page" not in st.session_state:
    st.session_state.page = "auth"
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = ""

# Auto-login from Google redirect
token_param = st.query_params.get("token")
if token_param and not st.session_state.token:
    st.session_state.token = token_param
    st.session_state.page = "main"
    st.rerun()

# Firebase functions
def firebase_register(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    return requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})

def firebase_login(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    return requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})

# Main content
if st.session_state.page == "main":
    st.title("🎉 EventFlow")
    st.subheader("Empowering Events, Enabling Connections")

    try:
        image = Image.open(image_path)
        st.image(image, use_container_width=True, caption="Your event journey starts here.")
    except FileNotFoundError:
        st.error("Banner image not found.")

    st.markdown("---")
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    try:
        res = requests.get(f"{API_URL}/events", headers=headers)
        if res.status_code == 200:
            for ev in res.json():
                st.markdown(f"📅 **{ev['name']}** — {ev['date']} (User: {ev['user']})")
        else:
            st.error("Failed to load events.")
    except Exception as e:
        st.error(f"Backend error: {e}")

    if st.button("Log out"):
        st.session_state.token = None
        st.session_state.page = "auth"
        st.rerun()

# Auth page
elif st.session_state.page == "auth":
    st.markdown("<h1 style='text-align: center;'>👋 Welcome to EventFlow 👋</h1>", unsafe_allow_html=True)

    # Sidebar login layout
    st.sidebar.title("🔐 Login")
    option = st.sidebar.selectbox(
        "", ["Login method", "Email", "Google"], index=0
    )

    if option == "Email":
        st.sidebar.text_input("Email", key="log_email")
        st.sidebar.text_input("Password", type="password", key="log_pass")
        if st.sidebar.button("Login"):
            res = firebase_login(st.session_state.log_email, st.session_state.log_pass)
            if res.status_code == 200:
                st.session_state.token = res.json()["idToken"]
                st.success("Login successful!")
                st.session_state.page = "main"
                st.rerun()
            else:
                st.sidebar.error("Login failed: " + res.json().get("error", {}).get("message", "Unknown error"))

    elif option == "Google":
        st.sidebar.markdown("[🔓 Sign in with Google](http://localhost:8000/auth/google_login.html)", unsafe_allow_html=True)
        st.sidebar.info("You will be redirected and logged in automatically.")

    st.sidebar.markdown("---")
    if st.sidebar.button("Register"):
        st.session_state.page = "register"
        st.rerun()

# Registration page
elif st.session_state.page == "register":
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
