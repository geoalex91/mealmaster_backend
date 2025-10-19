from fastapi import APIRouter, Depends, HTTPException, status, Query
from routers.schemas import (
    IngredientsDisplay,
    IngredientsBase,
    IngredientsUpdate,
    IngredientsSummary,
    CursorIngredientsResponse,
)
from sqlalchemy.orm.session import Session
from routers.schemas import UserDisplay
from db.database import get_db
from db.db_ingredients import create, get_ingredient_by_name, update, delete, get_ingredient_by_id
from resources.logger import Logger
from typing import List, Optional
from db.models import Ingredients
from auth.auth2 import get_current_user
from resources.core.cache import ingredient_cache
from resources.paginated_querry import paginated_query, paginate_live_search

logger = Logger()
router = APIRouter(prefix="/ingredients", tags=["ingredients"])
MAX_LIMIT = 100

@router.post('/create_ingredient',response_model=IngredientsDisplay, summary="Create a new ingredient",
            description="This endpoint allows the creation of a new ingredient associated with a user.",)
def create_ingredient(request: IngredientsBase, db: Session = Depends(get_db),current_user: UserDisplay = Depends(get_current_user)):
    try:
        ingredient = create(db, request, creator_id=current_user.id)
        ingredient_cache.add_ingredient(IngredientsSummary.model_validate(ingredient))
        return ingredient
    except Exception as e:
        logger.error(f"Error creating ingredient: {e}")
        raise HTTPException(status_code=500, detail=f"{e}")

@router.get("/search", response_model=CursorIngredientsResponse)
def live_tree_search(querry: str = Query(..., min_length=2),search_type = 'normal',limit: int = Query(10, ge=1, le=50),
    cursor: int | None = None,current_user: UserDisplay = Depends(get_current_user)):
    try:
        if search_type == 'normal':
            results = ingredient_cache.search_ingredients(querry)
        elif search_type == 'fuzzy':
            results = ingredient_cache.fuzzy_search(querry)
        elif search_type == 'smart':
            results = ingredient_cache.smart_search(querry, limit=50)
        else:
            logger.error(f"Invalid search type specified: {search_type}")
            raise HTTPException(status_code=400, detail="Invalid search type specified.")
        ingredient_list = []
        for item in results:
            ingredient_list.append(IngredientsSummary.model_validate(item))
        return paginate_live_search(ingredient_list, limit=limit, cursor=cursor)
    except Exception as e:
        logger.error(f"Error during live search: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/browse", response_model=CursorIngredientsResponse)
def list_ingredients_cursor(db: Session = Depends(get_db),limit: int = Query(20, ge=1, le=MAX_LIMIT),
    cursor: Optional[int] = None,filters: Optional[List] = Query(None),
    current_user: UserDisplay = Depends(get_current_user)):
    try:
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        return paginated_query(db, Ingredients, limit=limit, cursor=cursor, filters=filters)
    except Exception as e:
        logger.error(f"Error listing ingredients: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get('/{ingredient_id}', response_model=IngredientsDisplay, summary="Get ingredient by ID")
def get_ingredient(ingredient_id: int, db: Session = Depends(get_db), current_user: UserDisplay = Depends(get_current_user)):
    ingredient = get_ingredient_by_id(db, ingredient_id)
    if not ingredient:
        logger.error(f"Ingredient not found: ID {ingredient_id}")
        raise HTTPException(status_code=404, detail="Ingredient not found")
    ingredient_cache.increment_usage(IngredientsSummary.model_validate(ingredient))
    return ingredient

@router.patch('/{ingredient_id}', response_model=IngredientsDisplay, summary="Partially update an ingredient")
def edit_ingredient(ingredient_id: int,request: IngredientsUpdate,db: Session = Depends(get_db),
    current_user: UserDisplay = Depends(get_current_user)):
    try:
        old_name = get_ingredient_by_id(db, ingredient_id)
        if not old_name:
            raise HTTPException(status_code=404, detail="Ingredient not found")
        ingredient = update(db, ingredient_id=ingredient_id, user_id=current_user.id, updates=request)
        if request.name != old_name:
            ingredient_cache.rename_ingredient(old_name=old_name, new_name=IngredientsSummary.model_validate(ingredient))
        return ingredient
    except Exception as e:
        logger.error(f"Error editing ingredient: {e}")
        raise HTTPException(status_code=500, detail=f"{e}")

@router.delete('/{ingredient_id}', summary="Delete an ingredient", status_code=200)
def delete_ingredient(ingredient_id: int, db: Session = Depends(get_db), current_user: UserDisplay = Depends(get_current_user)):
    """Delete an ingredient owned by the current user."""
    try:
        ingredient_name = get_ingredient_by_id(db, ingredient_id)
        delete_msg = delete(db, ingredient_id=ingredient_id, user_id=current_user.id)
        if ingredient_name != None:
            ingredient_cache.remove_ingredient(ingredient_name)
        return delete_msg
    except Exception as e:
        logger.error(f"Error deleting ingredient: {e}")
        raise HTTPException(status_code=500, detail=f"{e}")

