import requests

def test_verify_token():
    print("Testing /verify-token endpoint...")
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get("http://localhost:8000/verify-token", headers=headers)
    assert response.status_code == 401 or response.status_code == 403

def test_sql_injection():
    print("Testing for SQL injection on comment...")
    malicious_payload = {
        "content": "' OR 1=1 --",
    }
    response = requests.post("http://localhost:8000/events/1/comment", json=malicious_payload)
    print("Response:", response.status_code, response.text)

if __name__ == "__main__":
    test_verify_token()
    test_sql_injection()
