import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import requests
from fastapi.testclient import TestClient
from app.main import app
from dotenv import load_dotenv
from firebase_admin import credentials, auth, initialize_app
from google.cloud import firestore
import firebase_admin
import time
import datetime
import json

load_dotenv()



client = TestClient(app)
db = firestore.Client()
categorianome =""

if not firebase_admin._apps:
    cred = credentials.Certificate("app/firebase_key.json")
    firebase_admin.initialize_app(cred)

categories_ref = db.collection("categories")
categories_docs = categories_ref.stream()

for doc in categories_docs:
    categorianome=doc.id

def get_token(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={os.getenv('FIREBASE_API_KEY')}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    res = requests.post(url, json=payload)
    if res.status_code == 200:
        time.sleep(0.5)
        return res.json()["idToken"]
    else:
        raise Exception("Login falhou: " + res.text)

@pytest.fixture(scope="session")
def client_token():
    return get_token("testuser@gmail.com", os.getenv("CLIENT_CRED"))

def  test_client_view_events(client_token):
    headers = {"Authorization": f"Bearer {client_token}"}
    res = client.get("/events", headers=headers)
    assert res.status_code == 200, f"Expected status code 200, but got {res.status_code}"
    
    response_data = res.json()
    assert isinstance(response_data["events"], list), "Response 'events' is not a list"

def test_client_filter_events(client_token):
    headers = {"Authorization": f"Bearer {client_token}"}
    res = client.get("/events/filter?start=2025-01-01&end=2025-12-31", headers=headers, timeout=10)
    assert res.status_code == 200, f"Expected status code 200, but got {res.status_code}"

    response_data = res.json()
    assert isinstance(response_data, list), "Response data is not a list"

def test_client_cannot_create_event(client_token):
    headers = {"Authorization": f"Bearer {client_token}"}
    data = {
        "title": "Client Attempt",
        "date": "2025-08-01",
        "description": "Tentativa ilegal",
        "image_url": "",
        "category": categorianome
    }
    res = client.post("/events/create", json=data, headers=headers)
    assert res.status_code == 403, f"Expected status code 403, but got {res.status_code}"

def test_client_comment_event(client_token):
    headers = {"Authorization": f"Bearer {client_token}"}

    eventos = client.get("/events", headers=headers).json()
    assert eventos.get("events"), "Precisas de pelo menos um evento criado"
    evento_id = eventos["events"][0]["id"]

    comment_data = {
        "text": "Comentário de teste do cliente",
        "author": "Cliente Teste"
    }
    res_comment = client.post(f"/events/{evento_id}/comment", json=comment_data, headers=headers, timeout=10)
    assert res_comment.status_code == 200, f"Expected status code 200, but got {res_comment.status_code}"
    assert "Comment added successfully" in res_comment.json().get("message", ""), "Message 'Comment added successfully' not found"



def test_client_register_user_to_event(client_token):
    headers = {"Authorization": f"Bearer {client_token}"}
    res = client.get("/events", headers=headers)
    assert res.status_code == 200, f"Expected status code 200, but got {res.status_code}"
    events = res.json()
    assert events.get("events"), "No events found"
    event_id = events["events"][0]["id"]
    res = client.post(f"/events/{event_id}/register", headers=headers)
    assert res.status_code == 200, f"Expected status code 200, but got {res.status_code}"

    response_msg = res.json().get("message", "").lower()
    assert "registered" in response_msg or "already registered" in response_msg, \
        f"Unexpected registration message: {response_msg}"


import datetime
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_event_manager_cannot_delete_comment(client_token):
    headers = {
        "Authorization": f"Bearer {client_token}",
        "Content-Type": "application/json"
    }

    res = client.get("/events", headers=headers)
    assert res.status_code == 200, f"Expected status code 200, got {res.status_code}"
    events = res.json()
    assert "events" in events and events["events"], "No events found"

    event_id = events["events"][0]["id"]

    comment = {
        "author": "Cliente Teste",
        "text": "Comentário de cliente para testar DELETE",
        "timestamp": datetime.datetime.utcnow().replace(microsecond=0).isoformat()
    }

    post_res = client.post(f"/events/{event_id}/comment", headers=headers, json=comment)
    assert post_res.status_code == 200, f"Expected 200 on comment post, got {post_res.status_code}"

    delete_res = client.request(
    method="DELETE",
    url=f"/events/{event_id}/comment",
    headers=headers,
    data=json.dumps(comment)
)
    assert delete_res.status_code == 403, f"Expected 403, got {delete_res.status_code}"
