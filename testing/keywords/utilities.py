from datetime import datetime
from resources.email_client import FakeEmailClient
class Utilities:
    def __init__(self):
        pass
    
    def _log_message(self, message: str, level: str = "INFO") -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{now}] [{level.upper()}] {message}"
        print(log_line)
    
    def log_info(self, message: str) -> None:
        self._log_message(message, "INFO")

    def log_warning(self, message: str) -> None:
        self._log_message(message, "WARNING")
    
    def log_error(self, message: str) -> None:
        self._log_message(message, "ERROR")

class FakeEmailKeywords:
    def __init__(self):
        self.client = FakeEmailClient().get_instance()
        self.last_code = None

    def _handle_email(self, email):
        if "Verification Code" in email["subject"]:
            self.last_code = email["body"].split()[-1]

    def send_fake_email(self, subject, recipient, body):
        self.client.clear()
        return self.client.send_email(subject, recipient, body)

    def get_last_verification_code(self, email: str):
        last_email = self.client.get_last_email(recipient=email)
        if last_email and "Verification Code" in last_email["subject"]:
            self._handle_email(last_email)
        return self.last_code