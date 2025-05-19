import streamlit as st
import requests
import os

st.set_page_config(page_title="Cancel Events", page_icon="❌")

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.title("❌ Cancel Events")

if "token" not in st.session_state:
    st.error("You must be logged in to cancel events.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}

# Check and enforce role
if "user_role" not in st.session_state or not st.session_state.user_role:
    try:
        res = requests.get(f"{API_URL}/verify-token", headers=headers)
        if res.status_code == 200:
            st.session_state.user_role = res.json().get("role", "client")
    except:
        st.session_state.user_role = "client"

if st.session_state.user_role not in ["admin", "event_manager"]:
    st.warning("You do not have permission to access this page.")
    st.stop()

try:
    res = requests.get(f"{API_URL}/events", headers=headers)
    if res.status_code == 200:
        events = res.json()
        uncancelled = [e for e in events if not e.get("cancelled")]
        if not uncancelled:
            st.info("There are no active events to cancel.")
        else:
            for ev in uncancelled:
                st.markdown("---")
                st.subheader(ev.get("title", "Untitled"))
                st.write(f"📆 {ev.get('date', 'Unknown')} | 👤 {ev.get('created_by', 'Unknown')}")
                if st.button(f"Cancel '{ev['title']}'", key=f"cancel_{ev['id']}"):
                    cancel_res = requests.post(f"{API_URL}/events/{ev['id']}/cancel", headers=headers)
                    if cancel_res.status_code == 200:
                        st.success(f"Event '{ev['title']}' cancelled successfully.")
                        st.rerun()
                    else:
                        st.error("Failed to cancel the event.")
    else:
        st.error("Failed to load events.")
except Exception as e:
    st.error(f"Backend error: {e}")
