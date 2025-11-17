"""
Mini-Project 3: Session Storage with Redis
Uses Redis Hashes to store structured session data.
"""

from fastapi import FastAPI, HTTPException, Cookie, Response
from fastapi.responses import JSONResponse
import redis
import uuid
import time
from typing import Optional
from pydantic import BaseModel

app = FastAPI(
    title="Redis Session Storage Demo",
    description="Session management using Redis Hashes",
    version="1.0.0"
)

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
    # Production: Add password='your_redis_password', ssl=True
)

SESSION_TTL = 1800  # 30 minutes


class LoginRequest(BaseModel):
    username: str
    password: str


def create_session(user_id: str, username: str) -> str:
    """Create a new session in Redis using Hashes"""
    session_id = str(uuid.uuid4())
    key = f"session:{session_id}"
    
    redis_client.hset(key, mapping={
        "user_id": user_id,
        "username": username,
        "created_at": str(time.time())
    })
    redis_client.expire(key, SESSION_TTL)
    
    return session_id


def get_session(session_id: str) -> Optional[dict]:
    """Get session data from Redis"""
    key = f"session:{session_id}"
    
    if not redis_client.exists(key):
        return None
    
    session_data = redis_client.hgetall(key)
    redis_client.expire(key, SESSION_TTL)
    
    return session_data


def delete_session(session_id: str):
    """Delete session from Redis"""
    key = f"session:{session_id}"
    redis_client.delete(key)


@app.post("/login")
async def login(credentials: LoginRequest, response: Response):
    """Login endpoint - creates a session"""
    if not credentials.username or not credentials.password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    
    if len(credentials.username) < 3 or len(credentials.username) > 50:
        raise HTTPException(status_code=400, detail="Username must be 3-50 characters")
    
    if len(credentials.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    user_id = f"user_{hash(credentials.username) % 10000}"
    session_id = create_session(user_id, credentials.username)
    
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=SESSION_TTL
    )
    
    return {
        "message": "Login successful",
        "username": credentials.username,
        "session_id": session_id
    }


@app.get("/profile")
async def get_profile(session_id: Optional[str] = Cookie(None)):
    """Protected route - requires valid session"""
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    
    return {
        "user_id": session["user_id"],
        "username": session["username"],
    }


@app.post("/logout")
async def logout(response: Response, session_id: Optional[str] = Cookie(None)):
    """Logout - destroys session"""
    if session_id:
        delete_session(session_id)
    
    response.delete_cookie(
        key="session_id",
        httponly=True,
        secure=False,  # Set to True in production
        samesite="lax"
    )
    
    return {"message": "Logged out successfully"}


@app.get("/health")
async def health_check():
    """Health check"""
    try:
        redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except redis.ConnectionError:
        return {"status": "unhealthy", "redis": "disconnected"}


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Session Storage Demo...")
    print("📚 API docs: http://localhost:8002/docs")
    uvicorn.run(app, host="0.0.0.0", port=8002)

