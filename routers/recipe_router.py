from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from schemas import RecipesBase, RecipesDisplay
from db.db_recipes import create_recipe
from auth.auth2 import get_current_user
from db.db_recipes import get_recipe_by_id, update_recipe, delete_recipe
from resources.logger import Logger

router = APIRouter(prefix="/recipes", tags=["Recipes"])
logger = Logger()

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
        return recipe
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.put("/{recipe_id}", response_model=RecipesDisplay, status_code=status.HTTP_200_OK, description="Edit an existing recipe.")
def edit_recipe_endpoint(recipe_id: int, request: RecipesBase, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
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
        logger.info(f"Recipe {recipe_id} deleted by user {current_user.id}.")
        return {"detail": message}
    except Exception as e:
        logger.error(f"Error deleting recipe {recipe_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")