from fastapi import APIRouter, Depends, HTTPException, status, Query
from enum import Enum
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
from resources.core.entity_cache import ingredient_cache
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

class SearchType(str, Enum):
    prefix = "prefix"
    fuzzy = "fuzzy"
    multi_token_prefix = "multi_token_prefix"
    multi_token_fuzzy = "multi_token_fuzzy"
    smart = "smart"

@router.get("/search", response_model=CursorIngredientsResponse, summary="Live search ingredients")
def live_tree_search(
    query: str = Query(..., min_length=2, description="Search text (min 2 chars)"),
    search_type: SearchType = SearchType.prefix,
    limit: int = Query(10, ge=1, le=50),
    cursor: Optional[int] = None,
    current_user: UserDisplay = Depends(get_current_user)):
    try:
        if search_type is SearchType.prefix:
            raw = ingredient_cache.prefix_search(query, limit=limit)
        elif search_type is SearchType.fuzzy:
            raw = ingredient_cache.fuzzy_search(query, limit=limit)
        elif search_type is SearchType.multi_token_prefix:
            raw = ingredient_cache.multi_token_prefix_search(query, limit=limit)
        elif search_type is SearchType.multi_token_fuzzy:
            raw = ingredient_cache.multi_token_fuzzy_search(query, limit=limit)
        else:  # smart
            raw = ingredient_cache.smart_search(query, limit=limit)

        # Defensive: ensure list
        if isinstance(raw, dict):
            # Cache returned error structure; treat as empty
            raw_list = []
        else:
            raw_list = raw

        # Normalize to IngredientsSummary models (avoid double validation if already model instances)
        ingredient_list = []
        for item in raw_list:
            if isinstance(item, IngredientsSummary):
                ingredient_list.append(item)
            else:
                try:
                    ingredient_list.append(IngredientsSummary.model_validate(item))
                except Exception:
                    logger.warning(f"Skipping invalid cache item: {item}")

        # Apply limit early if no cursor (optimization)
        if cursor in (None, 0) and len(ingredient_list) > limit:
            ingredient_list = ingredient_list[: limit + 1]  # keep one extra for has_more logic

        return paginate_live_search(ingredient_list, limit=limit, cursor=cursor)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during live search: {e}")
        raise HTTPException(status_code=500, detail=f"{e}")

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
        ingredient = get_ingredient_by_id(db, ingredient_id)
        if not ingredient:
            raise HTTPException(status_code=404, detail="Ingredient not found")
        ingredient = update(db, ingredient_id=ingredient_id, user_id=current_user.id, updates=request)
        if request.name != ingredient.name:
            ingredient_cache.rename_ingredient(old_item=IngredientsSummary.model_validate(ingredient),
                                            new_item=IngredientsSummary.model_validate(ingredient))
        return ingredient
    except Exception as e:
        logger.error(f"Error editing ingredient: {e}")
        raise HTTPException(status_code=500, detail=f"{e}")

@router.delete('/{ingredient_id}', summary="Delete an ingredient", status_code=200)
def delete_ingredient(ingredient_id: int, db: Session = Depends(get_db), current_user: UserDisplay = Depends(get_current_user)):
    """Delete an ingredient owned by the current user."""
    try:
        ingredient = get_ingredient_by_id(db, ingredient_id)
        delete_msg = delete(db, ingredient_id=ingredient_id, user_id=current_user.id)
        if ingredient != None:
            ingredient_cache.remove_ingredient(IngredientsSummary.model_validate(ingredient))
        return delete_msg
    except Exception as e:
        logger.error(f"Error deleting ingredient: {e}")
        raise HTTPException(status_code=500, detail=f"{e}")

@router.get('/id-by-name/{ingredient_name}', response_model=int, summary="Get ingredient ID by name")
def get_ingredient_id_by_name(ingredient_name: str, db: Session = Depends(get_db),
                              current_user: UserDisplay = Depends(get_current_user)) -> int:
    """Get ingredient ID by name."""
    try:
        ingredient = get_ingredient_by_name(db, ingredient_name)
        if not ingredient:
            logger.error(f"Ingredient not found: Name {ingredient_name}")
            raise HTTPException(status_code=404, detail="Ingredient not found")
        return {"id": ingredient.id}
    except Exception as e:
        logger.error(f"Error getting ingredient by name: {e}")
        raise HTTPException(status_code=500, detail=f"{e}")