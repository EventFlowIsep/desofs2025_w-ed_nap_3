import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

def print_result(name, response):
    print(f"\n== {name} ==")
    print(f"Status code: {response.status_code}")
    try:
        print("Response JSON:", response.json())
    except Exception:
        print("Response Text:", response.text)

# Test 1: Invalid token verification
print("Testing /verify-token with invalid token")
headers = {"Authorization": "Bearer invalidtoken123"}
try:
    r = requests.get(f"{API_URL}/verify-token", headers=headers)
    print_result("Invalid Token Verification", r)
except Exception as e:
    print("Erro:", e)

# Test 2: accessing /events without token
print("\nTesting /events without token")
try:
    r = requests.get(f"{API_URL}/events")
    print_result("Public Events Access", r)
except Exception as e:
    print("Erro:", e)

# Test 3: Create event with SQL injection
print("\nTesting /events/create with SQL Injection payload")
payload = {
    "title": "Event'; DROP TABLE events;--",
    "date": "2025-12-31",
    "description": "Test SQL injection",
    "image_url": ""
}
try:
    r = requests.post(f"{API_URL}/events/create", json=payload, headers=headers)
    print_result("SQL Injection Attempt", r)
except Exception as e:
    print("Erro:", e)

# Test  4: XSS comment injection
print("\nTesting comment injection (XSS)")
payload = {
    "event_id": "nonexistent",
    "text": "<script>alert('xss')</script>",
    "author": "attacker"
}
try:
    r = requests.post(f"{API_URL}/events/nonexistent/comment", json=payload, headers=headers)
    print_result("XSS Comment Injection", r)
except Exception as e:
    print("Erro:", e)

# Test 5: Cancel event with fake ID
print("\nTesting event cancellation with fake ID")
try:
    r = requests.post(f"{API_URL}/events/fake-id/cancel", headers=headers)
    print_result("Cancel Nonexistent Event", r)
except Exception as e:
    print("Erro:", e)
