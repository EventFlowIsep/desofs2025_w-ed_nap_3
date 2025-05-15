# app/assign_role.py

import firebase_admin
from firebase_admin import credentials, auth
import argparse

cred = credentials.Certificate("app/firebase_key.json")
firebase_admin.initialize_app(cred)

def assign_role(email: str, role: str):
    try:
        user = auth.get_user_by_email(email)
        auth.set_custom_user_claims(user.uid, {"role": role})
        print(f"✅ Role '{role}' assigned to {email} (uid: {user.uid})")
    except Exception as e:
        print(f"❌ Failed to assign role: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assign role to Firebase user")
    parser.add_argument("--email", required=True, help="Email of the user")
    parser.add_argument("--role", required=True, help="Role to assign (e.g., admin, client, moderator)")
    args = parser.parse_args()
    
    assign_role(args.email, args.role)
