"""
Ticket Booking API demonstrating race conditions and distributed locks

Shows the problem of concurrent bookings and how Redis locks solve it
"""

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from contextlib import asynccontextmanager
import time

from database import get_db, init_db, seed_data, Event, Booking, reset_event
from locks import RedisLock
from redis_client import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and Redis on startup"""
    init_db()
    seed_data()
    
    if redis_client.ping():
        print("✅ Redis connected")
    else:
        print("⚠️  Redis not connected - locking disabled")
    
    yield


app = FastAPI(
    title="Ticket Booking API - Distributed Locks Demo",
    description="Shows race conditions and how Redis locks prevent them",
    version="1.0.0",
    lifespan=lifespan
)


class BookingRequest(BaseModel):
    user_name: str


class BookingResponse(BaseModel):
    success: bool
    message: str
    booking_id: int = None
    event: dict = None


class EventResponse(BaseModel):
    id: int
    name: str
    total_tickets: int
    available_tickets: int
    booked: int


# ==========================================
# WITHOUT LOCK - Shows the race condition
# ==========================================

@app.post("/book-no-lock/{event_id}", response_model=BookingResponse)
async def book_ticket_no_lock(event_id: int, request: BookingRequest, db: Session = Depends(get_db)):
    """
    Book a ticket WITHOUT distributed lock
    
    ⚠️  RACE CONDITION: Multiple requests can oversell tickets!
    
    Flow:
    1. Read available_tickets (e.g., 1)
    2. [Another request reads 1 at the same time]
    3. Check if available (both see 1 available)
    4. Create booking
    5. Decrement counter
    
    Result: Both succeed, event oversold!
    """
    print(f"🎫 [{request.user_name}] Attempting to book event {event_id} (NO LOCK)")
    
    # Get event
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Read current tickets BEFORE any delay
    available = event.available_tickets
    print(f"🔍 [{request.user_name}] Read from DB: {available} tickets available")
    
    # Simulate processing time - ALL requests sleep here with same value!
    time.sleep(0.5)
    
    # Check availability using the OLD value we read
    if available <= 0:
        print(f"❌ [{request.user_name}] No tickets available")
        return BookingResponse(
            success=False,
            message="No tickets available",
            event=event.to_dict()
        )
    
    print(f"✅ [{request.user_name}] Proceeding with booking (saw {available} tickets)...")
    
    # Create booking
    booking = Booking(
        event_id=event_id,
        user_name=request.user_name
    )
    db.add(booking)
    
    # Decrement available tickets (RACE HERE - multiple threads decrement!)
    event.available_tickets -= 1
    
    db.commit()
    db.refresh(booking)
    db.refresh(event)
    
    print(f"✅ [{request.user_name}] Booking successful! ID: {booking.id}")
    
    return BookingResponse(
        success=True,
        message="Booking successful",
        booking_id=booking.id,
        event=event.to_dict()
    )


# ==========================================
# WITH LOCK - Prevents race condition
# ==========================================

@app.post("/book-with-lock/{event_id}", response_model=BookingResponse)
async def book_ticket_with_lock(event_id: int, request: BookingRequest, db: Session = Depends(get_db)):
    """
    Book a ticket WITH distributed lock
    
    ✅ SAFE: Only one request can book at a time
    
    Flow:
    1. Acquire Redis lock for this event
    2. Read available_tickets
    3. Check if available
    4. Create booking
    5. Decrement counter
    6. Release lock
    
    Result: Only 1 succeeds, no overselling!
    """
    lock_key = f"lock:event:{event_id}"
    lock = RedisLock(redis_client)
    
    print(f"🎫 [{request.user_name}] Attempting to book event {event_id} (WITH LOCK)")
    
    # Try to acquire lock (wait up to 5 seconds)
    acquired = False
    start_time = time.time()
    while time.time() - start_time < 5:
        if lock.acquire(lock_key, timeout=10):
            acquired = True
            break
        time.sleep(0.05)
    
    if not acquired:
        print(f"⏳ [{request.user_name}] Could not acquire lock (timeout)")
        return BookingResponse(
            success=False,
            message="System busy, please try again"
        )
    
    try:
        # CRITICAL SECTION - Only one request at a time
        
        # Get event
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Read current tickets
        available = event.available_tickets
        print(f"🔍 [{request.user_name}] Read from DB (LOCKED): {available} tickets available")
        
        # Simulate processing
        time.sleep(0.5)
        
        if available <= 0:
            print(f"❌ [{request.user_name}] No tickets available")
            return BookingResponse(
                success=False,
                message="No tickets available",
                event=event.to_dict()
            )
        
        print(f"✅ [{request.user_name}] Proceeding with booking (LOCKED, saw {available} tickets)...")
        
        # Create booking
        booking = Booking(
            event_id=event_id,
            user_name=request.user_name
        )
        db.add(booking)
        
        # Decrement available tickets
        event.available_tickets -= 1
        
        db.commit()
        db.refresh(booking)
        db.refresh(event)
        
        print(f"✅ [{request.user_name}] Booking successful! ID: {booking.id}")
        
        return BookingResponse(
            success=True,
            message="Booking successful",
            booking_id=booking.id,
            event=event.to_dict()
        )
    
    finally:
        # Always release the lock
        lock.release(lock_key)


# ==========================================
# Utility Endpoints
# ==========================================

@app.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get event details to check results"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return event.to_dict()


@app.post("/reset/{event_id}")
async def reset_event_endpoint(event_id: int, db: Session = Depends(get_db)):
    """Reset an event to run tests again"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Delete all bookings
    db.query(Booking).filter(Booking.event_id == event_id).delete()
    
    # Reset available tickets
    event.available_tickets = event.total_tickets
    db.commit()
    db.refresh(event)
    
    return {
        "message": "Event reset successfully",
        "event": event.to_dict()
    }


@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected" if redis_client.ping() else "disconnected"
    }


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Ticket Booking API...")
    print("📚 API docs: http://localhost:8005/docs")
    uvicorn.run(app, host="0.0.0.0", port=8005)

