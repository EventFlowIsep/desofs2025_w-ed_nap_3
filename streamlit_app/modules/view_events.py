import streamlit as st
import requests
import os
from datetime import datetime, date

API_URL = os.getenv("API_URL", "http://localhost:8000")
DEFAULT_TIMEOUT = 10

def show():
    st.title("📅 All Events")

    if "token" not in st.session_state or not st.session_state.token:
        st.warning("🔒 You must be logged in to view events.")
        return

    headers = {"Authorization": f"Bearer {st.session_state.token}"}

    # 🔍 Filter section (by start date only)
    with st.expander("🔍 Filter Events"):
        start_date = st.date_input("Show events starting from:", value=date.today(), key="start_date_filter")
        exclude_cancelled = st.checkbox("Exclude cancelled events", value=True, key="cancelled_filter")
        filter_clicked = st.button("Apply Filter", key="filter_button")

    try:
        res = requests.get(f"{API_URL}/events", headers=headers, timeout=DEFAULT_TIMEOUT)
        if res.status_code == 200:
            events = res.json()
            if not events:
                st.info("No events available yet.")
            else:
                if filter_clicked:
                    events = [e for e in events if "date" in e and e["date"] >= start_date.strftime("%Y-%m-%d")]
                    if exclude_cancelled:
                        events = [e for e in events if not e.get("cancelled", False)]
                    events.sort(key=lambda x: x["date"])

                cat_res = requests.get(f"{API_URL}/categories", headers=headers, timeout=DEFAULT_TIMEOUT)
                if cat_res.status_code == 200:
                    categories = cat_res.json()
                    category_names = [c['name'] for c in categories]
                else:
                    category_names = []

                for ev in events:
                    st.markdown("---")
                    st.subheader(ev.get("title", "Untitled Event"))
                    st.write(f"📆 Date: {ev.get('date', 'Unknown')}")
                    st.write(f"📝 Description: {ev.get('description', 'No description provided.')}")
                    st.write(f"👤 Created by: {ev.get('created_by', 'Unknown')}")
                    st.write(f"🏷 Category: {ev.get('category', 'Uncategorized')}")

                    image_url = ev.get("image_url")
                    if image_url:
                        st.image(image_url, caption="Event image", use_container_width=True)

                    if ev.get("cancelled"):
                        st.warning("🚫 This event has been cancelled.")

                    st.markdown("**💬 Comments:**")
                    comments = ev.get("comments", [])
                    if comments:
                        for c in comments:
                            st.markdown(f"- **{c.get('author', 'Anonymous')}:** {c.get('text', '')}")
                            if st.session_state.get("user_role") in ["Admin", "Moderator"] or (
                                st.session_state.get("user_role") == "Event_manager" and ev.get("created_by") == st.session_state.get("user_email")
                            ):
                                with st.form(f"delete_comment_{ev['id']}_{c['timestamp']}"):
                                    st.write("🗑️ Delete this comment:")
                                    if st.form_submit_button("Delete"):
                                        payload = {
                                            "author": c["author"],
                                            "timestamp": c["timestamp"],
                                            "text": c["text"]
                                        }
                                        del_res = requests.delete(f"{API_URL}/events/{ev['id']}/comment", json=payload, headers=headers)
                                        if del_res.status_code == 200:
                                            st.success("Comment deleted.")
                                            st.rerun()
                                        else:
                                            st.error("Failed to delete comment.")
                    else:
                        st.write("No comments yet.")

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
                            comment_res = requests.post(f"{API_URL}/events/{ev['id']}/comment", json=payload, headers=headers, timeout=DEFAULT_TIMEOUT)
                            if comment_res.status_code == 200:
                                st.success("Comment posted.")
                                st.rerun()
                            else:
                                st.error("Failed to post comment.")

                    if not ev.get("cancelled"):
                        already_registered = any(
                            r.get("email") == st.session_state.get("user_email")
                            for r in ev.get("registrations", [])
                        )
                        if already_registered:
                            st.success("✅ You are already registered for this event.")
                        elif st.button("📥 Register for this event", key=f"register_{ev['id']}"):
                            reg_res = requests.post(f"{API_URL}/events/{ev['id']}/register", headers=headers)
                            if reg_res.status_code == 200:
                                st.success("Registered successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to register.")

                    if st.session_state.get("user_role") in ["Admin", "Event_manager"]:
                        with st.expander("✏️ Edit Event"):
                            new_title = st.text_input("Title", value=ev.get("title", ""), key=f"title_{ev['id']}")
                            new_date = st.date_input("Date", value=datetime.strptime(ev.get("date"), "%Y-%m-%d"), key=f"date_{ev['id']}")
                            new_desc = st.text_area("Description", value=ev.get("description", ""), key=f"desc_{ev['id']}")
                            new_image = st.text_input("Image URL", value=ev.get("image_url", ""), key=f"img_{ev['id']}")
                            new_category = st.selectbox("Category", category_names, index=category_names.index(ev.get("category", "Uncategorized")), key=f"cat_{ev['id']}")
                            if st.button("Save Changes", key=f"save_{ev['id']}"):
                                payload = {
                                    "title": new_title,
                                    "date": new_date.strftime("%Y-%m-%d"),
                                    "description": new_desc,
                                    "image_url": new_image,
                                    "category": new_category
                                }
                                update_res = requests.put(f"{API_URL}/events/{ev['id']}", json=payload, headers=headers, timeout=DEFAULT_TIMEOUT)
                                if update_res.status_code == 200:
                                    st.success("Event updated successfully!")
                                    st.rerun()
                                else:
                                    st.error("Failed to update event.")
        else:
            st.error("Failed to load events.")
    except Exception as e:
        st.error(f"Backend error: {e}")
