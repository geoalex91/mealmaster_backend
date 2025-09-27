from routers.schemas import IngredientsBase
from sqlalchemy.orm import Session
from db.models import Ingredients
from resources.logger import Logger

logger = Logger()

def create(db: Session, request: IngredientsBase):
    new_ingredient = Ingredients(
        name=request.name,
        calories=request.calories,
        protein=request.protein,
        carbs=request.carbs,
        fat=request.fat,
        fibers=request.fibers,
        sugar=request.sugar,
        saturated_fats=request.saturated_fats,
        user_id=request.creator_id
    )
    db.add(new_ingredient)
    db.commit()
    db.refresh(new_ingredient)
    logger.info(f"Ingredient created: {new_ingredient.name} for user ID: {new_ingredient.user_id}")
    return new_ingredient

def get_all(db: Session):
    return db.query(Ingredients).all()