from sqlalchemy.orm import Session
from sqlalchemy import func
from db.models import Recipes, RecipeIngredients
from routers.schemas import RecipesBase, RecipeIngredientBase
from db.db_ingredients import get_ingredient_by_id
from fastapi import HTTPException, status
from resources.logger import Logger

logger = Logger()

def create_recipe(db: Session, recipe_data: RecipesBase, user_id: int):
    """Create a new recipe along with its ingredients."""
    # Create the recipe
    required_fields = [
        recipe_data.name, recipe_data.description]
    if any(field is None for field in required_fields):
        logger.error("Missing required recipe fields.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing or invalid recipe data.")
    if recipe_data.cooking_time < 0 or recipe_data.portions < 0:
        logger.error("Cooking time and portions cannot be negative.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cooking time and portions must be non-negative.")
    if not recipe_data.recipe_ingredients:
        logger.error("Attempted to create recipe without ingredients.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipe must have at least one ingredient")
    new_recipe = Recipes(
        name=recipe_data.name,description=recipe_data.description,
        category=recipe_data.category,user_id=user_id, portions=recipe_data.portions,
        season=recipe_data.season,type=recipe_data.type,
        photograph_url=recipe_data.photograph_url,
        cooking_time=getattr(recipe_data, 'cooking_time', None))
    if db.query(Recipes).filter(Recipes.name == recipe_data.name).first():
        logger.error(f"Recipe with name {recipe_data.name} already exists")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="A recipe with that name already exists")

    recipe_calories = 0.0
    recipe_protein = 0.0
    recipe_carbs = 0.0
    recipe_fat = 0.0
    recipe_fibers = 0.0
    recipe_sugar = 0.0
    recipe_saturated_fats = 0.0
    db.add(new_recipe)
    db.flush()  # Flush to get the new recipe ID
    # Add ingredients to the recipe
    for ingredient in recipe_data.recipe_ingredients:
        if ingredient.quantity <= 0:
            logger.error("Ingredient quantity must be greater than zero.")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Ingredient quantity must be greater than zero.")
        ingredient_data = get_ingredient_by_id(db, ingredient.ingredient_id)
        if not ingredient_data:
            logger.error(f"Ingredient with ID {ingredient.ingredient_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ingredient with ID {ingredient.ingredient_id} not found.")
        recipe_ingredient = RecipeIngredients(
            recipe_id=new_recipe.id,
            ingredient_id=ingredient.ingredient_id,
            quantity=ingredient.quantity
        )
        db.add(recipe_ingredient)
        recipe_calories += (ingredient_data.calories * ingredient.quantity) / 100
        recipe_protein += (ingredient_data.protein * ingredient.quantity) / 100
        recipe_carbs += (ingredient_data.carbs * ingredient.quantity) / 100
        recipe_fat += (ingredient_data.fat * ingredient.quantity) / 100
        recipe_fibers += (ingredient_data.fibers * ingredient.quantity) / 100
        recipe_sugar += (ingredient_data.sugar * ingredient.quantity) / 100
        recipe_saturated_fats += (ingredient_data.saturated_fats * ingredient.quantity) / 100
    new_recipe.calories = recipe_calories
    new_recipe.protein = recipe_protein
    new_recipe.carbs = recipe_carbs
    new_recipe.fat = recipe_fat
    new_recipe.fibers = recipe_fibers
    new_recipe.sugar = recipe_sugar
    new_recipe.saturated_fats = recipe_saturated_fats
    db.commit()
    db.refresh(new_recipe)
    return new_recipe

def get_recipe_by_id(db: Session, recipe_id: int):
    """Retrieve a recipe by its ID."""
    logger.info(f"Fetching recipe with ID: {recipe_id}")
    return db.query(Recipes).filter(Recipes.id == recipe_id).first()

def get_recipes_by_name(db: Session, name: str):
    """Retrieve recipes by their name."""
    logger.info(f"Fetching recipes with name: {name}")
    return db.query(Recipes).filter(Recipes.name == name).first()

def get_all_recipes(db: Session):
    """Retrieve all recipes."""
    logger.info("Fetching all recipes")
    return db.query(Recipes).all()

def get_recipes_by_ingredient(db: Session, ingredient_id: int):
    """Retrieve recipes that include a specific ingredient."""
    logger.info(f"Fetching recipes with ingredient ID: {ingredient_id}")
    return db.query(Recipes).join(RecipeIngredients).filter(RecipeIngredients.ingredient_id == ingredient_id).all()

