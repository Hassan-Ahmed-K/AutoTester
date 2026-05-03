import json
import os
from datetime import datetime, timedelta
from aiagentfinder.utils.logger import Logger

SESSION_FILE = "session.json"
CONFIG_FILE = "config.properties"

def get_session_timeout():
    """
    Reads session timeout from config.properties. Default is 1440 minutes.
    Format: session_timeout_minutes=1440
    """
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith("#") or line.startswith("!"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        if key.strip() == "SESSION_TIMEOUT_MINUTES":
                            return int(value.strip())
    except Exception as e:
        Logger.error(f"Error reading {CONFIG_FILE}: {e}")
    return 1440



# ==============================
# SAVE SESSION
# ==============================
def save_session(data):
    """
    Saves session data with an expiration time.
    """
    try:
        session_data = data.copy()
        # Add or update expiry
        timeout_mins = get_session_timeout()
        session_data["expires_at"] = (datetime.now() + timedelta(minutes=timeout_mins)).isoformat()


        with open(SESSION_FILE, "w") as f:
            json.dump(session_data, f)
        Logger.info(f"Session saved successfully to {SESSION_FILE}")
        return True
    except Exception as e:
        Logger.error(f"Error saving session: {e}")
        return False


# ==============================
# LOAD SESSION
# ==============================
def load_session():
    """
    Loads session data from the file.
    """
    if not os.path.exists(SESSION_FILE):
        return None

    try:
        with open(SESSION_FILE, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        Logger.error(f"Error loading session: {e}")
        return None


# ==============================
# CHECK VALID SESSION
# ==============================
def is_session_valid():
    """
    Checks if the session is still valid (not expired).
    Returns the data if valid, False otherwise.
    """
    data = load_session()

    if not data:
        return False

    try:
        expiry = datetime.fromisoformat(data["expires_at"])
        if datetime.now() < expiry:
            return data   # valid session
        else:
            Logger.info("Session expired, cleaning up.")
            clear_session()  # auto cleanup expired
            return False
    except Exception as e:
        Logger.error(f"Error validating session: {e}")
        clear_session()
        return False


# ==============================
# LOGOUT (CLEAR SESSION)
# ==============================
def clear_session():
    """
    Deletes the session file.
    """
    try:
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
            Logger.info("Session file cleared.")
            return True
        return False
    except Exception as e:
        Logger.error(f"Error clearing session: {e}")
        return False
