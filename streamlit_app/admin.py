import streamlit as st
import requests
from firebase_admin import credentials, auth, initialize_app
import firebase_admin
import pandas as pd
import datetime
import sys
import os
from dotenv import load_dotenv
from google.cloud import firestore
from datetime import datetime, timedelta
import json
import sqlite3
from streamlit_autorefresh import st_autorefresh
from datetime import timezone
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.logging_db import SQLiteLogger
import re

SQLiteLogger()

RATE_LIMIT = 5

ROLE_CHOICES = {
    "Client": "client",
    "Admin": "admin",
    "Event Manager": "event_manager",
    "Moderator": "moderator",
    "Supplier": "supplier",
    "Partner": "partner"
}
load_dotenv()
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

if not firebase_admin._apps:
    cred = credentials.Certificate("app/firebase_key.json")
    initialize_app(cred)

db = firestore.Client.from_service_account_json("app/firebase_key.json")

LOG_PATH = "admin_logs.csv"

st.set_page_config(page_title="Admin Login | EventFlow", page_icon="🔐")

if "admin_token" not in st.session_state:
    st.session_state.admin_token = None
if "admin_verified" not in st.session_state:
    st.session_state.admin_verified = False
if "admin_page" not in st.session_state:
    st.session_state.admin_page = "login"

DEFAULT_TIMEOUT = 30
# Firebase login (email/password)
def firebase_admin_login(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    res = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True}, timeout=DEFAULT_TIMEOUT)
    return res

# Verify if token is from admin
AUTHORIZED_ADMINS = ["adminuser@gmail.com","sakiw92923@nomrista.com"]
def verify_admin_token(token):
    try:
        decoded = auth.verify_id_token(token)
        is_admin = decoded.get("role") == "Admin"
        is_whitelisted = decoded.get("email", "").lower() in AUTHORIZED_ADMINS
        return is_admin and is_whitelisted
    except Exception:
        return False

def sanitize_input(text):
    if not isinstance(text, str):
        return text
    text = re.sub(r"(?i)<script.*?>.*?</script>", "", text)
    text = re.sub(r"(?i)on\w+\s*=", "", text)
    text = re.sub(r"[{}$]", "", text)
    return text


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
@st.cache_data(ttl=60)
def get_user_role(email):
    try:
        user = auth.get_user_by_email(email)
        claims = user.custom_claims or {}
        return claims.get("role", "client")
    except Exception as e:
        return f"❌ Error: {e}"

# List all users with roles
@st.cache_data(ttl=60)
def list_users_with_roles():
    users = auth.list_users().iterate_all()
    data = []
    for user in users:
        claims = user.custom_claims or {}
        data.append({
            "UID": user.uid,  
            "Email": user.email, 
            "Role": claims.get("role", "client"),
            "Last Sign-In": user.user_metadata.last_sign_in_timestamp,   
        })
    return pd.DataFrame(data)

# Create a category for events
def create_category(name):
    category_ref = db.collection('categories').document(name)
    category_ref.set({
        'name': name,
        'created_at': datetime.datetime.now()
    })
    return f"✅ Category '{name}' created successfully."

# List all categories and the number of events in each category
def list_categories():
    categories_ref = db.collection('categories')
    categories = categories_ref.stream()
    all_events = list(db.collection('events').stream())  # Uma só chamada para eventos

    category_counts = {}
    for event in all_events:
        data = event.to_dict()
        cat = data.get("category")
        if cat:
            category_counts[cat] = category_counts.get(cat, 0) + 1

    category_data = []
    for category in categories:
        name = category.id
        count = category_counts.get(name, 0)
        category_data.append({
            "Category": name,
            "Number of Events": count
        })

    return pd.DataFrame(category_data)

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
        if res.status_code != 200:
            st.error("Invalid credentials or user not found.")
            st.stop()

        token = res.json()["idToken"]
        headers = {"Authorization": f"Bearer {token}"}
        verify_res = requests.get("http://localhost:8000/verify-token", headers=headers)

        if verify_res.status_code != 200:
            st.error("❌ Failed to verify token. Possibly expired or invalid.")
            st.stop()

        try:
            data = verify_res.json()
            ip = data.get("ip", "unknown")
            st.session_state.admin_ip = ip
        except Exception:
            st.error("❌ Failed to parse JSON from /verify-token")
            st.stop()

        key = f"rate_limit:{ip}:admin_login"
        attempts = st.session_state.get(key, 0)
        if attempts >= RATE_LIMIT:
            st.error("🚫 Too many login attempts. Please try again later.")
            st.stop()
        else:
            st.session_state[key] = attempts + 1

        if verify_admin_token(token):
            st.session_state.admin_token = token
            st.session_state.admin_verified = True
            st.session_state.admin_page = "panel"
            st.success("✅ Admin verified! Redirecting...")
            st.rerun()
        else:
            st.error("⛔ Access denied. Not an authorized admin.")
            st.stop()


