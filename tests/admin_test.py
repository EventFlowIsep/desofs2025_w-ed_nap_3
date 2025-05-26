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

def get_token(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={os.getenv('FIREBASE_API_KEY')}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    res = requests.post(url, json=payload, timeout=10)
    if res.status_code == 200:
        time.sleep(0.5)
        return res.json()["idToken"]
    else:
        raise Exception("Login falhou: " + res.text)

@pytest.fixture(scope="session")
def admin_token():
    return get_token("adminuser@gmail.com", os.getenv("ADMIN_CRED"))


# -------------------------------
#           ADMIN TEST
# -------------------------------

def test_admin_create_event(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    data = {
        "title": "Admin Event Test",
        "date": "2025-07-01",
        "description": "Criado por Admin",
        "image_url": "",
        "category": "Categoria Teste"
    }
    res = client.post("/events/create", json=data, headers=headers)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}"
    response_data = res.json()
    assert "Event created successfully" in response_data.get("message", ""), "Event creation message not found"


def test_admin_list_events(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/events", headers=headers)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}"
    response_data = res.json()
    assert isinstance(response_data, list), "Response data is not a list"


def test_admin_cancel_event(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    data = {
        "title": "Evento para Cancelar",
        "date": "2025-09-01",
        "description": "Este evento será cancelado",
        "image_url": "",
        "category": "Categoria Teste"
    }
    res_create = client.post("/events/create", json=data, headers=headers)
    assert res_create.status_code == 200

    res_list = client.get("/events", headers=headers)
    eventos = res_list.json()
    evento_id = next(e["id"] for e in eventos if e["title"] == "Evento para Cancelar")

    res_cancel = client.post(f"/events/{evento_id}/cancel", headers=headers)
    assert res_cancel.status_code == 200, f"Expected 200 but got {res_cancel.status_code}"
    assert f"Event {evento_id} cancelled." in res_cancel.json()["message"], "Event cancellation message not found"


def test_admin_edit_event(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    data = {
        "title": "Evento a Editar",
        "date": "2025-10-01",
        "description": "testeEliminar",
        "image_url": "",
        "category": "Categoria Teste"
    }
    res = client.post("/events/create", json=data, headers=headers)
    assert res.status_code == 200

    eventos = client.get("/events", headers=headers).json()
    evento_id = next((e["id"] for e in eventos if e["title"] == "Evento a Editar"), None)
    assert evento_id is not None, "Evento não encontrado"

    update_data = {
        "title": "Evento Editado",
        "description": "Descrição atualizada pelo Admin",
        "date": "2025-10-01",
        "image_url": "",
        "category": "Categoria Teste"
    }
    res_update = client.put(f"/events/{evento_id}", json=update_data, headers=headers)
    assert res_update.status_code == 200, f"Expected 200 but got {res_update.status_code}"
    assert res_update.json()["msg"] == "Event updated successfully.", "Event update message not found"




def test_admin_delete_comment(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Criar categoria se necessário
    category_name = "Categoria Teste"
    client.post("/categories", json={"name": category_name, "description": "para teste"}, headers=headers)

    # Criar evento
    event_data = {
        "title": "Evento com Comentário",
        "date": "2025-12-01",
        "description": "Evento para teste de delete de comentário",
        "image_url": "",
        "category": category_name
    }
    res_create = client.post("/events/create", json=event_data, headers=headers)
    assert res_create.status_code == 200

    # Obter ID do evento
    eventos = client.get("/events", headers=headers).json()
    evento_id = next(e["id"] for e in eventos if e["title"] == "Evento com Comentário")

    # Criar comentário
    comment_text = "Comentário a remover"
    comment_payload = {
        "author": "Admin Tester",
        "text": comment_text,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    res_comment = client.post(f"/events/{evento_id}/comment", json=comment_payload, headers=headers)
    assert res_comment.status_code == 200

    # 💤 Esperar um pouco para garantir que Firestore já gravou
    time.sleep(1)

    # Ir buscar o evento para obter o comentário real
    res_event = client.get("/events", headers=headers)
    assert res_event.status_code == 200
    evento = next(e for e in res_event.json() if e["id"] == evento_id)

    # Procurar o comentário com o texto que sabemos
    real_comment = next(c for c in evento["comments"] if c["text"] == comment_text)

    # Apagar comentário com base no que foi realmente guardado
    res_delete = client.request(
        method="DELETE",
        url=f"/events/{evento_id}/comment",
        headers={**headers, "Content-Type": "application/json"},
        data=json.dumps(real_comment)
    )
    assert res_delete.status_code == 200, f"Esperado 200, mas obtido {res_delete.status_code}"



def test_admin_register_user_to_event(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/events", headers=headers)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}"
    events = res.json()
    assert events, "No events found"
    event_id = events[0]["id"]
    res = client.post(f"/events/{event_id}/register", headers=headers)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}"
    assert "registered" in res.json()["msg"].lower(), "Registration message not found"
   

def test_admin_create_category(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "name": "Categoria Teste",
        "description": "Criada para testes."
    }
    res = client.post("/categories", headers=headers, json=payload)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}"
    response_data = res.json()
    assert "created" in response_data.get("msg", "").lower(), "Category creation message not found in response."


def test_admin_list_categories(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/categories", headers=headers)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}"
    categories = res.json()
    assert isinstance(categories, list), "Response data is not a list of categories"

    
teste =get_token("adminuser@gmail.com", os.getenv("ADMIN_CRED"))
aa = test_admin_delete_comment(teste)