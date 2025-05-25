import requests
import os

FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
BASE_URL = f"https://identitytoolkit.googleapis.com/v1"

if not FIREBASE_API_KEY:
    print("❌ FIREBASE_API_KEY not found. Set it in GitHub secrets or environment.")
    exit(1)

def print_result(name, response):
    print(f"\n== {name} ==")
    print(f"Status code: {response.status_code}")
    try:
        print("Response JSON:", response.json())
    except Exception:
        print("Response Text:", response.text)

print("Testing Firebase login with SQL Injection payload")
try:
    r = requests.post(f"{BASE_URL}/accounts:signInWithPassword?key={FIREBASE_API_KEY}", json={
        "email": "test@example.com' OR '1'='1",
        "password": "fakepass",
        "returnSecureToken": True
    }, timeout=10)
    print_result("Login SQL Injection", r)
except Exception as e:
    print("Erro:", e)

print("\nTesting login with empty email")
try:
    r = requests.post(f"{BASE_URL}/accounts:signInWithPassword?key={FIREBASE_API_KEY}", json={
        "email": "",
        "password": "123456",
        "returnSecureToken": True
    },timeout=10)
    print_result("Login Empty Email", r)
except Exception as e:
    print("Erro:", e)

print("\nTesting registration with XSS in email")
try:
    r = requests.post(f"{BASE_URL}/accounts:signUp?key={FIREBASE_API_KEY}", json={
        "email": "<script>alert('xss')</script>@test.com",
        "password": "123456",
        "returnSecureToken": True
    },timeout=10)
    print_result("Register XSS Email", r)
except Exception as e:
    print("Erro:", e)

print("\nTesting registration with short password")
try:
    r = requests.post(f"{BASE_URL}/accounts:signUp?key={FIREBASE_API_KEY}", json={
        "email": "validuser@test.com",
        "password": "12",
        "returnSecureToken": True
    },timeout=10)
    print_result("Register Short Password", r)
except Exception as e:
    print("Erro:", e)

print("\n✅ DAST Firebase tests completed.")
