from testing.keywords import DATA_PATH
from testing.keywords.utilities import Utilities
from fastapi.testclient import TestClient
from main import app
from testing.keywords.mt_profile import MtProfile
import os, json

LOCALHOST = "http://localhost:8000"

class MTRecipes:
    def __init__(self, client: TestClient, mt_profile: MtProfile):
        self.client = client
        self.utilities = Utilities()
        self.data_path = DATA_PATH
        self.mt_profile = mt_profile
        self.all_recipes = []
        self.recipe_json_path = os.path.join(DATA_PATH, "recipes.json")

    def get_recipe(self, recipe_id: int):
        response = self.client.get(f"{LOCALHOST}/recipes/{recipe_id}")
        return response.json()

    def create_recipe(self, recipe_data: dict):
        recipes_json = {
            "name": recipe_data.get("name"),
            "description": recipe_data.get("description"),
            "image": recipe_data.get("image"),
            "type": recipe_data.get("type"),
            "portions": recipe_data.get("portions"),
            "cooking_time": recipe_data.get("cooking_time"),
            "season": recipe_data.get("season"),
            "category": recipe_data.get("category"),
            "recipe_ingredients": recipe_data.get("recipe_ingredients")}
        if not self.mt_profile.login_user_json:
            self.utilities.log_error("Login JSON is None. Please login first.")
            return False
        try:
            token = self.mt_profile.login_user_json.get("access_token")
        except Exception as e:
            self.utilities.log_error(f"Failed to get access token from profile JSON: {e}")
            return False
        headers = {"Authorization": f"Bearer {token}"}
        self.utilities.log_info(f"Creating recipe: {recipes_json}")
        response = self.client.post(f"{LOCALHOST}/recipes/", json=recipes_json, headers=headers)
        return response.json()

    def update_recipe(self, recipe_id: int, recipe_data: dict):
        recipes_json = {
            "name": recipe_data.get("name"),
            "description": recipe_data.get("description"),
            "image": recipe_data.get("image"),
            "type": recipe_data.get("type"),
            "portions": recipe_data.get("portions"),
            "cooking_time": recipe_data.get("cooking_time"),
            "season": recipe_data.get("season"),
            "category": recipe_data.get("category"),
            "recipe_ingredients": recipe_data.get("recipe_ingredients")}
        if not self.mt_profile.login_user_json:
            self.utilities.log_error("Login JSON is None. Please login first.")
            return False
        try:
            token = self.mt_profile.login_user_json.get("access_token")
        except Exception as e:
            self.utilities.log_error(f"Failed to get access token from profile JSON: {e}")
            return False
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.put(f"{LOCALHOST}/recipes/{recipe_id}", json=recipes_json, headers=headers)
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to update recipe: {response.json()}")
            return response.json()
        return True

    def delete_recipe(self, recipe_id: int):
        if not self.mt_profile.login_user_json:
            self.utilities.log_error("Login JSON is None. Please login first.")
            return False
        try:
            token = self.mt_profile.login_user_json.get("access_token")
        except Exception as e:
            self.utilities.log_error(f"Failed to get access token from profile JSON: {e}")
            return False
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.delete(f"{LOCALHOST}/recipes/{recipe_id}", headers=headers)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to delete recipe: {response.json()}")
            return response.json()
        return True
    
    def search_recipes(self, query: str, search_type: str = "normal"):
        if not self.mt_profile.login_user_json:
            self.utilities.log_error("Login JSON is None. Please login first.")
            return False
        try:
            token = self.mt_profile.login_user_json.get("access_token")
        except Exception as e:
            self.utilities.log_error(f"Failed to get access token from profile JSON: {e}")
            return False
        headers = {"Authorization": f"Bearer {token}"}
        self.utilities.log_info(f"Searching for recipes with query: {query}")
        response = self.client.get(f"{LOCALHOST}/recipes/search", headers=headers,
                                    params={"query": query, "search_type": search_type, "limit": 10, "cursor": 1})
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to search recipes: {response.json()}")
            return response.json()
        for item in response.json():
            if query.lower() in item["name"].lower():
                self.utilities.log_info(f"Found recipe: {item['name']}")
                return int(item["id"])
        return False
    
    def browse_recipes(self):
        """Retrieve all recipes."""
        if not self.mt_profile.login_user_json:
            self.utilities.log_error("Login JSON is None. Please login first.")
            return False
        try:
            token = self.mt_profile.login_user_json.get("access_token")
        except Exception as e:
            self.utilities.log_error(f"Failed to get access token from profile JSON: {e}")
            return False
        headers = {"Authorization": f"Bearer {token}"}
        self.utilities.log_info("Retrieving all recipes")
        response = self.client.get(f"{LOCALHOST}/recipes/browse", headers=headers)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to retrieve recipes: {response.json()}")
            return response.json()
        self.all_recipes = response.json().get("data")
        return self.all_recipes
    
    def get_recipe_details_by_id(self, recipe_id: int):
        """Get recipe details by ID."""
        if not self.mt_profile.login_user_json:
            self.utilities.log_error("Login JSON is None. Please login first.")
            return False
        try:
            token = self.mt_profile.login_user_json.get("access_token")
        except Exception as e:
            self.utilities.log_error(f"Failed to get access token from profile JSON: {e}")
            return False
        headers = {"Authorization": f"Bearer {token}"}
        self.utilities.log_info(f"Searching for recipe with ID: {recipe_id}")
        response = self.client.get(f"{LOCALHOST}/recipes/{recipe_id}", headers=headers)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to retrieve recipe details: {response.json()}")
            return response.json()
        return response.json()

    def get_recipe_usage_count(self, recipe_id: int):
        """Get the usage count of a recipe by ID."""
        if not self.mt_profile.login_user_json:
            self.utilities.log_error("Login JSON is None. Please login first.")
            return False
        try:
            token = self.mt_profile.login_user_json.get("access_token")
        except Exception as e:
            self.utilities.log_error(f"Failed to get access token from profile JSON: {e}")
            return False
        headers = {"Authorization": f"Bearer {token}"}
        self.utilities.log_info(f"Retrieving usage count for recipe ID: {recipe_id}")
        response = self.client.get(f"{LOCALHOST}/recipes/{recipe_id}", headers=headers)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to retrieve recipe usage count: {response.json()}")
            return response.json()
        usage_count = response.json().get("usage_count")
        return usage_count
    
    def load_recipes_data_from_file(self):
        """Load recipe data from a JSON file."""
        try:
            with open(self.recipe_json_path, 'r', encoding='utf-8') as file:
                recipe_data = json.load(file)
                self.utilities.log_info(f"Loaded recipe data from {self.recipe_json_path}")
                return recipe_data
        except Exception as e:
            self.utilities.log_error(f"Failed to load ingredient data from file: {e}")
            return None
         
    def create_recipes_from_file(self):
        """Create multiple recipes from a JSON file."""
        recipe_data = self.load_recipes_data_from_file()
        if not recipe_data:
            return False
        for recipe in recipe_data:
            result = self.create_recipe(recipe)
            if result is not True:
                self.utilities.log_error(f"Failed to create recipe from file data: {recipe}")
        return True
    
    def get_recipe_id_by_name(self, recipe_name: str):
        """Get recipe ID by name."""
        if not self.mt_profile.login_user_json:
            self.utilities.log_error("Login JSON is None. Please login first.")
            return False
        try:
            token = self.mt_profile.login_user_json.get("access_token")
        except Exception as e:
            self.utilities.log_error(f"Failed to get access token from profile JSON: {e}")
            return False
        headers = {"Authorization": f"Bearer {token}"}
        self.utilities.log_info(f"Searching for recipe with name: {recipe_name}")
        response = self.client.get(f"{LOCALHOST}/recipes/id-by-name/{recipe_name}", headers=headers)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to get recipe ID by name: {response.json()}")
            return response.json()
        recipe_id = response.json().get("id")
        return recipe_id