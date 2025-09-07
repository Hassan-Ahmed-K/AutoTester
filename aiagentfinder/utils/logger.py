# logger.py
import os
import traceback
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
class Logger:
    LOG_FILE = os.getenv("LOG_FILE")

    @staticmethod
    def _write_log(level: str, message: str):
        """Internal log writer with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"

        # Ensure log.txt exists in the same folder
        if Logger.LOG_FILE is None:
            raise ValueError("LOG_FILE environment variable is not set.")
        with open(Logger.LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)

        # Also print to console
        print(log_entry, end="")

    @staticmethod
    def info(message: str):
        Logger._write_log("INFO", message)

    @staticmethod
    def success(message: str):
        Logger._write_log("SUCCESS", f"✅ {message}")

    @staticmethod
    def error(message: str, exc: Exception = None):
        """Logs an error, with optional exception details (file + line)."""
        if exc:
            tb = traceback.extract_tb(exc.__traceback__)[-1]  # last call in traceback
            filename = os.path.basename(tb.filename)
            line_no = tb.lineno
            error_type = type(exc).__name__
            error_msg = f"{message} | {error_type}: {exc} (File: {filename}, Line: {line_no})"
        else:
            error_msg = message

        Logger._write_log("ERROR", error_msg)

    @staticmethod
    def debug(message: str):
        Logger._write_log("DEBUG", message)
    @staticmethod
    def warning(message: str):
        Logger._write_log("WARNING",message)
