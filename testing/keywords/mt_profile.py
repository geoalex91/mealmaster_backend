import csv
from testing.keywords import DATA_PATH
from testing.keywords.utilities import Utilities, FakeEmailKeywords
from fastapi.testclient import TestClient
from resources.email_client import get_fake_email_client
from main import app

LOCALHOST = "http://localhost:8000"
class MtProfile:
    def __init__(self, client: TestClient):
        self.client = client
        self.reader = self._load_users()
        self.utilities = Utilities()
        self.fake_emal_client = get_fake_email_client()
        app.dependency_overrides = {
                "dependencies.get_email_client": get_fake_email_client}
        self.email_keywords = FakeEmailKeywords(self.fake_emal_client)
        self.login_user_json = None
    def _load_users(self):
        """Load users from the CSV file."""
        try:
            with open(f"{DATA_PATH}/users.csv", 'r', newline='', encoding='utf-8') as csvfile:
                return list(csv.reader(csvfile))
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found at {DATA_PATH}/users.csv")
        except Exception as e:
            raise RuntimeError(f"An error occurred while reading the CSV file: {e}")
    
    def get_verification_code(self, email: str):
        """Retrieve the last verification code sent to the specified email."""
        return self.email_keywords.get_last_verification_code(email)

    def verify_user(self, email: str, verification_code: str):
        """Verify a user using the verification code sent to their email."""
        if not verification_code:
            self.utilities.log_error(f"Failed to retrieve verification code for {email}")
            return False
        verify_json = {"email": email,"code": verification_code}
        self.utilities.log_info(f"Verifying user: {verify_json}")
        response = self.client.post(f"{LOCALHOST}/users/verify", params=verify_json)
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to verify user {email}: {response.json()}")
            return False
        return True
    
    def create_profiles(self, num: int = 1):
        """Create a new user profile using the first user in the CSV file."""
        if not self.reader:
            raise ValueError("No users found in the CSV file.")
        user = self.reader[0]
        if len(user) < 3:
            raise ValueError("User data in the CSV file is incomplete.")
        for i in range(1,num):
            user_json = {"username": user[i][0],"email": user[i][1],"password": user[i][2]}
            self.utilities.log_info(f"Creating user: {user_json}")
            self.fake_emal_client.clear()
            response = self.client.post(f"{LOCALHOST}/users/register", json=user_json)
            self.utilities.log_info(f"Response status code: {response.status_code}")
            if response.status_code != 200:
                continue
            else:
                return True
        return False
    
    def create_new_profile(self, username: str, email: str, password: str):
        """Create a new user profile using the first user in the CSV file."""
        
        user_json = {"username": username,"email": email,"password": password}
        self.utilities.log_info(f"Creating user: {user_json}")
        self.fake_emal_client.clear()
        response = self.client.post(f"{LOCALHOST}/users/register", json=user_json)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to create user {user_json}: {response.json()}")
        return response.json()
    
    def resend_verification(self,email: str):
        """Resend verification code to the user profile using the email."""
        
        user_json = {"email": email}
        self.utilities.log_info(f"Resending verification code to user: {email}")
        self.fake_emal_client.clear()
        response = self.client.post(f"{LOCALHOST}/users/resend-verification", params=user_json)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to resend verification code to user {user_json}: {response.json()}")
            return response.json()
        return True
    
    def login_user(self, username: str, password: str):
        """Login a user using the username and password."""
        login_data = {"username": username,"password": password}
        self.utilities.log_info(f"Logging in user: {username}")
        response = self.client.post(f"{LOCALHOST}/token", data=login_data)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to login user {username}: {response.json()}")
            return response.json()
        self.utilities.log_info(f"Login successful for user: {username}")
        self.login_user_json = response.json()
        return True
    
    def __get_info_from_login_json(self, login_json: dict, key: str):
        """Get information from the login JSON response."""
        if not login_json:
            self.utilities.log_error("Login JSON is None")
            return None
        return login_json.get(key, None)
    
    def change_password(self, username: str, old_password: str, new_password: str):
        """Change the password of a user using the token."""
        self.utilities.log_info(f"Changing password for user: {username}")
        if not self.login_user_json:
            self.utilities.log_error("Login JSON is None. Please login first.")
            return False
        try:
            json_username = self.__get_info_from_login_json(self.login_user_json, "username")
            if json_username != username:
                self.utilities.log_error(f"Logged in user {json_username} does not match the provided username {username}. Please login with the correct user.")
                return False
            token = self.__get_info_from_login_json(self.login_user_json, "access_token")
        except Exception as e:
            self.utilities.log_error(f"Failed to get access token from login JSON: {e}")
            return False
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.post(f"{LOCALHOST}/change-password", 
                                    params={"old_pasword": old_password, "new_password": new_password},
                                    headers=headers)
        self.utilities.log_info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to change password for user {username}: {response.json()}")
            return False
        self.utilities.log_info(f"Password changed successfully for user: {username}")
        return True
    
    def delete_account(self, username: str,password: str):
        """Delete the account of a user using the token."""
        if not self.login_user_json:
            self.utilities.log_error("Login JSON is None. Please login first.")
            return False
        try:
            json_username = self.__get_info_from_login_json(self.login_user_json, "username")
            if json_username != username:
                self.utilities.log_error(f"Logged in user {json_username} does not match the provided username {username}. Please login with the correct user.")
                return False
            token = self.__get_info_from_login_json(self.login_user_json, "access_token")
        except Exception as e:
            self.utilities.log_error(f"Failed to get access token from login JSON: {e}")
            return False
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.delete(f"{LOCALHOST}/delete-account", params={"password": password},headers=headers)
        if response.status_code != 200:
            self.utilities.log_error(f"Failed to delete account for user {username}: {response.json()}")
            return response.json()
        self.utilities.log_info(f"Account deleted successfully for user: {username}")
        return True
    

