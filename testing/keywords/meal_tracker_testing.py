from mt_profile import MtProfile
from fastapi.testclient import TestClient
from main import app

class MealTracker:
    def __init__(self):
        # Initialize the TestClient with the FastAPI app
        self.client = TestClient(app)
        # Initialize the MtProfile instance with the TestClient
        self.mt_profile = MtProfile(self.client)

    def create_new_user(self):
        # Delegate the creation of a new profile to the MtProfile instance
        return self.mt_profile.create_new_profile()
