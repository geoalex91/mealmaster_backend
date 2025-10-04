from pydantic import BaseModel,ConfigDict
from typing import Optional

# User Schemas
class UserBase(BaseModel):
    """Base schema for user data."""
    username: str
    email: str
    password: str

class UserDisplay(BaseModel):
    """Schema for displaying user data."""
    username: str
    class Config:
        from_attributes = True

# Ingredient Schemas
class IngredientsBase(BaseModel):
    """Base schema for ingredient data."""
    model_config = ConfigDict(extra='forbid')
    name: str
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fibers: Optional[float] = None
    sugar: Optional[float] = None
    saturated_fats: Optional[float] = None
    category: Optional[str] = None

class User(BaseModel):
    username: str
    class Config:
        from_attributes = True

class IngredientsDisplay(BaseModel):
    """Schema for displaying ingredient data."""
    id: int
    name: str
    calories: float
    protein: float
    carbs: float
    fat: float
    fibers: float
    sugar: float
    saturated_fats: float
    category: str
    user: User
    class Config:
        from_attributes = True

class IngredientsUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: Optional[str] = None
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fibers: Optional[float] = None
    sugar: Optional[float] = None
    saturated_fats: Optional[float] = None
    category: Optional[str] = None