import requests
import json

# Dados do user
email = "testuser@gmail.com"      # O email que criaste no script anterior
password = "1q2w3e4r5t6y"        # A password que escolheste
api_key = "AIzaSyAHeLl9iaCku3LpBr0L-6Q3vMHQevgIw8c"  # Do teu .env

url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
payload = {
    "email": email,
    "password": password,
    "returnSecureToken": True
}
resp = requests.post(url, data=json.dumps(payload))
try:
    data = resp.json()
    print("\n==== Usa este valor como o teu ADMIN_CRED_DAST ou CLIENT_CRED_DAST ====\n")
    print(data["idToken"])  # <-- Este é o ID token JWT válido!
except Exception as e:
    print("Erro ao fazer login:", e)
    print("Resposta:", resp.text)
