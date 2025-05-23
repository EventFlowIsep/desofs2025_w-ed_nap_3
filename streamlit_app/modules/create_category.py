import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Create Category", page_icon="🏷")
st.title("🏷 Create Event Category")

if "token" not in st.session_state or not st.session_state.token:
    st.warning("🔒 You must be logged in as Admin to create categories.")
    st.stop()

if st.session_state.get("user_role") != "Admin":
    st.error("Only Admins can access this page.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}

with st.form("category_form"):
    name = st.text_input("Category name")
    description = st.text_area("Description (optional)")
    submitted = st.form_submit_button("Create Category")

    if submitted and name:
        payload = {"name": name, "description": description}
        try:
            res = requests.post(f"{API_URL}/categories", json=payload, headers=headers)
            if res.status_code == 200:
                st.success("Category created successfully.")
            else:
                st.error("Failed to create category: " + res.text)
        except Exception as e:
            st.error(f"Backend error: {e}")
