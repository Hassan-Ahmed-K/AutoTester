import re
import uuid
import json
import os
import time
import keyring
from dotenv import load_dotenv
from PyQt5.QtWidgets import QMessageBox
from aiagentfinder.utils.logger import Logger
from aiagentfinder.utils.workerThread import ThreadRunner

load_dotenv()
class HomeController:
    def __init__(self, ui):
        self.ui = ui
        self.runner = ThreadRunner()
        self.main_window = self.ui.parent()
        self.SERVICE_NAME = os.getenv("SERVICE_NAME")
        self.CACHE_KEY = os.getenv("CACHE_KEY")
        self.check_login()

        self.ui.signin_btn.clicked.connect(self.handle_login)
        self.ui.logout_btn.clicked.connect(self.handle_logout)

    def save_cache(self, data: dict):
        keyring.set_password(self.SERVICE_NAME, self.CACHE_KEY, json.dumps(data))
    
    def load_cache(self):
        data_str = keyring.get_password(self.SERVICE_NAME, self.CACHE_KEY)
        if data_str:
            return json.loads(data_str)
        return None

    def is_email_valid(self, email):
        return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email)

    def is_password_valid(self, password):
        return len(password) >= 6

    def generate_token(self):
        return str(uuid.uuid4())


    # def handle_login(self):
    #     print("Login button clicked")
    #     email = self.ui.email.text()
    #     password = self.ui.password.text()

    #     if not self.is_email_valid(email):
    #         QMessageBox.warning(self.ui, "Invalid Email", "Please enter a valid email address.")
    #         Logger.warning(f"Invalid email: {email}")
    #         return

    #     if not self.is_password_valid(password):
    #         QMessageBox.warning(self.ui, "Invalid Password", "Password must be at least 6 characters.")
    #         Logger.warning(f"Invalid password for email: {email}")
    #         return

       
    #     if email == "admin@example.com" and password == "123456":
    #         token = self.generate_token()
    #         cache_data = {
    #             "authenticated": True,
    #             "token": token,
    #             "validation_time": time.time(),
    #         }
    #         self.save_cache(cache_data)
    #         QMessageBox.information(self.ui, "Success", "Login successful!")
    #         Logger.info(f"User {email} logged in successfully.")
    #         self.main_window.authenticated = True
    #         self.check_login()

    #     else:
    #         QMessageBox.critical(self.ui, "Login Failed", "Invalid email or password.")
    #         Logger.warning(f"Failed login attempt for email: {email}")
    #         return False
    def handle_login(self):
        print("Login button clicked")
        email = self.ui.email.text()
        password = self.ui.password.text()

        if not self.is_email_valid(email):
            QMessageBox.warning(self.ui, "Invalid Email", "Please enter a valid email address.")
            Logger.warning(f"Invalid email: {email}")
            return

        if not self.is_password_valid(password):
            QMessageBox.warning(self.ui, "Invalid Password", "Password must be at least 6 characters.")
            Logger.warning(f"Invalid password for email: {email}")
            return

        def task():
            # simulate authentication (replace this with real API call later)
            if email == "admin@example.com" and password == "123456":
                token = self.generate_token()
                cache_data = {
                    "authenticated": True,
                    "token": token,
                    "validation_time": time.time(),
                }
                self.save_cache(cache_data)
                Logger.info(f"User {email} logged in successfully.")
                return cache_data
            else:
                Logger.warning(f"Failed login attempt for email: {email}")
                raise ValueError("Invalid email or password")

        def on_done(cache_data):
            QMessageBox.information(self.ui, "Success", "Login successful!")
            self.main_window.authenticated = True
            self.ui.notice_label.show()
            self.ui.login_widget.hide()
            self.ui.logout.show()
            Logger.info("User interface updated after login")

        def on_error(err):
            Logger.error("Login failed", err)
            QMessageBox.critical(self.ui, "Login Failed", "Invalid email or password.")

        # --- Run async thread ---
        self.runner = ThreadRunner()
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task)

    # def handle_logout(self):
    #     Logger.info("Logging out...")

    #     try:
    #         keyring.delete_password(self.SERVICE_NAME, self.CACHE_KEY)
    #         Logger.info("Keyring cache deleted")
    #     except keyring.errors.PasswordDeleteError:
    #         Logger.info("No cache found in keyring")

    #     self.main_window.authenticated = False
    #     self.check_login()
    #     Logger.info("User logged out")
    #     QMessageBox.information(self.ui, "Logged Out", "You have been logged out.")
    def handle_logout(self):
        Logger.info("Logging out...")

        def task():
            try:
                keyring.delete_password(self.SERVICE_NAME, self.CACHE_KEY)
                Logger.info("Keyring cache deleted")
                return True
            except keyring.errors.PasswordDeleteError:
                Logger.info("No cache found in keyring")
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
            if data and data.get("authenticated") and time.time() - data["validation_time"] < 3600:
                Logger.info("User authenticated via cache")
                self.main_window.authenticated = True
                self.ui.notice_label.show()
                self.ui.login_widget.hide()
            else:
                Logger.info("No valid cache found, user not authenticated")
                self.main_window.authenticated = False
                self.ui.notice_label.hide()
                self.ui.login_widget.show()

        def on_error(e):
            Logger.error("Error loading cache", e)
            self.ui.notice_label.hide()
            self.ui.login_widget.show()

        self.runner = ThreadRunner()
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task, show_dialog=False)

    def check_login(self):
        if self.check_cache():
            self.ui.notice_label.show()
            self.ui.login_widget.hide()
            self.ui.logout.show()
        else:
           self.ui.notice_label.hide()
           self.ui.login_widget.show()
           self.ui.logout.hide()
            
