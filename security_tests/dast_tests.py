import os
from dotenv import load_dotenv
import requests

# Carregar variáveis do .env
load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
ADMIN_TOKEN = os.getenv("ADMIN_CRED_DAST", "")
CLIENT_TOKEN = os.getenv("CLIENT_CRED_DAST", "")

print(f"ADMIN TOKEN SHORT: {ADMIN_TOKEN[:30]}...")  # Confirma que foi lido
print(f"CLIENT TOKEN SHORT: {CLIENT_TOKEN[:30]}...")

headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"} if ADMIN_TOKEN else {}
headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"} if CLIENT_TOKEN else {}

def print_result(name, response):
    print(f"\n== {name} ==")
    print(f"Status code: {response.status_code}")
    try:
        print("Response JSON:", response.json())
    except Exception:
        print("Response Text:", response.text)

# 1. Test Google login HTML (no auth)
print("Testing GET /auth/google_login.html")
r = requests.get(f"{BASE_URL}/auth/google_login.html")
print_result("Google Login HTML", r)

# 2. Test debug-token (admin)
print("\nTesting GET /debug-token (admin)")
r = requests.get(f"{BASE_URL}/debug-token", headers=headers_admin)
print_result("Debug Token (admin)", r)

# 3. Test verify-token (client)
print("\nTesting GET /verify-token (client)")
r = requests.get(f"{BASE_URL}/verify-token", headers=headers_client)
print_result("Verify Token (client)", r)

# 4. Test GET /events (client)
print("\nTesting GET /events (client)")
r = requests.get(f"{BASE_URL}/events", headers=headers_client)
print_result("List Events (client)", r)

# 5. Test POST /events/create (admin) (needs existing category!)
print("\nTesting POST /events/create (admin)")
payload = {
    "title": "<script>alert('xss')</script>",  # XSS test
    "date": "2099-12-31",
    "description": "A test event for DAST.",
    "image_url": "http://invalid-url.com/image.jpg",
    "category": "Uncategorized"
}
r = requests.post(f"{BASE_URL}/events/create", json=payload, headers=headers_admin)
print_result("Create Event (with XSS, admin)", r)

# Pega um event_id para usar nos endpoints seguintes
print("\nGetting events to extract one event_id...")
resp = requests.get(f"{BASE_URL}/events", headers=headers_admin)
event_id = None
try:
    events = resp.json()
    if isinstance(events, list) and events:
        event_id = events[0].get("id")
        print(f"Sample event_id: {event_id}")
except Exception:
    pass
if not event_id:
    print("No event_id available for further event-based tests!")

# 6. Test POST /events/{event_id}/cancel (admin)
if event_id:
    print("\nTesting POST /events/{event_id}/cancel (admin)")
    r = requests.post(f"{BASE_URL}/events/{event_id}/cancel", headers=headers_admin)
    print_result("Cancel Event (admin)", r)

# 7. Test POST /events/{event_id}/comment (client)
if event_id:
    print("\nTesting POST /events/{event_id}/comment (client)")
    comment_payload = {
        "text": "' OR '1'='1",      # SQLi test in comment
        "author": "<img src=x onerror=alert(1)>"
    }
    r = requests.post(f"{BASE_URL}/events/{event_id}/comment", json=comment_payload, headers=headers_client)
    print_result("Comment on Event (with SQLi/XSS, client)", r)

# 8. Test PUT /events/{event_id} (admin)
if event_id:
    print("\nTesting PUT /events/{event_id} (admin)")
    update_payload = {
        "title": "Updated'; DROP TABLE events;--",
        "description": "Updated description.",
        "date": "2099-11-30",
        "image_url": "",
        "category": "Uncategorized"
    }
    r = requests.put(f"{BASE_URL}/events/{event_id}", json=update_payload, headers=headers_admin)
    print_result("Update Event (SQLi in title, admin)", r)

# 9. Test GET /events/filter (client)
print("\nTesting GET /events/filter (client)")
params = {
    "start": "2000-01-01",
    "end": "2100-01-01"
}
r = requests.get(f"{BASE_URL}/events/filter", params=params, headers=headers_client)
print_result("Filter Events (client)", r)

# 10. Test POST /events/{event_id}/register (client)
if event_id:
    print("\nTesting POST /events/{event_id}/register (client)")
    r = requests.post(f"{BASE_URL}/events/{event_id}/register", headers=headers_client)
    print_result("Register for Event (client)", r)

# 11. Test DELETE /events/{event_id}/comment (admin)
if event_id:
    print("\nFetching event to find a comment to delete...")
    resp = requests.get(f"{BASE_URL}/events", headers=headers_admin)
    comment_to_delete = None
    try:
        events = resp.json()
        for evt in events:
            if evt.get("id") == event_id and evt.get("comments"):
                comment = evt["comments"][0]
                comment_to_delete = {
                    "author": comment.get("author", ""),
                    "timestamp": comment.get("timestamp", ""),
                    "text": comment.get("text", "")
                }
                break
    except Exception:
        pass

    if comment_to_delete:
        print("\nTesting DELETE /events/{event_id}/comment (admin)")
        r = requests.delete(f"{BASE_URL}/events/{event_id}/comment", json=comment_to_delete, headers=headers_admin)
        print_result("Delete Comment (admin)", r)
    else:
        print("No comment found to test DELETE /events/{event_id}/comment.")

# 12. Test POST /categories (admin)
print("\nTesting POST /categories (admin)")
cat_payload = {
    "name": "Test Category'; DROP TABLE categories;--",  # SQLi test
    "description": "DAST test category"
}
r = requests.post(f"{BASE_URL}/categories", json=cat_payload, headers=headers_admin)
print_result("Create Category (with SQLi, admin)", r)

# 13. Test GET /categories (admin)
print("\nTesting GET /categories (admin)")
r = requests.get(f"{BASE_URL}/categories", headers=headers_admin)
print_result("List Categories (admin)", r)

print("\n✅ DAST tests completed.")
