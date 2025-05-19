import streamlit as st
import requests
import os
import datetime
import firebase_admin
from firebase_admin import credentials, storage

st.set_page_config(page_title="Create Event", page_icon="➕")

API_URL = os.getenv("API_URL", "http://localhost:8000")
FIREBASE_CREDENTIALS = "app/firebase_key.json"
FIREBASE_BUCKET = "desofs2025w-ednap3.appspot.com"

# Initialize Firebase Storage if not already
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS)
    firebase_admin.initialize_app(cred, {
        'storageBucket': FIREBASE_BUCKET
    })

st.title("➕ Create New Event")

if "token" not in st.session_state:
    st.error("You must be logged in to create an event.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}

# Retrieve and validate role
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

title = st.text_input("Event Title")
date = st.date_input("Event Date", min_value=datetime.date.today())
description = st.text_area("Event Description")
image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

# Submit form
if st.button("Create Event"):
    if not title or not date:
        st.warning("Please provide a title and date.")
    else:
        image_url = ""
        if image:
            try:
                bucket = storage.bucket()
                blob = bucket.blob(f"event_images/{image.name}")
                blob.upload_from_file(image, content_type=image.type)
                blob.make_public()
                image_url = blob.public_url
            except Exception as e:
                st.error(f"Failed to upload image: {e}")

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
