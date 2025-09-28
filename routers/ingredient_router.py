from fastapi import APIRouter, Depends, HTTPException, status
from routers.schemas import IngredientsDisplay, IngredientsBase
from sqlalchemy.orm.session import Session
from routers.schemas import UserDisplay
from db.database import get_db
from db.db_ingredients import create, get_all
from resources.logger import Logger
from typing import List
from auth.auth2 import oauth2_scheme, get_current_user

Logger = Logger()
router = APIRouter(prefix="/ingredients", tags=["ingredients"])

@router.post('/create_ingredient',response_model=IngredientsDisplay, summary="Create a new ingredient",
            description="This endpoint allows the creation of a new ingredient associated with a user.",)
def create_ingredient(request: IngredientsBase, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    return create(db, request)

@router.get('/all', summary="Get all ingredients",
            description="This endpoint retrieves all ingredients from the database.")
def get_all_ingredients(db: Session = Depends(get_db),current_user: UserDisplay = Depends(get_current_user)):
    return {'data': get_all(db),
            'current_user':current_user}