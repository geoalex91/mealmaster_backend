from .database import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, JSON, event
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

class ReprMixin:
    __repr_fields__ = ("id",)

    def __repr__(self):
        parts = []
        for field in getattr(self, "__repr_fields__", []):
            # Use getattr defensively (SQLAlchemy may lazy-load)
            value = getattr(self, field, None)
            parts.append(f"{field}={value!r}")
        return f"<{self.__class__.__name__} {' '.join(parts)}>"

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
    recipes = relationship("Recipes", back_populates="user")
    user_stats = relationship("UserStats", back_populates="user", uselist=False,cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshTokens", back_populates="user", cascade="all, delete-orphan")
    measurements_entries = relationship("UserMeasurementsEntry", back_populates="user", cascade="all, delete-orphan")


class UserStats(Base):
    """SQLAlchemy model for the UserStats table."""
    __tablename__ = "user_stats"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, unique=True)
    profile_photo_url = Column(String, nullable=True)
    name = Column(String, nullable=True)
    height = Column(Integer, default=0)  # in cm
    birthdate = Column(DateTime, nullable=True)
    gender = Column(String(10), nullable=True)
    activity_level = Column(String(20), nullable=True)
    user = relationship("User", back_populates="user_stats")

    @property
    def email(self) -> str:
        return self.user.email if self.user else None

    @property
    def username(self) -> str:
        return self.user.username if self.user else None

class UserMeasurementsEntry(Base):
    """SQLAlchemy model for the UserMeasurementsEntry table."""
    __tablename__ = "user_measurements"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    weight = Column(Float, nullable=True, default=0.0)  # in kg
    arm_circumference_r = Column(Float, nullable=True, default=0.0)  # in cm
    arm_circumference_l = Column(Float, nullable=True, default=0.0)  # in cm
    waist_circumference = Column(Float, nullable=True, default=0.0)  # in cm
    hip_circumference = Column(Float, nullable=True, default=0.0)  # in cm
    chest_circumference = Column(Float, nullable=False, default=0.0)  # in cm
    quad_circumference_r = Column(Float, nullable=False, default=0.0)  # in cm
    quad_circumference_l = Column(Float, nullable=False, default=0.0)  # in cm
    shoulder_circumference = Column(Float, nullable=False, default=0.0)  # in cm
    fat_percentage = Column(Integer, nullable=True, default=0)  # in %
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc))
    user = relationship("User", back_populates="measurements_entries")

@event.listens_for(UserStats, "before_insert")
def set_userstats_name_default(mapper, connection, target):
    # Initialize name from user username on first insert when name not explicitly set.
    if not target.name and target.user is not None:
        target.name = target.user.username


class RefreshTokens(Base):
    """SQLAlchemy model for the RefreshTokens table."""
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc))
    user = relationship("User", back_populates="refresh_tokens")

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
    recipe_ingredients = relationship("RecipeIngredients", back_populates="ingredient",cascade="all, delete-orphan")
    usage_count = Column(Integer, default=0)


class Recipes(Base, ReprMixin):
    """SQLAlchemy model for the Recipe table."""
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)# Cooking instructions
    calories = Column(Float,default = 0.0)
    protein = Column(Float, default = 0.0)
    carbs = Column(Float, default = 0.0)
    fat = Column(Float, default = 0.0)
    fibers = Column(Float, default = 0.0)
    sugar = Column(Float, default = 0.0)
    saturated_fats = Column(Float, default = 0.0)
    category = Column(String(50), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User")
    portions = Column(Integer, default=1)
    season = Column(JSON, nullable=True, default=list)
    type = Column(JSON, nullable=True, default=list)
    photograph_url = Column(String, nullable=True)
    cooking_time = Column(Integer, nullable=True)  # in minutes
    usage_count = Column(Integer, default=0)
    recipe_ingredients = relationship("RecipeIngredients", back_populates="recipe",cascade="all, delete-orphan")
    __repr_fields__ = ("id", "name", "type")


class RecipeIngredients(Base):
    """SQLAlchemy model for the RecipeIngredients table.Ingredients and quantity for each recipe."""
    __tablename__ = "recipe_ingredients"
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE",onupdate="CASCADE"))
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="RESTRICT",onupdate="CASCADE"))
    quantity = Column(Float, default= 0.0)  # Quantity in grams or appropriate unit
    recipe = relationship("Recipes", back_populates="recipe_ingredients")
    ingredient = relationship("Ingredients",back_populates="recipe_ingredients")