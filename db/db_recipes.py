from sqlalchemy.orm import Session
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
    new_recipe = Recipes(name=recipe_data.name,description=recipe_data.description,
        category=recipe_data.category,user_id=user_id, portions=recipe_data.portions,
        season=recipe_data.season,type=recipe_data.type,
        photograph_url=recipe_data.photograph_url, cooking_time=recipe_data.cooking_time
    )
    if db.query(Recipes).filter(Recipes.name == recipe_data.name).first():
        logger.error(f"Recipe with name {recipe_data.name} already exists")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="A recipe with that name already exists")
    db.refresh(new_recipe)
    recipe_calories = 0.0
    recipe_protein = 0.0
    recipe_carbs = 0.0
    recipe_fat = 0.0
    recipe_fibers = 0.0
    recipe_sugar = 0.0
    recipe_saturated_fats = 0.0
    # Add ingredients to the recipe
    for ingredient in recipe_data.recipe_ingredients:
        if ingredient.quantity <= 0:
            logger.error("Ingredient quantity must be greater than zero.")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Ingredient quantity must be greater than zero.")
        recipe_ingredient = RecipeIngredients(
            recipe_id=new_recipe.id,
            ingredient_id=ingredient.ingredient_id,
            quantity=ingredient.quantity
        )
        db.add(recipe_ingredient)
        ingredient_data = get_ingredient_by_id(db, ingredient.ingredient_id)
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
    
    db.add(new_recipe)
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
        for key, value in recipe_data.model_dump(exclude_unset=True).items():
            setattr(recipe, key, value)
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
            recipe_ingredient = RecipeIngredients(recipe_id=recipe.id,
                ingredient_id=ingredient.ingredient_id,quantity=ingredient.quantity)
            recipe_data = get_ingredient_by_id(db, ingredient.ingredient_id)
            recipe_calories += (recipe_data.calories * ingredient.quantity) / 100
            recipe_protein += (recipe_data.protein * ingredient.quantity) / 100
            recipe_carbs += (recipe_data.carbs * ingredient.quantity) / 100
            recipe_fat += (recipe_data.fat * ingredient.quantity) / 100
            recipe_fibers += (recipe_data.fibers * ingredient.quantity) / 100
            recipe_sugar += (recipe_data.sugar * ingredient.quantity) / 100
            recipe_saturated_fats += (recipe_data.saturated_fats * ingredient.quantity) / 100
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
        db.delete(recipe)
        db.commit()
        logger.info(f"Deleted recipe with ID: {recipe_id}")
    except Exception as e:
        logger.error(f"Error deleting recipe ID {recipe_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting recipe")
    return "Recipe deleted successfully"