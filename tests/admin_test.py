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
import uuid
from app.main import in_memory_cache
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

    for attempt in range(3):  # Retry até 3 vezes
        res = client.post("/events/create", json=data, headers=headers)
        if res.status_code == 200:
            break
        time.sleep(1)

    assert res.status_code == 200, f"Expected 200 but got {res.status_code}"
    response_data = res.json()
    assert "Event created successfully" in response_data.get("message", ""), "Event creation message not found"


def test_admin_list_events(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    for attempt in range(3):  # Retry até 3 vezes
        res = client.get("/events", headers=headers)
        if res.status_code == 200:
            break
        time.sleep(1)

    assert res.status_code == 200, f"Expected 200 but got {res.status_code}"
    response_data = res.json()
    assert isinstance(response_data, dict), "Response data is not a dict"
    assert "events" in response_data, "'events' key not found in response"
    assert isinstance(response_data["events"], list), "Response 'events' is not a list"


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
    assert res_create.status_code == 200, f"[CREATE ERROR] {res_create.text}"

    evento_id = None
    max_attempts = 5
    for attempt in range(max_attempts):
        res_list = client.get("/events?per_page=100", headers=headers)
        assert res_list.status_code == 200, f"[LIST ERROR] Tentativa {attempt+1}: {res_list.text}"
        eventos = res_list.json().get("events", [])
        for e in eventos:
            if e["title"] == "Evento para Cancelar":
                evento_id = e["id"]
                break
        if evento_id:
            break
        time.sleep(1)

    assert evento_id is not None, "Evento para Cancelar não encontrado após várias tentativas"

    res_cancel = client.post(f"/events/{evento_id}/cancel", headers=headers)
    assert res_cancel.status_code == 200, f"[CANCEL ERROR] {res_cancel.text}"
    assert f"Event {evento_id} cancelled." in res_cancel.json()["message"], "Mensagem de cancelamento não encontrada"


def test_admin_edit_event(admin_token):
    in_memory_cache.clear()
    headers = {"Authorization": f"Bearer {admin_token}"}

    unique_title = f"Evento Editar {uuid.uuid4()}"
    print(f"[DEBUG] Criar evento com título: {unique_title}")

    create_payload = {
        "title": unique_title,
        "date": "2025-12-31",
        "description": "Descrição original",
        "image_url": "",
        "category": "Categoria Teste"
    }

    res_create = client.post("/events/create", json=create_payload, headers=headers)
    assert res_create.status_code == 200, f"[CREATE ERROR] {res_create.text}"
    evento_id = res_create.json()["event_id"]

    update_payload = {
        "title": "Evento Editado com Sucesso",
        "description": "Nova descrição do Admin",
        "date": "2026-01-01",
        "image_url": "",
        "category": "Categoria Teste"
    }

    res_update = client.put(f"/events/{evento_id}", json=update_payload, headers=headers)
    assert res_update.status_code == 200, f"[UPDATE ERROR] {res_update.text}"

    data = res_update.json()
    assert data.get("msg") == "Event updated successfully.", f"[MENSAGEM INVÁLIDA] {data}"




def test_admin_delete_comment(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    category_name = "Categoria Teste"
    client.post("/categories", json={"name": category_name, "description": "para teste"}, headers=headers)

    event_data = {
        "title": "Evento com Comentário",
        "date": "2025-12-01",
        "description": "Evento para teste de delete de comentário",
        "image_url": "",
        "category": category_name
    }
    res_create = client.post("/events/create", json=event_data, headers=headers)
    assert res_create.status_code == 200, f"[CREATE ERROR] {res_create.text}"

    evento_id = None
    for attempt in range(5):
        res_list = client.get("/events?per_page=100", headers=headers)
        assert res_list.status_code == 200
        eventos = res_list.json().get("events", [])
        for e in eventos:
            if e["title"] == "Evento com Comentário":
                evento_id = e["id"]
                break
        if evento_id:
            break
        time.sleep(1)
    assert evento_id is not None, "Evento não encontrado após várias tentativas"

    comment_text = "Comentário a remover"
    comment_payload = {
        "author": "Admin Tester",
        "text": comment_text,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    res_comment = client.post(f"/events/{evento_id}/comment", json=comment_payload, headers=headers)
    assert res_comment.status_code == 200, f"[COMMENT ERROR] {res_comment.text}"

    comment_dict = None
    for attempt in range(5):
        res_event = client.get("/events?per_page=100", headers=headers)
        assert res_event.status_code == 200
        eventos = res_event.json().get("events", [])
        for e in eventos:
            if e["id"] == evento_id and "comments" in e:
                for c in e["comments"]:
                    if c["text"] == comment_text:
                        comment_dict = c
                        break
        if comment_dict:
            break
        time.sleep(1)

    assert comment_dict is not None, "Comentário não encontrado após várias tentativas"

    res_delete = client.request(
        method="DELETE",
        url=f"/events/{evento_id}/comment",
        headers={**headers, "Content-Type": "application/json"},
        data=json.dumps(comment_dict)
    )
    assert res_delete.status_code == 200, f"Esperado 200, mas obtido {res_delete.status_code}"



def test_admin_register_user_to_event(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/events", headers=headers)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}"
    events = res.json()["events"]
    assert events, "No events found"
    event_id = events[0]["id"]
    res = client.post(f"/events/{event_id}/register", headers=headers)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}"
    assert "registered" in res.json()["message"].lower(), "Registration message not found"
   

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

    
# teste =get_token("adminuser@gmail.com", os.getenv("ADMIN_CRED"))
# aa = test_admin_delete_comment(teste)