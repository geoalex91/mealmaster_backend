import csv
from testing.keywords import DATA_PATH
from testing.keywords.utilities import Utilities
from fastapi.testclient import TestClient

LOCALHOST = "http://localhost:8000"
class MtProfile:
    def __init__(self, client: TestClient):
        self.client = client
        self.reader = self._load_users()
        self.utilities = Utilities()

    def _load_users(self):
        """Load users from the CSV file."""
        try:
            with open(f"{DATA_PATH}/users.csv", 'r', newline='', encoding='utf-8') as csvfile:
                return list(csv.reader(csvfile))
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found at {DATA_PATH}/users.csv")
        except Exception as e:
            raise RuntimeError(f"An error occurred while reading the CSV file: {e}")

    def create_profiles(self, num: int = 1):
        """Create a new user profile using the first user in the CSV file."""
        if not self.reader:
            raise ValueError("No users found in the CSV file.")

        user = self.reader[0]
        if len(user) < 3:
            raise ValueError("User data in the CSV file is incomplete.")
        for i in range(1,num):
            user_json = {"username": user[i],"email": user[i],"password": user[i]}
            self.utilities.log_info(f"Creating user: {user_json}")
            response = self.client.post(f"{LOCALHOST}/users/create_user", json=user_json)
            self.utilities.log_info(f"Response status code: {response.status_code}")
            if response.status_code != 200:
                return False
        return True
    
    def create_new_profile(self, username: str, email: str, password: str):
        """Create a new user profile using the first user in the CSV file."""
        
        user_json = {"username": username,"email": email,"password": password}
        self.utilities.log_info(f"Creating user: {user_json}")
        response = self.client.post(f"{LOCALHOST}/users/create_user", json=user_json)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code == 200:
            return True
        return response.json()