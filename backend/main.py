from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime
from config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A FastAPI backend for the Tauri desktop application",
    version=settings.VERSION
)

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class User(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

class CreateUserRequest(BaseModel):
    username: str
    email: str

class Message(BaseModel):
    message: str
    timestamp: datetime

# In-memory storage (replace with database in production)
users_db = []
messages_db = []

@app.get("/")
async def root():
    return {"message": "Welcome to Tauri Next.js FastAPI Backend!"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "service": "FastAPI Backend",
        "version": settings.VERSION
    }

@app.get("/api/users", response_model=List[User])
async def get_users():
    return users_db

@app.post("/api/users", response_model=User)
async def create_user(user_data: CreateUserRequest):
    user_id = len(users_db) + 1
    new_user = User(
        id=user_id,
        username=user_data.username,
        email=user_data.email,
        created_at=datetime.now()
    )
    users_db.append(new_user)
    return new_user

@app.get("/api/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    if user_id < 1 or user_id > len(users_db):
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id - 1]

@app.get("/api/messages", response_model=List[Message])
async def get_messages():
    return messages_db

@app.post("/api/messages", response_model=Message)
async def create_message(message_data: dict):
    new_message = Message(
        message=message_data.get("message", "Hello from FastAPI!"),
        timestamp=datetime.now()
    )
    messages_db.append(new_message)
    return new_message

@app.get("/api/stats")
async def get_stats():
    return {
        "total_users": len(users_db),
        "total_messages": len(messages_db),
        "uptime": "Running",
        "backend_version": settings.VERSION
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL
    ) 