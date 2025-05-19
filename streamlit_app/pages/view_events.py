import streamlit as st
import requests
import os

st.set_page_config(page_title="View Events", page_icon="📅")

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.title("📅 All Events")

if "token" not in st.session_state:
    st.error("You must be logged in to view events.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}

try:
    res = requests.get(f"{API_URL}/events", headers=headers)
    if res.status_code == 200:
        events = res.json()
        if not events:
            st.info("No events available yet.")
        else:
            for ev in events:
                st.markdown("---")
                st.subheader(ev.get("title", "Untitled Event"))
                st.write(f"📆 Date: {ev.get('date', 'Unknown')}  ")
                st.write(f"📝 Description: {ev.get('description', 'No description provided.')}")
                st.write(f"👤 Created by: {ev.get('created_by', 'Unknown')}")

                # Optional image display
                image_url = ev.get("image_url")
                if image_url:
                    st.image(image_url, caption="Event image", use_container_width=True)

                # Cancelled warning
                if ev.get("cancelled"):
                    st.warning("🚫 This event has been cancelled.")

                # Comments section
                st.markdown("**💬 Comments:**")
                comments = ev.get("comments", [])
                if comments:
                    for c in comments:
                        st.markdown(f"- **{c.get('author', 'Anonymous')}:** {c.get('text', '')}")
                else:
                    st.write("No comments yet.")

                # Add a comment
                with st.form(f"comment_form_{ev['id']}"):
                    comment_text = st.text_input("Write a comment:", key=f"comment_{ev['id']}")
                    author = st.text_input("Your name (optional):", key=f"author_{ev['id']}")
                    submitted = st.form_submit_button("Post comment")
                    if submitted and comment_text:
                        payload = {
                            "event_id": ev["id"],
                            "text": comment_text,
                            "author": author or "guest"
                        }
                        comment_res = requests.post(f"{API_URL}/events/{ev['id']}/comment", json=payload, headers=headers)
                        if comment_res.status_code == 200:
                            st.success("Comment posted.")
                            st.rerun()
                        else:
                            st.error("Failed to post comment.")
    else:
        st.error("Failed to load events.")
except Exception as e:
    st.error(f"Backend error: {e}")
