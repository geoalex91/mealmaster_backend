import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from resources.logger import Logger
from typing import List, Dict


class EmailClient:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SMTP_USER", "codemaster9123@gmail.com")
        self.sender_password = os.getenv("SMTP_PASSWORD")
        self.logger = Logger.get_instance()

    def send_email(self, subject: str, recipient: str, body: str):
        try:
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
        except Exception as e:
            self.logger.error(f"Failed to send email to {recipient}: {e}")

class FakeEmailClient:
    _instance = None
    def __init__(self):
        if FakeEmailClient._instance is not None:
            raise RuntimeError("Use FakeEmailClient.get_instance() instead of creating directly")
        self._sent_emails: List[Dict] = []

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = FakeEmailClient()
        return cls._instance

    def send_email(self, subject: str, recipient: str, body: str):
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

#dependency injection
def get_email_client():
    """Default provider for production"""
    return EmailClient()

def get_fake_email_client():
    """Provider for testing"""
    return FakeEmailClient.get_instance()