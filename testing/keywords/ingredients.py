from testing.keywords import DATA_PATH
from testing.keywords.utilities import Utilities
from fastapi.testclient import TestClient
from resources.email_client import
from main import app

LOCALHOST = "http://localhost:8000"
class MTIngredients:
    def __init__(self, client: TestClient):
        self.client = client
        self.utilities = Utilities()
    
    def create_ingredient(self, token: str, ingredient_data: dict):
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
        headers = {"Authorization": f"Bearer {token}"}
        self.utilities.log_info(f"Creating ingredient: {ingredient_json}")
        response = self.client.post(f"{LOCALHOST}/ingredients/", json=ingredient_json, headers=headers)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to create ingredient: {response.json()}")
            return response.json()
        return True

    def get_all_ingredients(self, token: str):
        """Retrieve all ingredients."""
        headers = {"Authorization": f"Bearer {token}"}
        self.utilities.log_info("Retrieving all ingredients")
        response = self.client.get(f"{LOCALHOST}/ingredients/all", headers=headers)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to retrieve ingredients: {response.json()}")
            return response.json()
        return response.json()
    
    def update_ingredient(self, token: str, ingredient_id: int, updates: dict):
        """Update an existing ingredient."""
        headers = {"Authorization": f"Bearer {token}"}
        self.utilities.log_info(f"Updating ingredient ID {ingredient_id} with data: {updates}")
        response = self.client.patch(f"{LOCALHOST}/ingredients/{ingredient_id}", json=updates, headers=headers)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to update ingredient: {response.json()}")
            return response.json()
        return True
    
    def delete_ingredient(self, token: str, ingredient_id: int):
        """Delete an ingredient."""
        headers = {"Authorization": f"Bearer {token}"}
        self.utilities.log_info(f"Deleting ingredient ID {ingredient_id}")
        response = self.client.delete(f"{LOCALHOST}/ingredients/{ingredient_id}", headers=headers)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to delete ingredient: {response.json()}")
            return response.json()
        return True