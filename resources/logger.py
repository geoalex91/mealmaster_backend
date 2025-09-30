from datetime import datetime
import os
import threading

class Logger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self, log_dir: str = "logs",debug = True) -> None:
        if getattr(self, "_initialized", False):
            # Check if the day changed → rotate log file
            today = datetime.now().strftime("%Y%m%d")
            if today != self._current_day:
                self._rotate_log_file(log_dir)
            return
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)

        # Create first logfile
        self._current_day = datetime.now().strftime("%Y%m%d")
        self.logfile = os.path.join(log_dir, f"app_{self._current_day}.log")

        self.debug = debug
        self._initialized = True

        self.log("INFO", f"--- New logging session started: {self.logfile} ---")

    def _rotate_log_file(self, log_dir: str):
        """Create a new log file when the date changes."""
        self._current_day = datetime.now().strftime("%Y%m%d")
        self.logfile = os.path.join(log_dir, f"app_{self._current_day}.log")
        self.log("INFO", f"--- Log rotated: {self.logfile} ---")

    def log(self, level: str, message: str) -> None:
        if self.debug is False:
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{now}] [{level.upper()}] {message}"

        # Print to console
        print(log_line)

        # Append to session log file
        with open(self.logfile, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")

    # Convenience methods
    def info(self, message: str) -> None:
        self.log("INFO", message)

    def warning(self, message: str) -> None:
        self.log("WARNING", message)

    def error(self, message: str) -> None:
        self.log("ERROR", message)
