from fastapi import FastAPI, Request, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, auth, initialize_app
from google.cloud import firestore
import firebase_admin
import os
import datetime
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

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
            "role": decoded.get("role", "Client")
        }
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/debug-token")
def debug_token(user=Depends(verify_token)):
    return user


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
    if user["role"] not in ["Admin", "Event_manager"]:
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
    if user["role"] not in ["Admin", "Event_manager", "Moderator"]:
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

# Edit event
class EventUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    date: Optional[str]  # Expecting YYYY-MM-DD
    image_url: Optional[str]

@app.put("/events/{event_id}")
def update_event(event_id: str, update: EventUpdate, user=Depends(verify_token)):
    if user.get("role") not in ["Admin", "Event_manager", "Moderator"]:
        raise HTTPException(status_code=403, detail="You are not allowed to edit events.")

    event_ref = db.collection("events").document(event_id)
    event_doc = event_ref.get()
    if not event_doc.exists:
        raise HTTPException(status_code=404, detail="Event not found")

    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if "date" in update_data:
        try:
            datetime.datetime.strptime(update_data["date"], "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    event_ref.update(update_data)
    return {"msg": "Event updated successfully."}

# Filter events
@app.get("/events/filter")
def filter_events_by_date(start: str = Query(...), end: str = Query(...)):
    try:
        start_date = datetime.datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be in YYYY-MM-DD format")

    docs = db.collection("events").stream()
    filtered = []
    for doc in docs:
        data = doc.to_dict()
        event_date_str = data.get("date")
        if not event_date_str:
            continue
        try:
            event_date = datetime.datetime.strptime(event_date_str, "%Y-%m-%d")
            if start_date <= event_date <= end_date:
                data["id"] = doc.id
                filtered.append(data)
        except:
            continue

    return filtered
