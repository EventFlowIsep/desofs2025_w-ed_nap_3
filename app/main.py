from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .firebase_auth import verify_firebase_token

app = FastAPI()

# Allow Streamlit frontend to access the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static HTML files like google_login.html at http://localhost:8000/auth/google_login.html
app.mount("/auth", StaticFiles(directory="public"), name="auth")


@app.get("/events")
def get_events(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")

    token = auth_header.split(" ")[1]
    user = verify_firebase_token(token)

    return [
        {"name": "Cybersecurity Conference", "date": "2025-07-12", "user": user["email"]},
        {"name": "Green Tech Expo", "date": "2025-08-05", "user": user["email"]},
    ]
