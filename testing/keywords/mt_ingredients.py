from routers.schemas import IngredientsSummary
from testing.keywords import DATA_PATH
from testing.keywords.utilities import Utilities
from fastapi.testclient import TestClient
from main import app
from testing.keywords.mt_profile import MtProfile
import os, json

LOCALHOST = "http://localhost:8000"
class MTIngredients:
    def __init__(self, client: TestClient, mt_profile: MtProfile):
        self.client = client
        self.utilities = Utilities()
        self.mt_profile = mt_profile
        self.all_ingredients = None
        self.ingredient_json_path = os.path.join(DATA_PATH, "ingredients_ro.json")
    
    def create_ingredient(self, ingredient_data: dict):
        """Create a new ingredient."""
        ingredient_json = {
            "name": ingredient_data.get("name"),
            "calories": ingredient_data.get("calories"),
            "protein": ingredient_data.get("protein"),
            "carbs": ingredient_data.get("carbs"),
            "fat": ingredient_data.get("fat"),
            "fibers": ingredient_data.get("fibers"),
            "sugar": ingredient_data.get("sugar"),
            "saturated_fats": ingredient_data.get("saturated_fats"),
            "category": ingredient_data.get("category")
        }
        if not self.mt_profile.login_user_json:
            self.utilities.log_error("Login JSON is None. Please login first.")
            return False
        try:
            token = self.mt_profile.login_user_json.get("access_token")
        except Exception as e:
            self.utilities.log_error(f"Failed to get access token from profile JSON: {e}")
            return False
        headers = {"Authorization": f"Bearer {token}"}
        self.utilities.log_info(f"Creating ingredient: {ingredient_json}")
        response = self.client.post(f"{LOCALHOST}/ingredients/create_ingredient/", json=ingredient_json, headers=headers)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to create ingredient: {response.json()}")
            return response.json()
        return True

    def browse_ingredients(self):
        """Retrieve all ingredients."""
        if not self.mt_profile.login_user_json:
            self.utilities.log_error("Login JSON is None. Please login first.")
            return False
        try:
            token = self.mt_profile.login_user_json.get("access_token")
        except Exception as e:
            self.utilities.log_error(f"Failed to get access token from profile JSON: {e}")
            return False
        headers = {"Authorization": f"Bearer {token}"}
        self.utilities.log_info("Retrieving all ingredients")
        response = self.client.get(f"{LOCALHOST}/ingredients/browse", headers=headers)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to retrieve ingredients: {response.json()}")
            return response.json()
        self.all_ingredients = response.json().get("data")
        return self.all_ingredients
    
    def update_ingredient(self, ingredient_id: int, updates: dict):
        """Update an existing ingredient."""
        if not self.mt_profile.login_user_json:
            self.utilities.log_error("Login JSON is None. Please login first.")
            return False
        try:
            token = self.mt_profile.login_user_json.get("access_token")
        except Exception as e:
            self.utilities.log_error(f"Failed to get access token from profile JSON: {e}")
            return False
        headers = {"Authorization": f"Bearer {token}"}
        self.utilities.log_info(f"Updating ingredient ID {ingredient_id} with data: {updates}")
        response = self.client.patch(f"{LOCALHOST}/ingredients/{ingredient_id}", json=updates, headers=headers)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to update ingredient: {response.json()}")
            return response.json()
        return True
    
    def delete_ingredient(self, ingredient_id: int):
        """Delete an ingredient."""
        if not self.mt_profile.login_user_json:
            self.utilities.log_error("Login JSON is None. Please login first.")
            return False
        try:
            token = self.mt_profile.login_user_json.get("access_token")
        except Exception as e:
            self.utilities.log_error(f"Failed to get access token from profile JSON: {e}")
            return False
        headers = {"Authorization": f"Bearer {token}"}
        self.utilities.log_info(f"Deleting ingredient ID {ingredient_id}")
        response = self.client.delete(f"{LOCALHOST}/ingredients/{ingredient_id}", headers=headers)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to delete ingredient: {response.json()}")
            return response.json()
        return True
    
    def get_ingredient_id(self, ingredient_name: str):
        """Get the ID of an ingredient by name."""
        if not self.mt_profile.login_user_json:
            self.utilities.log_error("Login JSON is None. Please login first.")
            return False
        try:
            token = self.mt_profile.login_user_json.get("access_token")
        except Exception as e:
            self.utilities.log_error(f"Failed to get access token from profile JSON: {e}")
            return False
        headers = {"Authorization": f"Bearer {token}"}
        self.utilities.log_info(f"Retrieving ingredient details for name: {ingredient_name}")
        response = self.client.get(f"{LOCALHOST}/ingredients/id-by-name/{ingredient_name}", headers=headers)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to retrieve ingredient details: {response.json()}")
            return response.json()
        return response.json().get("id")
    
    def load_ingredient_data_from_file(self):
        """Load ingredient data from a JSON file."""
        try:
            with open(self.ingredient_json_path, 'r', encoding='utf-8') as file:
                ingredient_data = json.load(file)
                self.utilities.log_info(f"Loaded ingredient data from {self.ingredient_json_path}")
                return ingredient_data
        except Exception as e:
            self.utilities.log_error(f"Failed to load ingredient data from file: {e}")
            return None
        
    def create_ingredients_from_file(self):
        """Create multiple ingredients from a JSON file."""
        ingredient_data = self.load_ingredient_data_from_file()
        if not ingredient_data:
            return False
        for ingredient in ingredient_data:
            result = self.create_ingredient(ingredient)
            if result is not True:
                self.utilities.log_error(f"Failed to create ingredient from file data: {ingredient}")
        return True
    
    def search_ingredient_in_database(self, ingredient_name:str,type='normal',limit=10):
        if not self.mt_profile.login_user_json:
            self.utilities.log_error("Login JSON is None. Please login first.")
            return False
        try:
            token = self.mt_profile.login_user_json.get("access_token")
        except Exception as e:
            self.utilities.log_error(f"Failed to get access token from profile JSON: {e}")
            return False
        headers = {"Authorization": f"Bearer {token}"}
        self.utilities.log_info(f"Searching for ingredient: {ingredient_name}")
        params = {
            "querry": ingredient_name,
            "search_type": type,
            "limit": limit
        }
        response = self.client.get(f"{LOCALHOST}/ingredients/search", params=params, headers=headers)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to search ingredient: {response.json()}")
            return response.json()
        for item in response.json():
            if ingredient_name.lower() in item["name"].lower():
                self.utilities.log_info(f"Found ingredient: {item['name']}")
                return int(item["id"])
        return False
    
    def get_ingredient_by_id(self, ingredient_dict: dict):
        """Get ingredient details by ID."""
        ingredient_id = ingredient_dict.get("id")
        if not ingredient_id:
            self.utilities.log_error("Ingredient ID not provided in the dictionary.")
            return False
        if not self.mt_profile.login_user_json:
            self.utilities.log_error("Login JSON is None. Please login first.")
            return False
        try:
            token = self.mt_profile.login_user_json.get("access_token")
        except Exception as e:
            self.utilities.log_error(f"Failed to get access token from profile JSON: {e}")
            return False
        headers = {"Authorization": f"Bearer {token}"}
        self.utilities.log_info(f"Retrieving ingredient by ID: {ingredient_id}")
        response = self.client.get(f"{LOCALHOST}/ingredients/{ingredient_id}", headers=headers)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to retrieve ingredient: {response.json()}")
            return response.json()
        return response.json()

    def get_ingredient_usage_count(self, ingredient_id: int):
        """Get the usage count of an ingredient by name."""
        if not self.mt_profile.login_user_json:
            self.utilities.log_error("Login JSON is None. Please login first.")
            return False
        try:
            token = self.mt_profile.login_user_json.get("access_token")
        except Exception as e:
            self.utilities.log_error(f"Failed to get access token from profile JSON: {e}")
            return False
        headers = {"Authorization": f"Bearer {token}"}
        self.utilities.log_info(f"Retrieving usage count for ingredient: {ingredient_id}")
        response = self.client.get(f"{LOCALHOST}/ingredients/{ingredient_id}", headers=headers)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to retrieve ingredient usage count: {response.json()}")
            return response.json()
        usage_count = response.json().get("usage_count")
        return usage_count
    
    def get_ingredient_details(self, ingredient_id: int):
        """Get ingredient details by ID."""
        if not self.mt_profile.login_user_json:
            self.utilities.log_error("Login JSON is None. Please login first.")
            return False
        try:
            token = self.mt_profile.login_user_json.get("access_token")
        except Exception as e:
            self.utilities.log_error(f"Failed to get access token from profile JSON: {e}")
            return False
        headers = {"Authorization": f"Bearer {token}"}
        self.utilities.log_info(f"Retrieving ingredient details for ID: {ingredient_id}")
        response = self.client.get(f"{LOCALHOST}/ingredients/{ingredient_id}", headers=headers)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to retrieve ingredient details: {response.json()}")
            return response.json()
        return response.json()