from fastapi import FastAPI, Request, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, auth, initialize_app
from google.cloud import firestore
import firebase_admin
import os
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
from fastapi.templating import Jinja2Templates
from fastapi import Request
from dotenv import load_dotenv
import re
import zxcvbn
import requests
import html
import json
from datetime import datetime, timedelta
import subprocess
import socket
from app.logging_db import SQLiteLogger
from fastapi import Request

SQLiteLogger()

load_dotenv()
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
# Logging config
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("eventflow")

# Setup env var for Firebase credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "app/firebase_key.json"

if not firebase_admin._apps:
    cred = credentials.Certificate("app/firebase_key.json")
    initialize_app(cred)

db = firestore.Client()

app = FastAPI()
in_memory_cache = {}
rate_limit_cache = {}

RATE_LIMIT = 100 

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DANGEROUS_PATTERNS = [
    r"<\s*script.*?>.*?<\s*/\s*script\s*>",
    r"on\w+\s*=",
    r"javascript:",
    r"\{\{.*?\}\}",
    r"<[^>]*>"
]

def sanitize_input(data: dict):
    for key, value in data.items():
        if isinstance(value, str):
            for pattern in DANGEROUS_PATTERNS:
                if re.search(pattern, value, flags=re.IGNORECASE | re.DOTALL):
                    raise HTTPException(status_code=400, detail=f"Insecure input detected in field '{key}'")
        elif isinstance(value, dict):
            sanitize_input(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    sanitize_input(item)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def sanitize_for_log(text: str) -> str:
    if not text:
        return ""
    return html.escape(text)

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

@app.get("/test-firestore-connection")
def test_firestore_connection():
    try:
        # Tente acessar um pequeno pedaço da coleção de eventos
        docs = db.collection("events").limit(1).stream()
        events = [doc.to_dict() for doc in docs]
        return {"message": "Firestore connection successful", "events": events}
    except Exception as e:
        logger.error(f"Error connecting to Firestore: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect to Firestore.")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    auth_header = request.headers.get("Authorization")
    user = "anonymous"
    token_hash = None
    e = None
    ip = request.client.host

    now = datetime.utcnow()
    entry = rate_limit_cache.get(ip)

    if entry and entry["count"] >= RATE_LIMIT and entry["reset_time"] > now:
        raise HTTPException(status_code=429, detail="Too many requests")
    elif not entry or entry["reset_time"] <= now:
        rate_limit_cache[ip] = {"count": 1, "reset_time": now + timedelta(minutes=1)}
    else:
        entry["count"] += 1

    
    if "events" in request.url.path:
        events_key = f"rate_limit:{ip}:events"
        now = datetime.utcnow()
        entry = in_memory_cache.get(events_key)
        if not entry or entry["reset_time"] <= now:
            in_memory_cache[events_key] = {"count": 1, "reset_time": now + timedelta(minutes=1)}
        elif entry["count"] >= RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Too many requests")
        else:
            entry["count"] += 1



    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        token_hash = hash_token(token)
        try:
            decoded_token = firebase_auth.verify_id_token(token)
            user = decoded_token.get("email", "unknown user")
        except FirebaseError:
            user = "invalid_token"

    user = await extract_user_from_token(request)
    token_hash = hash_token(request.headers.get("Authorization", "")) if user != "anonymous" else None
    client_host = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    safe_url = sanitize_for_log(str(request.url))
    safe_method = sanitize_for_log(request.method)
    
    try:
        logger.info(f"User: {user} - Token Hash: {token_hash} - Started request {safe_method} {safe_url}")
        response = await call_next(request)
        
        logger.info(f"User: {user} - Token Hash: {token_hash} - Completed request {safe_method} {safe_url} - Status: {response.status_code}")
        
        event_type = "request_end"
        logger.info(f"[{event_type}] User: {user} - Method: {safe_method} - Path: {safe_url} - Status: {response.status_code}")
        
        timestamp = datetime.utcnow().isoformat()
        save_log(user_email=user, method=request.method, path=str(request.url), status_code=response.status_code, ip=client_host, user_agent=user_agent)
        return response
    except Exception as e:
        event_type = "exception"
        safe_error = sanitize_for_log(str(e))
        
        logger.error(f"Exception on request from user {user} - Error: {safe_error}")
        logger.error(f"[{event_type}] User: {user} - Method: {safe_method} - Path: {safe_url} - Error: {safe_error}")
        
        timestamp = datetime.utcnow().isoformat()
        save_log(user_email=user, method=request.method, path=str(request.url), status_code=500, message=safe_error, ip=client_host, user_agent=user_agent)
        
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

templates = Jinja2Templates(directory="streamlit_app/auth")

@app.get("/auth/google_login.html")
async def serve_google_login(request: Request):
    return templates.TemplateResponse("google_login.html", {"request": request, "firebase_api_key": os.getenv("FIREBASE_API_KEY")}, media_type="text/html")

def verify_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning(f"Missing or invalid token on {request.method} {request.url}")
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = auth_header.split(" ")[1]
    ip = request.client.host
    try:
        decoded = auth.verify_id_token(token)
        return {
            "uid": decoded.get("uid"),
            "email": decoded.get("email"),
            "role": decoded.get("role", "Client"),
            "ip": ip
        }
    except:
        logger.warning(f"Invalid token on {request.method} {request.url}")
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/logs")
def get_logs(req: Request, user=Depends(verify_token)):
    if user["role"] != "Admin":
        logger.warning(f"Access denied for user {user['email']} on {req.method} {req.url} - Forbidden")
        raise HTTPException(status_code=403, detail="Forbidden")
    try:    
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

    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        raise HTTPException(status_code=500, detail="Error fetching logs: {str(e)}")

@app.get("/debug-token")
def debug_token(user=Depends(verify_token)):
    return user

@app.get("/events")
def get_events(user=Depends(verify_token), page: int = Query(1, ge=1), per_page: int = Query(10, ge=1)):
    try:
        cache_key = f"events_page_{page}_per_{per_page}"
        cached = in_memory_cache.get(cache_key)
        
        if cached and cached["expires_at"] > datetime.utcnow():
            return {"events": cached["data"]}

        
        events_ref = db.collection("events").offset((page - 1) * per_page).limit(per_page)
        docs = events_ref.stream()
        events = []
        
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            events.append(data)
        
        in_memory_cache[cache_key] = {
            "data": events,
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        }

        return {"events": events}
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching events: {str(e)}")

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
        sanitize_input(body)
    except Exception as e:
        user_email = user.get("email", "anonymous") if user else "anonymous"
        logger.error(f"Deserialization failure from user {user_email} on {req.method} {req.url}: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    title = html.escape(body.get("title", ""))
    date = body.get("date")
    description = html.escape(body.get("description", ""))
    image_url = html.escape(body.get("image_url", ""))
    category = html.escape(body.get("category", ""))

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
    logger.info(f"User {user['email']} CREATED event '{title}' in category '{category}'")
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
    logger.info(f"User {user['email']} CANCELLED event {event_id}")
    return {"message": f"Event {event_id} cancelled."}

@app.post("/events/{event_id}/comment")
async def post_comment(event_id: str, req: Request, user=Depends(verify_token)):
    try:
        body = await req.json()
        sanitize_input(body)
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
        "author": html.escape(author),
        "text": html.escape(text),
        "timestamp": datetime.utcnow().isoformat()
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
    
    sanitize_input(update.dict())
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
        "timestamp": datetime.utcnow().isoformat()
    }

    doc_ref.update({"registrations": firestore.ArrayUnion([registration])})
    return {"msg": "You have been registered for the event."}

class Category(BaseModel):
    name: str
    description: str = ""

@app.post("/categories")
def create_category(req: Request, category: Category, user=Depends(verify_token)):
    sanitize_input(category.dict())
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

@app.get("/events/{event_id}/comments")
def get_comments(event_id: str, user=Depends(verify_token), page: int = Query(1, ge=1), per_page: int = Query(10, ge=1)):
    cache_key = f"comments_{event_id}_page_{page}_per_{per_page}"

    cached = in_memory_cache.get(cache_key)
    
    if cached and cached["expires_at"] > datetime.utcnow():
        return {"comments": cached["data"]}

    
    event_ref = db.collection("events").document(event_id)
    event_doc = event_ref.get()
    
    if not event_doc.exists:
        raise HTTPException(status_code=404, detail="Event not found")

    event_data = event_doc.to_dict()
    comments = event_data.get("comments", [])

    start = (page - 1) * per_page
    end = start + per_page
    paginated_comments = comments[start:end]
    
    in_memory_cache[cache_key] = {
        "data": paginated_comments,
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    }

    return {"comments": paginated_comments}

@app.delete("/events/{event_id}/comment")
def delete_comment(req: Request,event_id: str, comment: CommentToDelete, user=Depends(verify_token)):
    cache_key = f"comments_{event_id}"
    if cache_key in in_memory_cache:
        comments = in_memory_cache[cache_key]["data"]
    else:
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

    sanitize_input(comment_dict)
    comment_dict = comment.dict()
    existing_comments = event_data.get("comments", [])
    event_ref = db.collection("events").document(event_id)
    event_doc = event_ref.get()
    event_data = event_doc.to_dict()
    if comment_dict not in existing_comments:
        raise HTTPException(status_code=404, detail="Comment not found")

    keys_to_delete = [k for k in in_memory_cache if k.startswith(f"comments_{event_id}_")]
    for k in keys_to_delete:
        in_memory_cache.pop(k, None)
    updated_comments = [c for c in existing_comments if c != comment_dict]
    event_ref.update({"comments": updated_comments})
    in_memory_cache.pop(cache_key, None)
    return {"msg": "Comment deleted successfully."}

@app.get("/user/email")
async def get_email(request: Request, user=Depends(verify_token)):
    return {"email": user['email']}

class ResetPasswordRequest(BaseModel):
    email: str

@app.post("/user/reset_password")
async def reset_password(request: ResetPasswordRequest):
    try:
        firebase_auth.send_password_reset_email(request.email)
        return {"message": "Password reset email sent."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")
    
def validate_password(password: str):
    # Remove consecutive spaces and trim the password
    password = re.sub(r'\s+', ' ', password.strip())
    
    # Validate length
    if len(password) < 12:
        raise HTTPException(status_code=400, detail="Password must be at least 12 characters.")
    
    if len(password) > 128:
        raise HTTPException(status_code=400, detail="Password must not exceed 128 characters.")
    
    if not password.strip():
        raise HTTPException(status_code=400, detail="Password cannot be empty or only spaces.")
    
    return password

def check_password_strength(password: str):
    strength = zxcvbn.password_strength(password)
    if strength['score'] < 3:  # If the score is too low, we can consider it weak
        raise HTTPException(status_code=400, detail="Password is too weak. Consider using a stronger password.")
    
def check_breached_password(password: str):
    hashed_password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix, suffix = hashed_password[:5], hashed_password[5:]
    
    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    response = requests.get(url)
    
    if response.status_code == 200:
        hashes = response.text.splitlines()
        for hash in hashes:
            if hash.startswith(suffix):
                raise HTTPException(status_code=400, detail="This password has been breached. Please choose another one.")
    else:
        raise HTTPException(status_code=500, detail="Error checking password breach status.")
