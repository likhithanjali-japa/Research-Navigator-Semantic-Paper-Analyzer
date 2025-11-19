# backend/auth_utils.py

from backend.database import users
from datetime import datetime
import bcrypt

def register_user(name, email, password, institution=None, research=None):

    # Check if exists
    existing = users.find_one({"email": email})
    if existing:
        return {"error": "User already exists"}

    # Hash password
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    doc = {
        "name": name,
        "email": email,
        "password": hashed_pw,
        "institution": institution,
        "research": research,
        "created_at": datetime.utcnow()
    }

    # Insert into DB
    result = users.insert_one(doc)

    # Add _id AFTER insert
    doc["_id"] = str(result.inserted_id)

    # Remove password before returning
    doc.pop("password", None)

    return {"data": doc}


def login_user(email, password):

    user = users.find_one({"email": email})
    if not user:
        return {"error": "Invalid email or password"}, 401

    stored_hash = user["password"].encode()

    if not bcrypt.checkpw(password.encode(), stored_hash):
        return {"error": "Invalid email or password"}, 401

    # Clean output
    user["_id"] = str(user.get("_id"))
    user.pop("password", None)

    return {"data": user}
