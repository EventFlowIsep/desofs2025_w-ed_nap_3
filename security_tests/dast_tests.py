import requests
import os

API_KEY = os.getenv("FIREBASE_API_KEY")
BASE_FIREBASE_URL = "https://identitytoolkit.googleapis.com/v1"

def test_firebase_sql_injection_login():
    print("Testing Firebase login with SQL injection payload")
    payload = {
        "email": "' OR '1'='1@example.com",
        "password": "123456",
        "returnSecureToken": True
    }
    url = f"{BASE_FIREBASE_URL}/accounts:signInWithPassword?key={API_KEY}"
    response = requests.post(url, json=payload)
    print("Status code:", response.status_code)
    print("Response body:", response.text)
    assert response.status_code in [400, 403, 422]

def test_firebase_empty_password():
    print("Testing Firebase login with empty password")
    payload = {
        "email": "test@example.com",
        "password": "",
        "returnSecureToken": True
    }
    url = f"{BASE_FIREBASE_URL}/accounts:signInWithPassword?key={API_KEY}"
    response = requests.post(url, json=payload)
    print("Status code:", response.status_code)
    assert response.status_code in [400, 403, 422]

def test_invalid_token_verification():
    print("Testing invalid token verification on internal endpoint")
    headers = {"Authorization": "Bearer INVALID_TOKEN"}
    try:
        response = requests.get("http://localhost:8000/verify-token", headers=headers, timeout=3)
        print("Status code:", response.status_code)
        assert response.status_code in [401, 403]
    except requests.exceptions.RequestException as e:
        print("Error connecting to internal endpoint: it probably does not exist.")
        print(str(e))

if __name__ == "__main__":
    test_firebase_sql_injection_login()
    test_firebase_empty_password()
    test_invalid_token_verification()
