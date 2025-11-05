from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Recipes
from resources.paginated_querry import paginate_live_search, paginated_query
from routers.ingredient_router import SearchType
from routers.schemas import CursorRecipesResponse, RecipeSummary, RecipesBase, RecipesDisplay, UserDisplay, RecipeUpdate
from db.db_recipes import create_recipe
from auth.auth2 import get_current_user
from db.db_recipes import *
from resources.logger import Logger
from resources.core.entity_cache import recipe_cache

router = APIRouter(prefix="/recipes", tags=["Recipes"])
logger = Logger()
MAX_LIMIT = 100

@router.post("/", response_model=RecipesDisplay, status_code=status.HTTP_201_CREATED, description="Create a new recipe with associated ingredients.")
def create_recipe_endpoint(request: RecipesBase,db: Session = Depends(get_db),current_user: dict = Depends(get_current_user)):
    """Creates a new recipe for the authenticated user.

    Args:
        request (RecipesBase): The recipe data to create.
        db (Session): The database session dependency.
        current_user (dict): The currently authenticated user dependency.

    Returns:
        Recipe: The created recipe object.

    Raises:
        HTTPException: If there is a validation error with status code 400."""
    
    try:
        recipe = create_recipe(db, request, user_id=current_user.id)
        recipe_cache.add_ingredient(RecipeSummary.model_validate(recipe))
        return recipe
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.put("/{recipe_id}", response_model=RecipesDisplay, status_code=status.HTTP_200_OK, description="Edit an existing recipe.")
def edit_recipe_endpoint(recipe_id: int, request: RecipeUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Edits an existing recipe for the authenticated user.

    Args:
        recipe_id (int): The ID of the recipe to edit.
        request (RecipesBase): The updated recipe data.
        db (Session): The database session dependency.
        current_user (dict): The currently authenticated user dependency.

    Returns:
        Recipe: The updated recipe object.

    Raises:
        HTTPException: If the recipe does not exist or user is not authorized.
    """
    try:
        recipe = get_recipe_by_id(db, recipe_id)
        if not recipe:
            logger.error(f"Recipe with ID {recipe_id} not found for editing.")
            raise HTTPException(status_code=404, detail="Recipe not found")
        if recipe.user_id != current_user.id:
            logger.error(f"User {current_user.id} is not authorized to edit recipe {recipe_id}.")
            raise HTTPException(status_code=403, detail="Not authorized to edit this recipe")
        try:
            updated_recipe = update_recipe(db, recipe_id, current_user.id,request)
            recipe_cache.rename_ingredient(old_item=RecipeSummary.model_validate(recipe),
                                          new_item=RecipeSummary.model_validate(updated_recipe))
            return updated_recipe
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error editing recipe {recipe_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT, description="Delete an existing recipe.")
def delete_recipe_endpoint(recipe_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Deletes an existing recipe for the authenticated user.

    Args:
        recipe_id (int): The ID of the recipe to delete.
        db (Session): The database session dependency.
        current_user (dict): The currently authenticated user dependency.

    Raises:
        HTTPException: If the recipe does not exist or user is not authorized.
    """
    try:
        recipe = get_recipe_by_id(db, recipe_id)
        if not recipe:
            logger.error(f"Recipe with ID {recipe_id} not found for deletion.")
            raise HTTPException(status_code=404, detail="Recipe not found")
        if recipe.user_id != current_user.id:
            logger.error(f"User {current_user.id} is not authorized to delete recipe {recipe_id}.")
            raise HTTPException(status_code=403, detail="Not authorized to delete this recipe")
        message = delete_recipe(db, recipe_id, current_user.id)
        recipe_cache.remove_ingredient(RecipeSummary.model_validate(recipe))
        logger.info(f"Recipe {recipe_id} deleted by user {current_user.id}.")
        return {"detail": message}
    except Exception as e:
        logger.error(f"Error deleting recipe {recipe_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/browse", response_model=CursorRecipesResponse, description="Browse recipes with cursor pagination.")
def list_recipes_cursor(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=MAX_LIMIT),
    cursor: Optional[int] = None,
    filters: Optional[List[str]] = Query(None),
    current_user: UserDisplay = Depends(get_current_user)
):
    """
    Lists recipes with cursor-based pagination.

    Args:
        db (Session): The database session dependency.
        limit (int): The maximum number of recipes to return.
        cursor (int): The cursor for pagination.
        filters (list): Optional filters to apply.
        current_user (dict): The currently authenticated user dependency.

    Returns:
        dict: A dictionary containing the list of recipes and pagination info.
    """
    try:
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        # Implement your paginated query logic here
        return paginated_query(db, Recipes, limit=limit, cursor=cursor, filters=filters)
        
    except Exception as e:
        logger.error(f"Error listing recipes: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@router.get("/search", response_model=CursorRecipesResponse, summary="Live search recipes")
def live_search_recipes(query: str = Query(..., min_length=2, description="Search text (min 2 chars)"),
    search_type: SearchType = SearchType.prefix, limit: int = Query(10, ge=1, le=50),
    cursor: Optional[int] = None, current_user: UserDisplay = Depends(get_current_user)):
    """
    Performs a live search for recipes based on a query string with pagination.

    Args:
        query (str): The search query string.
        db (Session): The database session dependency.
        limit (int): The maximum number of recipes to return.
        cursor (int): The cursor for pagination.

    Returns:
        dict: A dictionary containing the list of recipes and pagination info.
    """
    try:
        if search_type is SearchType.prefix:
            raw = recipe_cache.prefix_search(query, limit=limit)
        elif search_type is SearchType.fuzzy:
            raw = recipe_cache.fuzzy_search(query, limit=limit)
        elif search_type is SearchType.multi_token_prefix:
            raw = recipe_cache.multi_token_prefix_search(query, limit=limit)
        elif search_type is SearchType.multi_token_fuzzy:
            raw = recipe_cache.multi_token_fuzzy_search(query, limit=limit)
        else:  # smart
            raw = recipe_cache.smart_search(query, limit=limit)
        
         # Defensive: ensure list
        if isinstance(raw, dict):
            # Cache returned error structure; treat as empty
            raw_list = []
        else:
            raw_list = raw
         # Normalize to RecipeSummary models (avoid double validation if already model instances)
        recipe_list = []
        for item in raw_list:
            if isinstance(item, RecipeSummary):
                recipe_list.append(item)
            else:
                try:
                    recipe_list.append(RecipeSummary.model_validate(item))
                except Exception:
                    logger.warning(f"Skipping invalid cache item: {item}")
        # Apply limit early if no cursor (optimization)
        if cursor in (None, 0) and len(recipe_list) > limit:
            recipe_list = recipe_list[: limit + 1]  # keep one extra for has_more logic
        return paginate_live_search(recipe_list, limit=limit, cursor=cursor)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during live search: {e}")
        raise HTTPException(status_code=500, detail=f"Internal exception: {e}")

@router.get("find-by-ingredients", response_model = CursorRecipesResponse, summary="Find recipes by ingredient list")
def find_recipes_by_ingredient_list(ingredient_ids: List[int] = Query(..., description="List of ingredient IDs to search for"),
    db: Session = Depends(get_db), min_matches: int = Query(1, ge=1, description="Minimum number of matching ingredients"),
    limit: int = Query(20, ge=1, le=MAX_LIMIT, description="Maximum number of recipes to return"), cursor: Optional[int] = None):
    """
    Finds recipes that contain a specified list of ingredient IDs."""
    if not ingredient_ids:
        raise HTTPException(status_code=400, detail="Ingredient IDs list cannot be empty")
    if len(ingredient_ids) == 1:
        recipes = get_recipes_by_ingredient(db, ingredient_ids[0])
    else:
        recipes = get_recipe_with_ingredients(db, ingredient_ids, min_matches)
    recipes = [RecipeSummary.model_validate(r) for r in recipes]
    if len(recipes) == 0:
        return {"items": [], "next_cursor": None, "has_more": False}
    
    return paginate_live_search(recipes, limit=limit, cursor=cursor)

@router.get("/{recipe_id}", response_model=RecipesDisplay, description="Get a recipe by its ID.")
def get_recipe(recipe_id: int, db: Session = Depends(get_db), current_user: UserDisplay = Depends(get_current_user)):
    """
    Retrieves a recipe by its ID.

    Args:
        recipe_id (int): The ID of the recipe to retrieve.
        db (Session): The database session dependency.
        current_user (dict): The currently authenticated user dependency.

    Returns:
        Recipe: The requested recipe object.

    Raises:
        HTTPException: If the recipe does not exist.
    """
    recipe = get_recipe_by_id(db, recipe_id)
    recipe_cache.increment_usage(RecipeSummary.model_validate(recipe))
    if not recipe:
        logger.error(f"Recipe not found: ID {recipe_id}")
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe

@router.get('/id-by-name/{recipe_name}', response_model=dict, summary="Get recipe ID by name")
def get_recipe_id_by_name(
    recipe_name: str,
    db: Session = Depends(get_db),
    current_user: UserDisplay = Depends(get_current_user)
) -> int:
    """Return the numeric recipe ID for a given recipe name."""
    try:
        recipe = get_recipes_by_name(db, recipe_name)
        if not recipe:
            logger.error(f"Recipe not found: Name {recipe_name}")
            raise HTTPException(status_code=404, detail="Recipe not found")
        return {"id":recipe.id}
    except Exception as e:
        logger.error(f"Error getting recipe by name: {e}")
        raise HTTPException(status_code=500, detail=f"{e}")