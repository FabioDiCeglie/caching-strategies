"""
Database setup with SQLAlchemy and Postgres
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "postgresql://blog_user:blog_pass@localhost:5432/blog_db"

engine = create_engine(DATABASE_URL)

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
    """Add 500,000 sample posts for testing cache performance at scale"""
    db = SessionLocal()
    
    if db.query(Post).first():
        print("Database already has data, skipping seed")
        db.close()
        return
    
    print("🌱 Seeding 500,000 posts... (this will take a minute)")
    
    topics = [
        "Redis", "Caching", "Database", "Performance", "API Design",
        "Microservices", "Docker", "Python", "FastAPI", "SQL"
    ]
    
    authors = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"]
    
    batch_size = 10000
    total = 500000
    
    for batch_start in range(1, total + 1, batch_size):
        posts = []
        batch_end = min(batch_start + batch_size, total + 1)
        
        for i in range(batch_start, batch_end):
            topic = topics[i % len(topics)]
            author = authors[i % len(authors)]
            
            post = Post(
                title=f"{topic} Best Practices - Part {i}",
                content=f"This is a detailed article about {topic}. " * 20,
                author=author
            )
            posts.append(post)
        
        db.add_all(posts)
        db.commit()
        print(f"  ✓ Inserted {batch_end - 1:,} / {total:,} posts")
    
    db.close()
    print("✅ 500,000 posts added to database")


if __name__ == "__main__":
    init_db()
    seed_data()

