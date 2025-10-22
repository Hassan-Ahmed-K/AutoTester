# logger.py
import os
import traceback
from datetime import datetime
from dotenv import load_dotenv
from PyQt5.QtWidgets import QMessageBox, QApplication
import sys

load_dotenv()

class Logger:
    # Primary path from .env
    LOG_FILE = os.getenv("LOG_FILE")

    # Backup path if env not set or invalid
    BACKUP_LOG_FILE = os.path.join("data", "logs", "logs.txt")

    @staticmethod
    def _ensure_log_file():
        """Ensure a valid log file path exists, fallback to backup."""
        log_file = Logger.LOG_FILE

        if not log_file:  # If not set in env
            log_file = Logger.BACKUP_LOG_FILE

        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)  # auto-create

        return log_file

    @staticmethod
    def _write_log(level: str, message: str):
        """Internal log writer with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"

        log_file = Logger._ensure_log_file()

        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            Logger._show_popup(f"Failed to write log: {e}")
            raise

        # Also print to console
        print(log_entry, end="")

    @staticmethod
    def _show_popup(message: str):
        """Show PyQt popup with error message"""
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
            temp_app = True
        else:
            temp_app = False

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Logger Error")
        msg.setText(message)
        msg.exec_()

        if temp_app:
            sys.exit(1)

    @staticmethod
    def info(message: str):
        Logger._write_log("INFO", message)

    @staticmethod
    def success(message: str):
        Logger._write_log("SUCCESS", f"✅ {message}")

    @staticmethod
    def error(message: str, exc: Exception = None):
        """Logs an error safely, handling both string and Exception inputs."""
        try:
            if exc:
                # Handle both real Exception and string cases gracefully
                if isinstance(exc, Exception):
                    tb = traceback.extract_tb(exc.__traceback__)[-1]
                    filename = os.path.basename(tb.filename)
                    line_no = tb.lineno
                    error_type = type(exc).__name__
                    error_msg = f"{message} | {error_type}: {exc} (File: {filename}, Line: {line_no})"
                else:
                    # If exc is a string or non-exception object
                    error_msg = f"{message} | Details: {exc}"
            else:
                error_msg = message

            Logger._write_log("ERROR", error_msg)

        except Exception as log_exc:
            # Fallback in case logging itself fails
            print(f"[LOGGER ERROR] Failed to log error: {log_exc}")
            print(f"[LOGGER ERROR] Original message: {message}")
            if exc:
                print(f"[LOGGER ERROR] Original exception: {exc}")

                

    @staticmethod
    def debug(message: str):
        Logger._write_log("DEBUG", message)

    @staticmethod
    def warning(message: str):
        Logger._write_log("WARNING", message)