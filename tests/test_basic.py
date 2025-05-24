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

load_dotenv()

client = TestClient(app)
categorianome =""

# 🔐 Funções para obter os tokens de cada utilizador
def get_token(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={os.getenv('FIREBASE_API_KEY')}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    res = requests.post(url, json=payload)
    if res.status_code == 200:
        return res.json()["idToken"]
    else:
        raise Exception("Login falhou: " + res.text)

# 🔐 Fixtures para cada role
@pytest.fixture(scope="session")
def admin_token():
    return get_token("adminuser@gmail.com", "1q2w3e4r5t6y")

@pytest.fixture(scope="session")
def client_token():
    return get_token("testuser@gmail.com", "1q2w3e4r5t6y")

# -------------------------------
# 👑 TESTES DO ADMINISTRADOR
# -------------------------------

def test_admin_create_event(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    data = {
        "title": "Admin Event Test",
        "date": "2025-07-01",
        "description": "Criado por Admin",
        "image_url": "",
        "category": categorianome
    }
    res = client.post("/events/create", json=data, headers=headers)
    assert res.status_code == 200
    assert "Event created successfully" in res.json()["message"]

def test_admin_list_events(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/events", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

# -------------------------------
# 👤 TESTES DO CLIENTE
# -------------------------------

def test_client_view_events(client_token):
    headers = {"Authorization": f"Bearer {client_token}"}
    res = client.get("/events", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_client_filter_events(client_token):
    headers = {"Authorization": f"Bearer {client_token}"}
    res = client.get("/events/filter?start=2025-01-01&end=2025-12-31", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

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
    assert res.status_code == 403  # Cliente não tem permissão


if not firebase_admin._apps:
    cred = credentials.Certificate("app/firebase_key.json")
    firebase_admin.initialize_app(cred)

db = firestore.Client()

categories_ref = db.collection("categories")
categories_docs = categories_ref.stream()

for doc in categories_docs:
    categorianome=doc.id


