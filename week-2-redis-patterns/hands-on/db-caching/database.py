"""
Database setup with SQLAlchemy and SQLite
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./blog.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Post(Base):
    """Blog post model"""
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "author": self.author,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
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
    """Add sample posts for testing"""
    db = SessionLocal()
    
    if db.query(Post).first():
        print("Database already has data, skipping seed")
        db.close()
        return
    
    sample_posts = [
        Post(
            title="Introduction to Redis",
            content="Redis is an in-memory data structure store...",
            author="Alice"
        ),
        Post(
            title="Caching Strategies",
            content="There are several caching patterns: cache-aside, write-through...",
            author="Bob"
        ),
        Post(
            title="Database Performance Tips",
            content="Optimizing database queries is crucial for performance...",
            author="Alice"
        )
    ]
    
    db.add_all(sample_posts)
    db.commit()
    db.close()
    print("✅ Sample data added")


if __name__ == "__main__":
    init_db()
    seed_data()

