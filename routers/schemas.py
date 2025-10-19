from pydantic import BaseModel,ConfigDict
from typing import Optional, List

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

class User(BaseModel):
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

class IngredientsSummary(BaseModel):
    id: int
    name: str
    category: str | None = None
    calories: float
    protein: float
    carbs: float
    fat: float
    usage_count: int
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


class CursorIngredientsResponse(BaseModel):
    items: List[IngredientsSummary]
    next_cursor: Optional[int] = None
    has_more: bool


class RecipeIngredientBase(BaseModel):
    model_config = ConfigDict(extra='forbid')
    ingredient_id: int
    quantity: float  # Quantity in grams or appropriate unit

class RecipeIngredientDisplay(BaseModel):
    ingredient: IngredientsDisplay
    quantity: float
    class Config:
        from_attributes = True
# Recipe Schemas
class RecipesBase(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    description: str
    category: Optional[str] = None
    recipe_ingredients: List[RecipeIngredientBase] = None

class RecipesDisplay(BaseModel):
    id: int
    name:str
    description: str
    calories: float
    protein:float
    carbs: float
    fat: float
    fibers: float
    sugar: float
    saturated_fats: float
    category: str
    user: User
    recipe_ingredients: List[RecipeIngredientDisplay]
    class Config:
        from_attributes = True

