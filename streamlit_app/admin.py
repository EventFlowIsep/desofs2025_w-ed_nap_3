import streamlit as st
import requests
from firebase_admin import credentials, auth, initialize_app
import firebase_admin
import pandas as pd
import datetime

ROLE_CHOICES = {
    "Client": "client",
    "Admin": "admin",
    "Event Manager": "event_manager",
    "Moderator": "moderator",
    "Supplier": "supplier",
    "Partner": "partner"
}

# Initialize Firebase Admin
if not firebase_admin._apps:
    cred = credentials.Certificate("app/firebase_key.json")
    initialize_app(cred)

FIREBASE_API_KEY = "AIzaSyAHeLl9iaCku3LpBr0L-6Q3vMHQevgIw8c"
LOG_PATH = "admin_logs.csv"

st.set_page_config(page_title="Admin Login | EventFlow", page_icon="🔐")

if "admin_token" not in st.session_state:
    st.session_state.admin_token = None
if "admin_verified" not in st.session_state:
    st.session_state.admin_verified = False
if "admin_page" not in st.session_state:
    st.session_state.admin_page = "login"

DEFAULT_TIMEOUT = 10
# Firebase login (email/password)
def firebase_admin_login(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    res = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True}, timeout=DEFAULT_TIMEOUT)
    return res

# Verify if token is from admin
AUTHORIZED_ADMINS = ["adminuser@gmail.com"]
def verify_admin_token(token):
    try:
        decoded = auth.verify_id_token(token)
        is_admin = decoded.get("role") == "Admin"
        is_whitelisted = decoded.get("email", "").lower() in AUTHORIZED_ADMINS
        return is_admin and is_whitelisted
    except Exception:
        return False

# Assign role via Firebase Admin
def assign_user_role(email, role):
    try:
        user = auth.get_user_by_email(email)
        auth.set_custom_user_claims(user.uid, {"role": role})
        log_action(email, role)
        return f"✅ Role '{role}' assigned to {email}"
    except Exception as e:
        return f"❌ Error: {e}"

# Get user role
def get_user_role(email):
    try:
        user = auth.get_user_by_email(email)
        claims = user.custom_claims or {}
        return claims.get("role", "client")
    except Exception as e:
        return f"❌ Error: {e}"

# List all users with roles
def list_users_with_roles():
    users = auth.list_users().iterate_all()
    data = []
    for user in users:
        claims = user.custom_claims or {}
        data.append({
            "UID": user.id,  
            "Email": user.email, 
            "Role": claims.get("role", "client"),
            "Last Sign-In": user.user_metadata.last_sign_in_timestamp,   
        })
    return pd.DataFrame(data)

# Log changes
def log_action(email, role):
    timestamp = datetime.datetime.now().isoformat()
    entry = pd.DataFrame([[timestamp, email, role]], columns=["timestamp", "email", "assigned_role"])
    try:
        entry.to_csv(LOG_PATH, mode="a", header=not pd.io.common.file_exists(LOG_PATH), index=False)
    except Exception as e:
        st.warning(f"⚠️ Could not write to log: {e}")

# --- Login Page ---
if st.session_state.admin_page == "login":
    st.title("🔐 Admin Login - EventFlow")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        res = firebase_admin_login(email, password)
        if res.status_code == 200:
            token = res.json()["idToken"]
            if verify_admin_token(token):
                st.session_state.admin_token = token
                st.session_state.admin_verified = True
                st.session_state.admin_page = "panel"
                st.success("Admin verified! Redirecting...")
                st.rerun()
            else:
                st.error("Access denied. Not an admin user.")
        else:
            st.error("Invalid credentials or user not found.")

# --- Admin Panel ---
elif st.session_state.admin_page == "panel" and st.session_state.admin_verified:
    st.title("🛠️ Admin Panel - Manage Roles")

    with st.expander("🔍 Check User Role"):
        query_email = st.text_input("Enter user email to check role", key="check_role")
        if st.button("Check Role"):
            result = get_user_role(query_email)
            st.info(f"Current role: {result}")

    with st.expander("🧑‍🏫 Assign Role"):
        user_email = st.text_input("User Email", key="assign_email")
        role = st.selectbox("Select Role", [
            "Client", "Admin", "Event Manager", "Moderator", "Supplier", "Partner"])
        if st.button("Assign Role"):
            result = assign_user_role(user_email, role)
            st.success(result)
            st.info("⚠️ Ask the user to log in again to refresh their role.")

    with st.expander("📋 List All Users and Roles"):
        df = list_users_with_roles()
        st.dataframe(df)

    with st.expander("📜 Role Assignment Log"):
        try:
            logs = pd.read_csv(LOG_PATH)
            st.dataframe(logs)
        except Exception:
            st.info("No log file found yet.")

    st.markdown("---")
    if st.button("Log out"):
        st.session_state.admin_token = None
        st.session_state.admin_verified = False
        st.session_state.admin_page = "login"
        st.rerun()

# Fallback if token was cleared
elif not st.session_state.admin_verified:
    st.warning("Session expired. Please log in again.")
    st.session_state.admin_page = "login"
    st.rerun()