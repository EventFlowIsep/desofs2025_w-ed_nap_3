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
categorianome =""
if not firebase_admin._apps:
    cred = credentials.Certificate("app/firebase_key.json")
    firebase_admin.initialize_app(cred)

db = firestore.Client()

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

# 🔐 Fixtures para cada role
@pytest.fixture(scope="session")
def admin_token():
    return get_token("adminuser@gmail.com", "1q2w3e4r5t6y")


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


def test_admin_cancel_event(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Primeiro cria um evento para cancelar
    data = {
        "title": "Evento para Cancelar",
        "date": "2025-09-01",
        "description": "Este evento será cancelado",
        "image_url": "",
        "category": categorianome
    }
    res_create = client.post("/events/create", json=data, headers=headers)
    assert res_create.status_code == 200

    # Obter o ID do evento recém-criado
    res_list = client.get("/events", headers=headers)
    eventos = res_list.json()
    evento_id = next(e["id"] for e in eventos if e["title"] == "Evento para Cancelar")

    # Cancelar o evento
    res_cancel = client.post(f"/events/{evento_id}/cancel", headers=headers)
    assert res_cancel.status_code == 200
    assert f"Event {evento_id} cancelled." in res_cancel.json()["message"]

def test_admin_edit_event(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Criar evento
    data = {
        "title": "Evento a Editar",
        "date": "2025-10-01",
        "description": "testeEliminar",
        "image_url": "",
        "category": categorianome
    }
    res = client.post("/events/create", json=data, headers=headers)
    assert res.status_code == 200

    # Obter ID do evento recém-criado
    eventos = client.get("/events", headers=headers).json()
    evento_id = next(
        (e["id"] for e in eventos if e["title"] == "Evento a Editar" and e["description"] == "testeEliminar"),
        None
    )

    # Atualizar o evento (respeitando o modelo EventUpdate)
    update_data = {
        "title": "Evento Editado",
        "description": "Descrição atualizada pelo Admin",
        "date": "2025-10-01",
        "image_url": "",
        "category": categorianome
    }
    res_update = client.put(
        f"/events/{evento_id}",
        json=update_data,
        headers=headers
    )
    assert res_update.status_code == 200
    assert res_update.json()["msg"] == "Event updated successfully."

def test_admin_delete_comment(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Criar evento
    event_data = {
        "title": "Evento com Comentário",
        "date": "2025-12-01",
        "description": "Evento para teste de delete de comentário",
        "image_url": "",
        "category": categorianome
    }
    res_create = client.post("/events/create", json=event_data, headers=headers)
    assert res_create.status_code == 200

    # 2. Obter ID do evento
    eventos = client.get("/events", headers=headers).json()
    evento_id = next(e["id"] for e in eventos if e["title"] == "Evento com Comentário")

    # 3. Adicionar comentário
    comment = {
        "author": "Admin Tester",
        "text": "Comentário a remover",
        "timestamp": datetime.datetime.utcnow().replace(microsecond=0).isoformat()
    }
    res_comment = client.post(f"/events/{evento_id}/comment", json=comment, headers=headers)
    assert res_comment.status_code == 200

    # 4. Apagar comentário — usar data + headers
    headers["Content-Type"] = "application/json"
    res_delete = client.request(
    method="DELETE",
    url=f"/events/{evento_id}/comment",
    headers=headers,
    data=json.dumps(comment))


def test_admin_register_user_to_event(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/events", headers=headers)
    assert res.status_code == 200
    events = res.json()
    assert events, "No events found"
    event_id = events[0]["id"]
    res = client.post(f"/events/{event_id}/register", headers=headers)
    assert res.status_code == 200
    assert "registered" in res.json()["msg"].lower()
   

def test_admin_create_category(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "name": "Categoria Teste",
        "description": "Criada para testes."
    }
    res = client.post("/categories", headers=headers, json=payload)
    assert res.status_code == 200
    assert "created" in res.json()["msg"].lower()


def test_admin_list_categories(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/categories", headers=headers)
    assert res.status_code == 200
    categories = res.json()
    assert isinstance(categories, list)

    
teste =get_token("adminuser@gmail.com", "1q2w3e4r5t6y")
aa = test_admin_delete_comment(teste)