def update_recipe(db: Session, recipe_id: int, user_id: int, recipe_data: RecipesBase):
    """Update an existing recipe and its ingredients."""
    recipe = db.query(Recipes).filter(Recipes.id == recipe_id, Recipes.user_id == user_id).first()
    try:
        if not recipe:
            logger.warning(f"Recipe with ID {recipe_id} not found or access denied.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found or access denied")
        if not recipe_data.recipe_ingredients:
            logger.warning("Attempted to update recipe without ingredients.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recipe must have at least one ingredient")
        # Update recipe fields
        recipe.name = recipe_data.name
        recipe.description = recipe_data.description
        recipe.category = recipe_data.category
        recipe.portions = recipe_data.portions
        recipe.season = recipe_data.season
        recipe.type = recipe_data.type
        recipe.photograph_url = recipe_data.photograph_url
        recipe.cooking_time = recipe_data.cooking_time
        recipe_calories = 0.0
        recipe_protein = 0.0
        recipe_carbs = 0.0
        recipe_fat = 0.0
        recipe_fibers = 0.0
        recipe_sugar = 0.0
        recipe_saturated_fats = 0.0
        # Clear existing ingredients
        db.query(RecipeIngredients).filter(RecipeIngredients.recipe_id == recipe_id).delete()
        logger.info(f"Cleared existing ingredients for recipe ID: {recipe_id}")
        # Add updated ingredients
        for ingredient in recipe_data.recipe_ingredients:
            ingredient_row = get_ingredient_by_id(db, ingredient.ingredient_id)
            if not ingredient_row:
                logger.error(f"Ingredient with ID {ingredient.ingredient_id} not found.")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ingredient with ID {ingredient.ingredient_id} not found.")
            recipe_ingredient = RecipeIngredients(recipe_id=recipe.id,
                ingredient_id=ingredient.ingredient_id,quantity=ingredient.quantity)
            recipe_calories += (ingredient_row.calories * ingredient.quantity) / 100
            recipe_protein += (ingredient_row.protein * ingredient.quantity) / 100
            recipe_carbs += (ingredient_row.carbs * ingredient.quantity) / 100
            recipe_fat += (ingredient_row.fat * ingredient.quantity) / 100
            recipe_fibers += (ingredient_row.fibers * ingredient.quantity) / 100
            recipe_sugar += (ingredient_row.sugar * ingredient.quantity) / 100
            recipe_saturated_fats += (ingredient_row.saturated_fats * ingredient.quantity) / 100
            db.add(recipe_ingredient)
        recipe.calories = recipe_calories
        recipe.protein = recipe_protein
        recipe.carbs = recipe_carbs
        recipe.fat = recipe_fat
        recipe.fibers = recipe_fibers
        recipe.sugar = recipe_sugar
        recipe.saturated_fats = recipe_saturated_fats
        db.commit()
        db.refresh(recipe)
        return recipe
    except Exception as e:
        logger.error(f"Error updating recipe ID {recipe_id}: {e}")
        db.rollback()
        return False

def delete_recipe(db: Session, recipe_id: int, user_id: int):
    """Delete a recipe by its ID."""
    try:
        recipe = db.query(Recipes).filter(Recipes.id == recipe_id, Recipes.user_id == user_id).first()
        if not recipe:
            logger.warning(f"Recipe with ID {recipe_id} not found or access denied.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found or access denied")
        recipe_ingredient = db.query(RecipeIngredients).filter(RecipeIngredients.recipe_id == recipe_id).all()
        for ingredient in recipe_ingredient:
            db.delete(ingredient)
        db.delete(recipe)
        db.commit()
        logger.info(f"Deleted recipe with ID: {recipe_id}")
    except Exception as e:
        logger.error(f"Error deleting recipe ID {recipe_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting recipe")
    return "Recipe deleted successfully"

def get_recipe_with_ingredients(db:Session, ingredient_ids: list[int] = None, min_matches = None):
    """
    Retrieve recipes that contain a specified list of ingredient IDs.
    Args:
        db (Session): SQLAlchemy database session.
        ingredient_ids (list[int], optional): List of ingredient IDs to filter recipes. Defaults to None.
        min_matches (int, optional): Minimum number of matching ingredients required. Defaults to None.
    Returns:
        list[Recipes]: List of recipes that match the criteria.
    """
    ingredient_ids = [i for i in ingredient_ids if i is not None]
    if not ingredient_ids:
        return []
    total = len(ingredient_ids)
    if min_matches is None:
        min_matches = total
    if min_matches < 0:
        min_matches = 1
    if min_matches > total:
        min_matches = total
    query = db.query(Recipes)
    if min_matches == 1:
        query = query.join(RecipeIngredients, RecipeIngredients.recipe_id == Recipes.id).filter(
            RecipeIngredients.ingredient_id.in_(ingredient_ids).distinct()
        )
    else:
        subquery = db.query(RecipeIngredients.recipe_id).filter(
            RecipeIngredients.ingredient_id.in_(ingredient_ids)).group_by(
                RecipeIngredients.recipe_id).having(func.count(func.distinct(RecipeIngredients.ingredient_id)) >= min_matches).subquery()
        query = query.filter(Recipes.id.in_(subquery))

    results = query.all()
    logger.info(f"Fetched {len(results)} recipes with specified ingredients.")
    return results