import streamlit as st
import requests
from PIL import Image
from pathlib import Path

API_URL = "http://localhost:8000"

# Path to the EventFlow image
image_path = Path(__file__).resolve().parent.parent / "images" / "EventFlow.png"

# Persistent session state
if "token" not in st.session_state:
    st.session_state.token = None
if "page" not in st.session_state:
    st.session_state.page = "auth"  # or "main"
if "tab" not in st.session_state:
    st.session_state.tab = "Login"

# --- Page routing logic ---
if st.session_state.page == "main":
    st.title("🎉 EventFlow")
    st.subheader("Empowering Events, Enabling Connections")

    # Display image from images folder
    try:
        image = Image.open(image_path)
        st.image(image, use_container_width=True, caption="Your event journey starts here.")
    except FileNotFoundError:
        st.error("Image not found. Please ensure 'EventFlow.png' exists in the images/ folder.")

    st.markdown("---")
    st.success("Welcome! You're logged in.")
    if st.button("Log out"):
        st.session_state.token = None
        st.session_state.page = "auth"
        st.rerun()

else:
    # Sidebar navigation between Login and Register
    st.sidebar.title("EventFlow")
    st.sidebar.subheader("Access")
    st.session_state.tab = st.sidebar.radio("Choose:", ["Login", "Register"], index=0 if st.session_state.tab == "Login" else 1)

    if st.session_state.tab == "Register":
        st.subheader("Create Account")
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_pass")
        if st.button("Register"):
            try:
                res = requests.post(f"{API_URL}/register", json={"email": email, "password": password})
                if res.status_code == 200:
                    st.success("✅ Registered! You can now log in.")
                    st.session_state.tab = "Login"
                    st.rerun()
                else:
                    st.error(res.json().get("detail", "Registration failed."))
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {e}")

    elif st.session_state.tab == "Login":
        st.subheader("Login")
        email = st.text_input("Email", key="log_email")
        password = st.text_input("Password", type="password", key="log_pass")
        if st.button("Login"):
            try:
                res = requests.post(f"{API_URL}/login", json={"email": email, "password": password})
                if res.status_code == 200:
                    st.session_state.token = res.json()["access_token"]
                    st.success("Login successful!")
                    st.session_state.page = "main"
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {e}")
