from mt_profile import MtProfile
from fastapi.testclient import TestClient
from main import app

class MealTracker:
    
    def __init__(self):
        self.client = TestClient(app)
        self.mt_profile = MtProfile(self.client)

    def create_new_user(self):
        return self.mt_profile.create_new_profile()
