"""
Database setup with Products and Categories
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://shop_user:shop_pass@localhost:5432/shop_db"
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Category(Base):
    """Product category model"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    products = relationship("Product", back_populates="category")
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Product(Base):
    """Product model"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))
    featured = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = relationship("Category", back_populates="products")
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "featured": bool(self.featured),
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
    """Add sample products and categories"""
    db = SessionLocal()
    
    if db.query(Category).first():
        print("Database already has data, skipping seed")
        db.close()
        return
    
    print("🌱 Seeding categories and products...")
    
    # Create categories
    categories = [
        Category(name="Electronics", description="Electronic devices and gadgets"),
        Category(name="Books", description="Physical and digital books"),
        Category(name="Clothing", description="Fashion and apparel"),
        Category(name="Home", description="Home and kitchen items"),
        Category(name="Sports", description="Sports and outdoor equipment")
    ]
    
    db.add_all(categories)
    db.commit()
    
    # Refresh to get IDs
    for cat in categories:
        db.refresh(cat)
    
    # Create products
    products = [
        # Electronics
        Product(name="Laptop Pro", description="High-performance laptop", price=1299.99, category_id=categories[0].id, featured=1),
        Product(name="Wireless Mouse", description="Ergonomic wireless mouse", price=29.99, category_id=categories[0].id),
        Product(name="USB-C Hub", description="7-in-1 USB-C adapter", price=49.99, category_id=categories[0].id),
        
        # Books
        Product(name="Redis in Action", description="Learn Redis", price=39.99, category_id=categories[1].id, featured=1),
        Product(name="Python Cookbook", description="Python recipes", price=44.99, category_id=categories[1].id),
        
        # Clothing
        Product(name="Cotton T-Shirt", description="Comfortable cotton tee", price=19.99, category_id=categories[2].id),
        Product(name="Denim Jeans", description="Classic blue jeans", price=59.99, category_id=categories[2].id, featured=1),
        
        # Home
        Product(name="Coffee Maker", description="Programmable coffee maker", price=79.99, category_id=categories[3].id),
        Product(name="Blender", description="High-speed blender", price=89.99, category_id=categories[3].id),
        
        # Sports
        Product(name="Yoga Mat", description="Non-slip yoga mat", price=24.99, category_id=categories[4].id),
        Product(name="Running Shoes", description="Lightweight running shoes", price=99.99, category_id=categories[4].id, featured=1)
    ]
    
    db.add_all(products)
    db.commit()
    db.close()
    
    print(f"✅ Added {len(categories)} categories and {len(products)} products")


if __name__ == "__main__":
    init_db()
    seed_data()

