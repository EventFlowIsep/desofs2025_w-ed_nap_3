from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, auth, initialize_app
from google.cloud import firestore
import firebase_admin
import os
import datetime
from fastapi.responses import FileResponse


# Setup environment variable to load credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "app/firebase_key.json"

# Initialize Firebase Admin
if not firebase_admin._apps:
    cred = credentials.Certificate("app/firebase_key.json")
    initialize_app(cred)

db = firestore.Client()

app = FastAPI()

@app.get("/auth/google_login.html")
def serve_google_login():
    return FileResponse("streamlit_app/auth/google_login.html", media_type="text/html")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware to validate token and role
def verify_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = auth_header.split(" ")[1]
    try:
        decoded = auth.verify_id_token(token)
        return {
            "uid": decoded.get("uid"),
            "email": decoded.get("email"),
            "role": decoded.get("role", "client")
        }
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/events")
def get_events(user=Depends(verify_token)):
    events_ref = db.collection("events")
    docs = events_ref.stream()
    events = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        events.append(data)
    return events

@app.post("/events/create")
async def create_event(req: Request, user=Depends(verify_token)):
    if user["role"] not in ["admin", "event_manager"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    body = await req.json()
    title = body.get("title")
    date = body.get("date")
    description = body.get("description", "")
    image_url = body.get("image_url", "")
    if not title or not date:
        raise HTTPException(status_code=400, detail="Missing title or date")

    event = {
        "title": title,
        "date": date,
        "description": description,
        "image_url": image_url,
        "created_by": user["email"],
        "cancelled": False,
        "comments": []
    }
    db.collection("events").add(event)
    return {"message": "Event created successfully."}

@app.post("/events/{event_id}/cancel")
def cancel_event(event_id: str, user=Depends(verify_token)):
    if user["role"] not in ["admin", "event_manager"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    doc_ref = db.collection("events").document(event_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="Event not found")

    doc_ref.update({"cancelled": True})
    return {"message": f"Event {event_id} cancelled."}

@app.post("/events/{event_id}/comment")
async def post_comment(event_id: str, req: Request, user=Depends(verify_token)):
    body = await req.json()
    text = body.get("text")
    author = body.get("author", "guest")

    if not text:
        raise HTTPException(status_code=400, detail="Comment text is required")

    doc_ref = db.collection("events").document(event_id)
    event_doc = doc_ref.get()
    if not event_doc.exists:
        raise HTTPException(status_code=404, detail="Event not found")

    comment = {
        "author": author,
        "text": text,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    doc_ref.update({"comments": firestore.ArrayUnion([comment])})
    return {"message": "Comment added successfully"}

@app.get("/verify-token")
def verify(token: str = Depends(verify_token)):
    return {"email": token["email"], "role": token["role"]}
