from mt_profile import MtProfile
from fastapi.testclient import TestClient
from testing.keywords.mt_ingredients import MTIngredients
from main import app

class MealTracker:
    def __init__(self):
        # Initialize the TestClient with the FastAPI app
        self.client = TestClient(app)
        # Initialize the MtProfile instance with the TestClient
        self.mt_profile = MtProfile(self.client)
        self.mt_ingredients = MTIngredients(self.client,self.mt_profile)

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
        mt_ingredients = MTIngredients(self.client)
        return mt_ingredients.create_ingredient(ingredient_data)
    
    def get_all_ingredients(self):
        # Import MTIngredients here to avoid circular import issues
        mt_ingredients = MTIngredients(self.client)
        return mt_ingredients.get_all_ingredients()
    
    def update_ingredient(self, ingredient_id: int, updates: dict):
        # Import MTIngredients here to avoid circular import issues
        mt_ingredients = MTIngredients(self.client)
        return mt_ingredients.update_ingredient(ingredient_id, updates)
    
    def delete_ingredient(self, ingredient_id: int):
        # Import MTIngredients here to avoid circular import issues
        mt_ingredients = MTIngredients(self.client)
        return mt_ingredients.delete_ingredient(ingredient_id)
    
    def get_ingredient_id(self, ingredient_name: str):
        # Import MTIngredients here to avoid circular import issues
        mt_ingredients = MTIngredients(self.client)
        return mt_ingredients.get_ingredient_id(ingredient_name)
