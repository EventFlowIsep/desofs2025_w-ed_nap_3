import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

def show():
    st.title("➕ Create Event")

    if "token" not in st.session_state or not st.session_state.token:
        st.warning("🔒 You must be logged in to access this page.")
        return

    headers = {"Authorization": f"Bearer {st.session_state.token}"}

    # Verificar role do utilizador
    if "user_role" not in st.session_state or not st.session_state.user_role:
        try:
            res = requests.get(f"{API_URL}/verify-token", headers=headers)
            if res.status_code == 200:
                st.session_state.user_role = res.json().get("role", "client")
        except:
            st.session_state.user_role = "client"

    if st.session_state.user_role not in ["admin", "event_manager"]:
        st.warning("❌ You do not have permission to create events.")
        return

    with st.form("create_event_form"):
        title = st.text_input("Title")
        date = st.date_input("Date")
        description = st.text_area("Description")
        image_url = st.text_input("Image URL (optional)")
        submitted = st.form_submit_button("Create")

        if submitted:
            payload = {
                "title": title,
                "date": str(date),
                "description": description,
                "image_url": image_url
            }

            try:
                res = requests.post(f"{API_URL}/events/create", json=payload, headers=headers)
                if res.status_code == 200:
                    st.success("✅ Event created successfully.")
                    st.experimental_rerun()
                else:
                    st.error("❌ Failed to create event.")
            except Exception as e:
                st.error(f"Backend error: {e}")
