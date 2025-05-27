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
import logging
from firebase_admin import auth as firebase_auth
from firebase_admin.exceptions import FirebaseError
from app.logging_db import save_log
import hashlib
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.requests import Request

# Logging config
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("eventflow")

# Setup env var for Firebase credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "app/firebase_key.json"

# Firebase init
if not firebase_admin._apps:
    cred = credentials.Certificate("app/firebase_key.json")
    initialize_app(cred)

db = firestore.Client()

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

# Middleware to log every request with Firebase user email
async def extract_user_from_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return "anonymous"
    id_token = auth_header.split(" ")[1]
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token.get("email", "unknown user")
    except FirebaseError as e:
        logger.warning(f"Invalid Firebase token: {e}")
        return "invalid_token"

@app.middleware("http")
async def log_requests(request: Request, call_next):
    auth_header = request.headers.get("Authorization")
    user = "anonymous"
    token_hash = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        token_hash = hash_token(token)
        try:
            decoded_token = firebase_auth.verify_id_token(token)
            user = decoded_token.get("email", "unknown user")
        except FirebaseError:
            user = "invalid_token"

    logger.info(f"User: {user} - Token Hash: {token_hash} - Started request {request.method} {request.url}")

    try:
        response = await call_next(request)

        save_log(user_email=user, method=request.method, path=str(request.url), status_code=response.status_code)
        logger.info(f"User: {user} - Token Hash: {token_hash} - Completed request {request.method} {request.url} - Status: {response.status_code}")
        return response
    except Exception as e:
        save_log(user_email=user, method=request.method, path=str(request.url), status_code=500, message=str(e))
        logger.error(f"Exception on request: {e}")
        raise

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    user_email = await extract_user_from_token(request)
    logger.error(f"Input validation failure from user {user_email} on {request.method} {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

@app.get("/auth/google_login.html")
def serve_google_login():
    return FileResponse("streamlit_app/auth/google_login.html", media_type="text/html")

def verify_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning(f"Missing or invalid token on {request.method} {request.url}")
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
        logger.warning(f"Invalid token on {request.method} {request.url}")
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/logs")
def get_logs(req: Request, user=Depends(verify_token)):
    if user["role"] != "Admin":
        logger.warning(f"Access denied for user {user['email']} on {req.method} {req.url} - Forbidden")
        raise HTTPException(status_code=403, detail="Forbidden")
    
    import sqlite3
    conn = sqlite3.connect("eventflow_logs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, user_email, method, path, status_code, message FROM logs ORDER BY timestamp DESC LIMIT 100")
    rows = cursor.fetchall()
    conn.close()

    logs = [
        {
            "timestamp": row[0],
            "user_email": row[1],
            "method": row[2],
            "path": row[3],
            "status_code": row[4],
            "message": row[5],
        } for row in rows
    ]
    return JSONResponse(content={"logs": logs})


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
        logger.warning(f"Access denied for user {user['email']} on {req.method} {req.url} - Forbidden")
        raise HTTPException(status_code=403, detail="Forbidden")
    
    categories_ref = db.collection("categories")
    categories_docs = categories_ref.stream()
    categories = []
    for doc in categories_docs:
        categories.append(doc.to_dict())

    if not categories:
        raise HTTPException(status_code=400, detail="No categories found. Please create categories first.")
    try:
        body = await req.json()
    except Exception as e:
        user_email = user.get("email", "anonymous") if user else "anonymous"
        logger.error(f"Deserialization failure from user {user_email} on {req.method} {req.url}: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    title = body.get("title")
    date = body.get("date")
    description = body.get("description", "")
    image_url = body.get("image_url", "")
    category = body.get("category")

    if category not in [cat["name"] for cat in categories]:
        raise HTTPException(status_code=400, detail="Invalid category.")
    if not title or not date:
        raise HTTPException(status_code=400, detail="Missing title or date")

    event = {
        "title": title,
        "date": date,
        "description": description,
        "image_url": image_url,
        "category": body.get("category", "Uncategorized"),
        "created_by": user["email"],
        "cancelled": False,
        "comments": [],
        "registrations": []
    }
    db.collection("events").add(event)
    return {"message": "Event created successfully."}

@app.post("/events/{event_id}/cancel")
def cancel_event(req: Request, event_id: str, user=Depends(verify_token)):
    if user["role"] not in ["Admin", "Event_manager", "Moderator"]:
        logger.warning(f"Access denied for user {user['email']} on {req.method} {req.url} - Forbidden")
        raise HTTPException(status_code=403, detail="Forbidden")
    doc_ref = db.collection("events").document(event_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="Event not found")

    doc_ref.update({"cancelled": True})
    return {"message": f"Event {event_id} cancelled."}

@app.post("/events/{event_id}/comment")
async def post_comment(event_id: str, req: Request, user=Depends(verify_token)):
    try:
        body = await req.json()
    except:
        user_email = user.get("email", "anonymous") if user else "anonymous"
        logger.error(f"Deserialization failure from user {user_email} on {req.method} {req.url}: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
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

class EventUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    date: Optional[str]
    image_url: Optional[str]
    category: Optional[str]

@app.put("/events/{event_id}")
def update_event(req: Request, event_id: str, update: EventUpdate, user=Depends(verify_token)):
    if user.get("role") not in ["Admin", "Event_manager", "Moderator"]:
        logger.warning(f"Access denied for user {user['email']} on {req.method} {req.url} - Forbidden")
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
        except Exception as e:
            logger.error(f"Error processing event {doc.id}: {e}")

    return filtered

@app.post("/events/{event_id}/register")
def register_for_event(event_id: str, user=Depends(verify_token)):
    doc_ref = db.collection("events").document(event_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="Event not found")

    registration = {
        "uid": user["uid"],
        "email": user["email"],
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    doc_ref.update({"registrations": firestore.ArrayUnion([registration])})
    return {"msg": "You have been registered for the event."}

class Category(BaseModel):
    name: str
    description: str = ""

@app.post("/categories")
def create_category(req: Request, category: Category, user=Depends(verify_token)):
    if user["role"] != "Admin":
        logger.warning(f"Access denied for user {user['email']} on {req.method} {req.url} - Forbidden")
        raise HTTPException(status_code=403, detail="Only Admin can create categories.")

    cat_data = category.dict()
    db.collection("categories").add(cat_data)
    return {"msg": "Category created successfully."}

@app.get("/categories")
def get_categories(req: Request,user=Depends(verify_token)):
    if user["role"] not in ["Admin", "Event_manager"]:
        logger.warning(f"Access denied for user {user['email']} on {req.method} {req.url} - Forbidden")
        raise HTTPException(status_code=403, detail="Only Admin or Event Manager can view categories.")

    categories_ref = db.collection("categories")
    docs = categories_ref.stream()
    categories = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        categories.append(data)
    return categories

class CommentToDelete(BaseModel):
    author: str
    timestamp: str
    text: str

@app.delete("/events/{event_id}/comment")
def delete_comment(req: Request,event_id: str, comment: CommentToDelete, user=Depends(verify_token)):
    event_ref = db.collection("events").document(event_id)
    event_doc = event_ref.get()
    if not event_doc.exists:
        raise HTTPException(status_code=404, detail="Event not found")

    event_data = event_doc.to_dict()
    role = user.get("role")

    if role not in ["Admin", "Moderator"]:
        if role == "Event_manager" and event_data.get("created_by") != user["email"]:
            logger.warning(f"Access denied for user {user['email']} on {req.method} {req.url} - Forbidden")
            raise HTTPException(status_code=403, detail="You can only delete comments on events you created.")
        elif role != "Event_manager":
            logger.warning(f"Access denied for user {user['email']} on {req.method} {req.url} - Forbidden")
            raise HTTPException(status_code=403, detail="Permission denied.")

    comment_dict = comment.dict()
    existing_comments = event_data.get("comments", [])
    if comment_dict not in existing_comments:
        raise HTTPException(status_code=404, detail="Comment not found")

    updated_comments = [c for c in existing_comments if c != comment_dict]
    event_ref.update({"comments": updated_comments})
    return {"msg": "Comment deleted successfully."}
