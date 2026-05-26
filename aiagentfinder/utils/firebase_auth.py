import firebase_admin
from firebase_admin import credentials, firestore
import bcrypt
import os

from .paths import get_external_path

# ==============================
# INIT FIREBASE
# ==============================
# firebaseCredential.json is an EXTERNAL file placed next to the EXE,
# NOT bundled inside the PyInstaller archive.
cred_path = get_external_path("firebaseCredential.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()


# ==============================
# HELPER: GET USER
# ==============================
def get_user(username):
    doc = db.collection("UserCredentials").document(username).get()
    return doc.to_dict() if doc.exists else None


# ==============================
# CHECK IF USER EXISTS
# ==============================
def user_exists(username):
    return get_user(username) is not None


# ==============================
# CREATE USER (SIGNUP)
# ==============================
def create_user(username, password):
    if user_exists(username):
        return {
            "status": False,
            "message": "User already exists"
        }

    # Hash password
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    # Save user
    db.collection("UserCredentials").document(username).set({
        "username": username,
        "password": hashed_pw
    })

    return {
        "status": True,
        "message": "User created successfully"
    }


# ==============================
# LOGIN USER (VERIFY)
# ==============================
def login_user(username, password):
    user = get_user(username)

    if not user:
        return {
            "status": False,
            "message": "User not found"
        }

    stored_hash = user["password"].encode()

    if bcrypt.checkpw(password.encode(), stored_hash):
        return {
            "status": True,
            "message": "Login successful"
        }
    else:
        return {
            "status": False,
            "message": "Invalid password"
        }