# --- Admin Panel ---
elif st.session_state.admin_page == "panel" and st.session_state.admin_verified:
    st.title("🛠️ Admin Panel - Manage Roles")

    ip = st.session_state.get("admin_ip", "unknown")
    key = f"rate_limit:{ip}:admin_panel"
    requests_made = st.session_state.get(key, 0)
    if requests_made >= RATE_LIMIT:
        st.error("Too many requests. Try again later.")
    else:
        st.session_state[key] = requests_made + 1

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

        with st.expander("🔍 Create Category"):
            category_name = st.text_input("Enter category name", key="category_name")
            if st.button("Create Category"):
                if category_name:
                    result = sanitize_input(category_name)
                    st.success(result)
                else:
                    st.warning("❌ Category name is required.")

        with st.expander("📋 View Categories and Event Counts"):
            df = list_categories()
            st.dataframe(df)

        with st.expander("View Backend Logs"):
            st.subheader("📄 Backend Logs (last 100)")

            if st.button("Fetch Logs"):
                if st.session_state.admin_token:
                    headers = {"Authorization": f"Bearer {st.session_state.admin_token}"}
                    try:
                        res = requests.get("http://localhost:8000/logs", headers=headers, timeout=DEFAULT_TIMEOUT)
                        if res.status_code == 200:
                            logs_data = res.json().get("logs", [])
                            if logs_data:
                                df_logs = pd.DataFrame(logs_data)
                                st.dataframe(df_logs)
                            else:
                                st.info("No logs available.")
                        else:
                            st.error(f"Failed to fetch logs: {res.status_code}")
                    except Exception as e:
                        st.error(f"Error fetching logs: {e}")
                        st.write("Error details:", e)
                else:
                    st.error("Admin token missing. Please log in again.")

        with st.expander("🚀 Real-Time Log Monitoring Dashboard"):
            st_autorefresh(interval=60 * 1000, key="log_refresh")

            st.subheader("📄 Last 100 Logs")
            try:
                DB_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "eventflow_logs.db")
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT timestamp, user_email, method, path, status_code, message
                    FROM logs
                    ORDER BY timestamp DESC
                    LIMIT 100
                ''')
                logs = cursor.fetchall()
                conn.close()

                if logs:
                    df_logs = pd.DataFrame(logs, columns=[
                        "Timestamp", "User Email", "Method", "Path", "Status Code", "Message"
                    ])
                    st.dataframe(df_logs, use_container_width=True)
                else:
                    st.info("No logs available.")

            except Exception as e:
                st.error(f"❌ Error reading logs: {e}")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        ten_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=10)
        cursor.execute('''
            SELECT timestamp, user_email, ip, pattern, path
            FROM alerts
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        ''', (ten_minutes_ago.isoformat(),))
        alerts = cursor.fetchall()
        conn.close()

        if alerts:
            for alert in alerts:
                timestamp, email, ip, pattern, path = alert
                st.toast(
                    f"⚠️ [{pattern}] from {email} at {ip} on {path}",
                    icon="🚨"
                )
        else:
            st.success("✅ No suspicious activity detected recently.")

    except Exception as e:
        st.error(f"❌ Error reading alerts: {e}")
        with st.expander("⚠️ Suspicious Activity"):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, user_email, method, path, status_code, message 
                FROM logs 
                WHERE message LIKE '%<script>%' OR path LIKE '%union%' OR path LIKE '%/../%'
                ORDER BY timestamp DESC LIMIT 100
            """)    
            rows = cursor.fetchall()
            conn.close()

            if rows:
                st.error(f"{len(rows)} suspicious log(s) detected.")
                df_suspicious = pd.DataFrame(rows, columns=["Time", "User", "Method", "Path", "Status", "Message"])
                st.dataframe(df_suspicious)
            else:
                st.success("✅ No suspicious activity detected.")
                
        with st.expander("🚨 Suspicious Activity Alerts"):
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT timestamp, user_email, ip, pattern, path
                    FROM alerts
                    ORDER BY timestamp DESC
                    LIMIT 100
                ''')
                alerts = cursor.fetchall()
                conn.close()

                if alerts:
                    df_alerts = pd.DataFrame(alerts, columns=["Timestamp", "User Email", "IP", "Pattern Detected", "Path"])
                    st.warning("🚨 Suspicious patterns detected in the last 100 logs:")
                    st.dataframe(df_alerts, use_container_width=True)
                else:
                    st.success("✅ No suspicious activity detected.")
            except Exception as e:
                st.error(f"❌ Error reading alerts: {e}")

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