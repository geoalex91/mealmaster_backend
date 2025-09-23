from datetime import datetime
import os
import threading

class Logger:
    _instance = None
    _lock = threading.Lock()

    def __init__(self, log_dir: str = "logs",debug = True) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)

        # Create a unique log file for this session
        session_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logfile = os.path.join(log_dir, f"session_{session_time}.log")
        self._initialized = True
        self.debug = debug
        # Optionally, write session start header
        self.log("INFO", f"--- New logging session started: {self.logfile} ---")
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # double-checked locking
                    cls._instance = cls()
        return cls._instance

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
