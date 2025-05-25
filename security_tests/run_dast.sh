import requests

BASE_URL = "http://backend:8000"  # Usa 'backend' porque o teste corre na mesma rede docker-compose

def test_root():
    print("== GET / ==")
    r = requests.get(f"{BASE_URL}/")
    print("Status:", r.status_code)
    print("Response:", r.json())

def test_login_sql_injection():
    print("\n== POST /login com payload SQLi ==")
    payload = {"email": "admin' OR '1'='1", "password": "123"}
    r = requests.post(f"{BASE_URL}/login", json=payload)
    print("Status:", r.status_code)
    try:
        print("Response:", r.json())
    except Exception:
        print("Response:", r.text)

def test_login_empty_email():
    print("\n== POST /login com email vazio ==")
    payload = {"email": "", "password": "qualquer"}
    r = requests.post(f"{BASE_URL}/login", json=payload)
    print("Status:", r.status_code)
    try:
        print("Response:", r.json())
    except Exception:
        print("Response:", r.text)

if __name__ == "__main__":
    test_root()
    test_login_sql_injection()
    test_login_empty_email()
