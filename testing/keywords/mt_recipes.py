from testing.keywords import DATA_PATH
from testing.keywords.utilities import Utilities
from fastapi.testclient import TestClient
from main import app
from mt_profile import MtProfile

LOCALHOST = "http://localhost:8000"

class MTRecipes:
    def __init__(self, client: TestClient, mt_profile: MtProfile):
        self.client = client
        self.utilities = Utilities()
        self.data_path = DATA_PATH
        self.mt_profile = mt_profile

    def get_recipe(self, recipe_id: int):
        response = self.client.get(f"{LOCALHOST}/recipes/{recipe_id}")
        return response.json()

    def create_recipe(self, recipe_data: dict):
        recipes_json = {
            "name": recipe_data.get("name"),
            "description": recipe_data.get("description"),
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
    