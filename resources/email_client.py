import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from resources.logger import Logger
from typing import List, Dict
import threading
from dns import resolver

class FakeEmailClient:
    _instance = None
    _lock = threading.Lock()
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(FakeEmailClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._sent_emails: List[Dict] = []
        self._initialized = True

    def _validate_email_domain(self,email: str):
        domain = email.split("@")[-1]
        try:
            resolver.resolve(domain, "MX")
            return True
        except Exception:
            return False

    def send_email(self, subject: str, recipient: str, body: str):
        if not self._validate_email_domain(recipient):
            return {"status": "failed", "reason": "Invalid email domain"}
        email = {
            "subject": subject,
            "recipient": recipient,
            "body": body,
        }
        self._sent_emails.append(email)
        return {"status": "fake-sent"}

    def get_last_email(self, recipient: str) -> Dict | None:
        for email in reversed(self._sent_emails):
            if email["recipient"] == recipient:
                return email
        return None

    def clear(self):
        self._sent_emails.clear()

class EmailClient():
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SMTP_USER", "codemaster9123@gmail.com")
        self.sender_password = os.getenv("SMTP_PASSWORD")
        self.logger = Logger()

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._sent_emails: List[Dict] = []
        self._initialized = True

    def _validate_email_domain(self,email: str):
        domain = email.split("@")[-1]
        try:
            resolver.resolve(domain, "MX")
            return True
        except Exception:
            return False
    def send_email(self, subject: str, recipient: str, body: str):
        try:
            if not self._validate_email_domain(recipient):
                return {"status": "failed", "reason": "Invalid email domain"}
            # Create message
            message = MIMEMultipart()
            message["From"] = self.sender_email
            message["To"] = recipient
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain"))

            # Connect and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient, message.as_string())

            self.logger.info(f"Email sent to {recipient} with subject: {subject}")
        except smtplib.SMTPRecipientsRefused:
            return {"status": "failed", "reason": "Recipient address refused"}
        except Exception as e:
            self.logger.error(f"Failed to send email to {recipient}: {e}")
            return {"status": "failed", "reason": str(e)}
        return {"status": "sent"}

#dependency injection
def get_email_client():
    """Default provider for production"""
    return EmailClient()

def get_fake_email_client():
    """Provider for testing"""
    return FakeEmailClient()