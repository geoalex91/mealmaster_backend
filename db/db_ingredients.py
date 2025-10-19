from routers.schemas import IngredientsBase, IngredientsUpdate
from sqlalchemy.orm import Session
from db.models import Recipes, Ingredients, RecipeIngredients
from resources.logger import Logger
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from sqlalchemy import func
import threading
from resources.core.cache import sync_usage_to_db
logger = Logger()

def create(db: Session, request: IngredientsBase, creator_id: int):
    """Create a new ingredient associated with a user.
    Args:
        db (Session): SQLAlchemy database session.
        request (IngredientsBase): Pydantic model containing ingredient data.
        creator_id (int): ID of the user creating the ingredient.
        Raises:
        HTTPException: 
            - 422 if required fields are missing or invalid.
            Returns:
            Ingredients: The created ingredient instance."""
    required_fields = [
        request.name, request.calories, request.protein, request.carbs,
        request.fat, request.fibers, request.sugar, request.saturated_fats, request.category
    ]
    if any(field is None for field in required_fields):
        logger.error("Missing required ingredient fields.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing or invalid ingredient data.")
    # Optionally, add more checks (e.g., negative values)
    if request.calories < 0 or request.protein < 0:
        logger.error("Nutritional values cannot be negative.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nutritional values must be non-negative.")
    new_ingredient = Ingredients(
        name=request.name,
        calories=request.calories,
        protein=request.protein,
        carbs=request.carbs,
        fat=request.fat,
        fibers=request.fibers,
        sugar=request.sugar,
        saturated_fats=request.saturated_fats,
        category=request.category,
        user_id=creator_id
    )
    if db.query(Ingredients).filter(Ingredients.name == request.name).first():
        logger.error(f"Ingredient with name {request.name} already exists")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="An ingredient with that name already exists")
    db.add(new_ingredient)
    db.commit()
    db.refresh(new_ingredient)
    logger.info(f"Ingredient created: {new_ingredient.name} for user ID: {new_ingredient.user_id}")
    return new_ingredient

def get_all(db: Session):
    return db.query(Ingredients).all()

def get_ingredient_by_id(db: Session, ingredient_id: int):
    return db.query(Ingredients).filter(Ingredients.id == ingredient_id).first()

def get_ingredients_by_recipe(db: Session, recipe_id: int):
    return db.query(Ingredients).join(RecipeIngredients).filter(RecipeIngredients.recipe_id == recipe_id).all()

def get_ingredient_by_name(db: Session, name: str):
    return db.query(Ingredients).filter(Ingredients.name == name).first()

def update(db: Session, ingredient_id: int, user_id: int, updates: IngredientsUpdate):
    """
    Update an existing ingredient for a specific user.
    Args:
        db (Session): SQLAlchemy database session.
        ingredient_id (int): ID of the ingredient to update.
        user_id (int): ID of the user who owns the ingredient.
        updates (IngredientsUpdate): Pydantic model containing fields to update.
    Raises:
        HTTPException: 
            - 404 if the ingredient is not found.
            - 400 if no fields are provided to update.
            - 409 if the new name already exists or there is a database conflict.
    Returns:
        Ingredients: The updated ingredient instance.
    """

    ingredient = db.query(Ingredients).filter(
        Ingredients.id == ingredient_id,
        Ingredients.user_id == user_id
    ).first()
    if not ingredient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Ingredient not found")

    data = updates.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No fields provided to update")

    # If name is changing, optionally validate uniqueness
    if "name" in data and data["name"] != ingredient.name:
        existing = db.query(Ingredients).filter(
            Ingredients.name == data["name"]
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="An ingredient with that name already exists")

    for field, value in data.items():
        setattr(ingredient, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Conflict updating ingredient")
    db.refresh(ingredient)
    logger.info(f"Ingredient updated: id={ingredient.id} by user {user_id}")
    return ingredient

def delete(db: Session, ingredient_id: int, user_id: int):
    """Delete an ingredient owned by the given user.

    Args:
        db: Database session
        ingredient_id: ID of ingredient to delete
        user_id: ID of current authenticated user (ownership enforcement)
    Raises:
        HTTPException 404 if not found or not owned by user
    Returns:
        dict message on success
    """
    ingredient = db.query(Ingredients).filter(
        Ingredients.id == ingredient_id,
        Ingredients.user_id == user_id
    ).first()
    if not ingredient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Ingredient not found")
    db.delete(ingredient)
    db.commit()
    logger.info(f"Ingredient deleted: id={ingredient_id} by user {user_id}")
    return {"message": "Ingredient deleted successfully", "ingredient_id": ingredient_id}
