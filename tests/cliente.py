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
        time.sleep(0.5)
        return res.json()["idToken"]
    else:
        raise Exception("Login falhou: " + res.text)

@pytest.fixture(scope="session")
def client_token():
    return get_token("testuser@gmail.com", "1q2w3e4r5t6y")

def  test_client_view_events(client_token):
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

def test_client_comment_event(client_token):
    headers = {"Authorization": f"Bearer {client_token}"}

    # Obter um evento existente
    eventos = client.get("/events", headers=headers).json()
    assert eventos, "Precisas de pelo menos um evento criado"
    evento_id = eventos[0]["id"]

    # Enviar comentário
    comment_data = {
        "text": "Comentário de teste do cliente",
        "author": "Cliente Teste"
    }
    res_comment = client.post(f"/events/{evento_id}/comment", json=comment_data, headers=headers)
    assert res_comment.status_code == 200
    assert "Comment added successfully" in res_comment.json()["message"]



