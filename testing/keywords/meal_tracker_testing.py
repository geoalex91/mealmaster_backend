from testing.keywords.mt_profile import MtProfile
from fastapi.testclient import TestClient
from testing.keywords.mt_ingredients import MTIngredients
from testing.keywords.mt_recipes import MTRecipes
from main import app

class MealTracker:
    def __init__(self):
        # Initialize the TestClient with the FastAPI app
        self.client = TestClient(app)
        # Initialize the MtProfile instance with the TestClient
        self.mt_profile = MtProfile(self.client)
        self.mt_ingredients = MTIngredients(self.client,self.mt_profile)
        self.mt_recipes = MTRecipes(self.client,self.mt_profile)

    def create_profiles(self):
        # Delegate the creation of a new profile to the MtProfile instance
        return self.mt_profile.create_profiles()
    
    def create_new_user(self, username: str, email: str, password: str):
        # Delegate the creation of a new profile to the MtProfile instance
        return self.mt_profile.create_new_profile(username=username, email=email, password=password)
    
    def verify_user(self, email: str,code: str):
        # Delegate the verification of a user to the MtProfile instance
        return self.mt_profile.verify_user(email, code)
    
    def resend_verification(self, email: str):
        # Delegate the resending of verification code to the MtProfile instance
        return self.mt_profile.resend_verification(email)
    
    def get_verification_code(self, email: str):
        # Delegate the retrieval of the verification code to the MtProfile instance
        return self.mt_profile.get_verification_code(email)
    
    def login_user(self, username: str, password: str):
        # Delegate the login of a user to the MtProfile instance
        return self.mt_profile.login_user(username, password)
    def change_password(self, username: str, old_password: str, new_password: str):
        # Delegate the change password of a user to the MtProfile instance
        return self.mt_profile.change_password(username, old_password, new_password)
    
    def delete_account(self, username: str, password: str):
        # Delegate the deletion of a user account to the MtProfile instance
        return self.mt_profile.delete_account(username, password)
    
    def create_ingredient(self, ingredient_data: dict):
        # Import MTIngredients here to avoid circular import issues
        return self.mt_ingredients.create_ingredient(ingredient_data)
    
    def get_all_ingredients(self):
        # Import MTIngredients here to avoid circular import issues
        return self.mt_ingredients.get_all_ingredients()
    
    def update_ingredient(self, ingredient_id: int, updates: dict):
        # Import MTIngredients here to avoid circular import issues
        return self.mt_ingredients.update_ingredient(ingredient_id, updates)
    
    def delete_ingredient(self, ingredient_id: int):
        # Import MTIngredients here to avoid circular import issues
        return self.mt_ingredients.delete_ingredient(ingredient_id)
    
    def get_ingredient_id(self, ingredient_name: str):
        # Import MTIngredients here to avoid circular import issues
        return self.mt_ingredients.get_ingredient_id(ingredient_name)

    def create_ingredients_from_file(self):
        """Create ingredients from a predefined JSON file."""
        return self.mt_ingredients.create_ingredients_from_file()

    def search_ingredients(self, query: str, search_type: str = "normal", limit: int = 10):
        return self.mt_ingredients.search_ingredient_in_database(ingredient_name=query, type=search_type, limit=limit)

    def get_ingredient_by_id(self, ingredient_id: int):
        return self.mt_ingredients.get_ingredient_by_id(ingredient_id)

    def get_ingredient_usage_count(self, ingredient_name: str):
        return self.mt_ingredients.get_ingredient_usage_count(ingredient_name)
    
    def create_recipe(self, recipe_data: dict):
        return self.mt_recipes.create_recipe(recipe_data)
    
    def edit_recipe(self, recipe_id: int, recipe_data: dict):
        return self.mt_recipes.update_recipe(recipe_id, recipe_data)
    
    def delete_recipe(self, recipe_id: int):
        return self.mt_recipes.delete_recipe(recipe_id)
    
    def search_recipes(self, query: str, search_type: str = "normal"):
        return self.mt_recipes.search_recipes(query, search_type)
    
    def get_recipe_details(self, recipe_id: int):
        return self.mt_recipes.get_recipe_details_by_id(recipe_id)
    
    def get_recipe_usage_count(self, recipe_name: str):
        return self.mt_recipes.get_recipe_usage_count(recipe_name)
    
    def create_recipes_from_file(self):
        """Create recipes from a predefined JSON file."""
        return self.mt_recipes.create_recipes_from_file()
    
    def get_recipe_id_by_name(self, recipe_name: str):
        return self.mt_recipes.get_recipe_id_by_name(recipe_name)
