from fastapi import APIRouter, Depends, HTTPException, status
from routers.schemas import IngredientsDisplay, IngredientsBase
from sqlalchemy.orm.session import Session
from db.database import get_db
from db.db_ingredients import create, get_all
from resources.logger import Logger
from typing import List

router = APIRouter(prefix="/ingredients", tags=["ingredients"])

@router.post('/create_ingredient',response_model=IngredientsDisplay, summary="Create a new ingredient",
            description="This endpoint allows the creation of a new ingredient associated with a user.",)
def create_ingredient(request: IngredientsBase, db: Session = Depends(get_db)):
    return create(db, request)

@router.get('/all', response_model=List[IngredientsDisplay], summary="Get all ingredients",
            description="This endpoint retrieves all ingredients from the database.")
def get_all_ingredients(db: Session = Depends(get_db)):
    return get_all(db)