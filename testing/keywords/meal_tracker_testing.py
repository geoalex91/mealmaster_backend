from mt_profile import MtProfile
from fastapi.testclient import TestClient
from main import app

class MealTracker:
    def __init__(self):
        # Initialize the TestClient with the FastAPI app
        self.client = TestClient(app)
        # Initialize the MtProfile instance with the TestClient
        self.mt_profile = MtProfile(self.client)

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
    
