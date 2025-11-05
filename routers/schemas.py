from pydantic import BaseModel,ConfigDict, field_validator
from typing import Optional, List, Union

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
    usage_count: int
    class Config:
        from_attributes = True

class IngredientsSummary(BaseModel):
    id: int
    name: str
    category: str = None
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
    name: Optional[str] = None
    description: Optional[str] = None
    portions: Optional[int] = None
    category: Optional[str] = None
    season: Optional[Union[str, List[str]]] = None
    cooking_time: Optional[int] = None  # in minutes
    type: Optional[Union[str, List[str]]] = None
    photograph_url: Optional[str] = None
    recipe_ingredients: Optional[List[RecipeIngredientBase]] = None

    @field_validator('season', 'type', mode='before')
    def normalize_types(cls,v):
        if isinstance(v, str):
            return [v]
        return v

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
    portions: Optional[int] = None
    season: Optional[List[str]] = None
    type: Optional[List[str]] = None
    cooking_time: Optional[int] = None  # in minutes
    photograph_url: Optional[str] = None
    usage_count: int
    class Config:
        from_attributes = True

class RecipeUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: Optional[str] = None
    description: Optional[str] = None
    portions: Optional[int] = None
    category: Optional[str] = None
    season: Optional[Union[str, List[str]]] = None
    type: Optional[Union[str, List[str]]] = None
    cooking_time: Optional[int] = None  # in minutes
    photograph_url: Optional[str] = None
    recipe_ingredients: Optional[List[RecipeIngredientBase]] = None

    @field_validator('season', 'type', mode='before')
    def normalize_types(cls,v):
        if v is None:
            return v
        return [v] if isinstance(v, str) else v

class RecipeSummary(BaseModel):
    id: int
    name: str
    calories: float
    protein: float
    carbs: float
    fat: float
    usage_count: int
    class Config:
        from_attributes = True

class CursorRecipesResponse(BaseModel):
    items: List[RecipeSummary]
    next_cursor: Optional[int] = None
    has_more: bool