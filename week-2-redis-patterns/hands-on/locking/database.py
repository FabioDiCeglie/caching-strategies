"""
Database setup with Events and Bookings
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://booking_user:booking_pass@localhost:5432/booking_db"
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Event(Base):
    """Event model with limited tickets"""
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    total_tickets = Column(Integer, nullable=False)
    available_tickets = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    bookings = relationship("Booking", back_populates="event")
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "total_tickets": self.total_tickets,
            "available_tickets": self.available_tickets,
            "booked": self.total_tickets - self.available_tickets,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Booking(Base):
    """Booking model"""
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey('events.id'))
    user_name = Column(String(100), nullable=False)
    booked_at = Column(DateTime, default=datetime.utcnow)
    
    event = relationship("Event", back_populates="bookings")
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "user_name": self.user_name,
            "booked_at": self.booked_at.isoformat() if self.booked_at else None
        }


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")


def seed_data():
    """Add sample events"""
    db = SessionLocal()
    
    if db.query(Event).first():
        print("Database already has data, skipping seed")
        db.close()
        return
    
    print("🌱 Seeding events...")
    
    events = [
        Event(name="Concert - Last Ticket", total_tickets=1, available_tickets=1),
        Event(name="Conference - 5 Tickets", total_tickets=5, available_tickets=5),
        Event(name="Workshop - 10 Tickets", total_tickets=10, available_tickets=10),
    ]
    
    db.add_all(events)
    db.commit()
    db.close()
    
    print(f"✅ Added {len(events)} events")


def reset_event(event_id: int):
    """Reset an event to full capacity"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if event:
        # Delete all bookings
        db.query(Booking).filter(Booking.event_id == event_id).delete()
        # Reset available tickets
        event.available_tickets = event.total_tickets
        db.commit()
        print(f"✅ Reset event {event_id}")
    
    db.close()


if __name__ == "__main__":
    init_db()
    seed_data()

