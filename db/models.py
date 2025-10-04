from .database import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.orm import relationship

class User(Base):
    """SQLAlchemy model for the User table."""
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String(100))
    verification_code = Column(String(100), nullable=True)
    code_expiry = Column(DateTime, nullable=True)
    is_verified = Column(Boolean, default=False)
    ingredients = relationship("Ingredients", back_populates="user")

class Ingredients(Base):
    """SQLAlchemy model for the Ingredient table."""
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    calories = Column(Float,default=0.0)
    protein = Column(Float,default=0.0)
    carbs = Column(Float,default=0.0)
    fat = Column(Float,default=0.0)
    fibers = Column(Float,default=0.0)
    sugar = Column(Float,default=0.0)
    saturated_fats = Column(Float,default=0.0)
    # New category column to classify ingredient (e.g., 'meat', 'vegetable', 'fruit').
    category = Column(String(50), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User",back_populates="ingredients")