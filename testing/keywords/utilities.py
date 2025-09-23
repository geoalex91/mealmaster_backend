from datetime import datetime

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