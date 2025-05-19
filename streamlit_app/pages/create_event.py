import streamlit as st
import requests
import os
import datetime
import cloudinary
import cloudinary.uploader

st.set_page_config(page_title="Create Event", page_icon="➕")

API_URL = os.getenv("API_URL", "http://localhost:8000")

cloudinary.config(
  cloud_name = "dfe2gzr7c",
  api_key = "518849434635411",
  api_secret = "Sz2i5BLKWqNA_Pbn42G4tx7FAs8"
)

st.title("➕ Create New Event")

if "token" not in st.session_state:
    st.error("You must be logged in to create an event.")
    st.stop()

if st.session_state.get("user_role") not in ["admin", "event_manager"]:
    st.warning("You do not have permission to create events.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}

title = st.text_input("Event Title")
date = st.date_input("Event Date", min_value=datetime.date.today())
description = st.text_area("Event Description")
image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

# Upload to Imgur
image_url = ""
if image:
    try:
        result = cloudinary.uploader.upload(image)
        image_url = result["secure_url"]
        st.image(image_url, caption="Uploaded image preview", use_container_width=True)
    except Exception as e:
        st.warning(f"Image upload failed: {e}")

if st.button("Create Event"):
    if not title or not date:
        st.warning("Please provide a title and date.")
    else:
        payload = {
            "title": title,
            "date": date.strftime("%Y-%m-%d"),
            "description": description,
            "image_url": image_url
        }
        res = requests.post(f"{API_URL}/events/create", json=payload, headers=headers)
        if res.status_code == 200:
            st.success("✅ Event created successfully!")
        else:
            st.error(f"Failed to create event: {res.text}")
