import firebase_admin
from firebase_admin import credentials, auth

# Inicializar Firebase Admin SDK
cred = credentials.Certificate("app/firebase_key.json")
firebase_admin.initialize_app(cred)

def set_user_role(uid: str, role: str):
    # ⚠️ Este método sobrescreve os claims existentes
    auth.set_custom_user_claims(uid, { "role": role })
    print(f"✅ Set role '{role}' for user {uid}")

# Exemplo de uso
if __name__ == "__main__":
    uid = input("Enter Firebase UID: ")
    role = input("Enter role (admin, event_manager, client): ")
    set_user_role(uid, role)
