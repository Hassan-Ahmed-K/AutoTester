import re
import os
import time
from dotenv import load_dotenv
from PyQt5.QtWidgets import QMessageBox
from aiagentfinder.utils.logger import Logger
from aiagentfinder.utils.workerThread import ThreadRunner
from aiagentfinder.utils.firebase_auth import login_user
from aiagentfinder.utils.session_manager import save_session, is_session_valid, clear_session

load_dotenv()
class HomeController:
    def __init__(self, ui):
        self.ui = ui
        self.runner = ThreadRunner()
        self.main_window = self.ui.parent()
        self.check_cache()

        self.ui.signin_btn.clicked.connect(self.handle_login)
        self.ui.logout_btn.clicked.connect(self.handle_logout)


    def save_cache(self, data: dict):
        """Safely save cache data to session file."""
        if save_session(data):
            Logger.info("Cache saved successfully to session file.")
        else:
            Logger.error("Failed to save cache to session file.")


    def load_cache(self):
        """Safely load cache data from session file."""
        try:
            data = is_session_valid()
            if data:
                Logger.info("Valid session found and loaded.")
                return data
            else:
                Logger.warning("No valid session found.")
                return None
        except Exception as e:
            Logger.error("Failed to load cache from session file", e)
            return None


    def is_email_valid(self, email):
        return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email)

    def is_password_valid(self, password):
        return len(password) >= 6

    def handle_login(self):
        print("Login button clicked")
        email = self.ui.email.text()
        password = self.ui.password.text()

        print(email, password)

        if not self.is_email_valid(email):
            QMessageBox.warning(self.ui, "Invalid Email", "Please enter a valid email address.")
            Logger.warning(f"Invalid email: {email}")
            return

        if not self.is_password_valid(password):
            QMessageBox.warning(self.ui, "Invalid Password", "Password must be at least 6 characters.")
            Logger.warning(f"Invalid password for email: {email}")
            return

        def task():
            result = login_user(email, password)
            
            if result.get("status"):
                cache_data = {
                    "authenticated": True,
                    "validation_time": time.time(),
                    "email": email
                }
                self.save_cache(cache_data)
                Logger.info(f"User {email} logged in successfully via Firebase Admin SDK.")
                return cache_data
            else:
                error_message = result.get("message", "Unknown error")
                Logger.warning(f"Failed login attempt for email {email}: {error_message}")
                raise ValueError(error_message)

        def on_done(cache_data):
            QMessageBox.information(self.ui, "Success", "Login successful!")
            self.main_window.authenticated = True
            self.ui.notice_label.show()
            self.ui.login_widget.hide()
            self.ui.logout.show()
            Logger.info("User interface updated after login")

        def on_error(err):
            Logger.error("Login failed", err)
            QMessageBox.critical(self.ui, "Login Failed", str(err))

        # --- Run async thread ---
        self.runner = ThreadRunner()
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task)

    def handle_logout(self):
        Logger.info("Logging out...")

        def task():
            try:
                clear_session()
                Logger.info("Session file cleared.")
                return True
            except Exception as e:
                Logger.error(f"Error clearing session: {e}")
                return False

        def on_done():
            self.main_window.authenticated = False
            # Update UI directly
            self.ui.notice_label.hide()
            self.ui.login_widget.show()
            self.ui.logout.hide()
            Logger.info("User logged out")
            QMessageBox.information(self.ui, "Logged Out", "You have been logged out.")

        def on_error(e):
            Logger.error("Error during logout", e)
            QMessageBox.critical(self.ui, "Error", f"An error occurred during logout:\n{e}")

        self.runner = ThreadRunner()
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task)
        
    def check_cache(self):
        def task():
            data = self.load_cache()
            Logger.info(f"Cache loaded: {data}")
            return data

        def on_done(data):
            if data:
                Logger.info("User authenticated via cache")
                self.main_window.authenticated = True
                self.ui.notice_label.show()
                self.ui.login_widget.hide()
                self.ui.logout.show()
            else:
                Logger.info("No valid cache found, user not authenticated")
                self.main_window.authenticated = False
                self.ui.notice_label.hide()
                self.ui.login_widget.show()
                self.ui.logout.hide()

        def on_error(e):
            Logger.error("Error loading cache", e)
            self.ui.notice_label.hide()
            self.ui.login_widget.show()

        self.runner = ThreadRunner()
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task, show_dialog=False)
