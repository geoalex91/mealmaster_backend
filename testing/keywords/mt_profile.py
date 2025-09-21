import csv
from testing.keywords import DATA_PATH
from fastapi.testclient import TestClient

class MtProfile:
    def __init__(self, client: TestClient):
        self.client = client
        with open(f"{DATA_PATH}\\users.csv", 'r') as csvfile:
            self.reader = list(csv.reader(csvfile))
            

    def create_new_profile(self):
        user = self.reader[0]
        user_json = {"user": user[0], "email": user[1], "hashed_password": user[2]}
        response = self.client.post("/users", json=user_json)
        if response.status_code == 200:
            return True
        else:
            return False