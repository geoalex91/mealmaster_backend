from pydantic import BaseModel

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
    name: str
    calories: float
    protein: float
    carbs: float
    fat: float
    fibers: float
    sugar: float
    saturated_fats: float
    creator_id: int

class User(BaseModel):
    username: str
    class Config:
        from_attributes = True

class IngredientsDisplay(BaseModel):
    """Schema for displaying ingredient data."""
    name: str
    calories: float
    protein: float
    carbs: float
    fat: float
    fibers: float
    sugar: float
    saturated_fats: float
    user: User
    class Config:
        from_attributes = True