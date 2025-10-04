from fastapi import APIRouter, Depends, HTTPException, status
from routers.schemas import IngredientsDisplay, IngredientsBase, IngredientsUpdate
from sqlalchemy.orm.session import Session
from routers.schemas import UserDisplay
from db.database import get_db
from db.db_ingredients import create, get_all, update, delete
from resources.logger import Logger
from typing import List
from auth.auth2 import get_current_user

logger = Logger()
router = APIRouter(prefix="/ingredients", tags=["ingredients"])

@router.post('/create_ingredient',response_model=IngredientsDisplay, summary="Create a new ingredient",
            description="This endpoint allows the creation of a new ingredient associated with a user.",)
def create_ingredient(request: IngredientsBase, db: Session = Depends(get_db),current_user: UserDisplay = Depends(get_current_user)):
    return create(db, request, creator_id=current_user.id)

@router.get('/all', summary="Get all ingredients",
            description="This endpoint retrieves all ingredients from the database.")
def get_all_ingredients(db: Session = Depends(get_db),current_user: UserDisplay = Depends(get_current_user)):
    return {'data': get_all(db),
            'current_user':current_user}

@router.patch('/{ingredient_id}', response_model=IngredientsDisplay, summary="Partially update an ingredient")
def edit_ingredient(ingredient_id: int,request: IngredientsUpdate,db: Session = Depends(get_db),
    current_user: UserDisplay = Depends(get_current_user)):
    return update(db, ingredient_id=ingredient_id, user_id=current_user.id, updates=request)

@router.delete('/{ingredient_id}', summary="Delete an ingredient", status_code=200)
def delete_ingredient(ingredient_id: int, db: Session = Depends(get_db), current_user: UserDisplay = Depends(get_current_user)):
    """Delete an ingredient owned by the current user."""
    return delete(db, ingredient_id=ingredient_id, user_id=current_user.id)