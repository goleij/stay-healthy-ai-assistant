# auth/auth_logic.py
import re
import bcrypt
from storage.profile_manager import load_users, save_users

# email validation pattern
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def signup_user(username: str, email: str, password: str):
    """Create a new user with basic validation."""
    username = username.strip()
    email = email.strip().lower()
    password = password.strip()

    # Basic non-empty check
    if not username or not email or not password:
        return False, "Please fill all fields."

    # Basic username length rule
    if len(username) < 3:
        return False, "Username must be at least 3 characters long."

    # Validate email format
    if not EMAIL_REGEX.match(email):
        return False, "Please enter a valid email address."

    users = load_users()

    # Check if username already exists
    if username in users:
        return False, "Username already exists."

    # Check if email already used
    for u in users.values():
        if u.get("email", "").lower() == email:
            return False, "Email is already registered."

    # Hash password
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    users[username] = {"email": email, "password": hashed}
    save_users(users)
    return True, "Signup successful. You can now log in."


def login_user(identifier: str, password: str):
    """Login using username or email."""
    identifier = identifier.strip()
    password = password.strip()
    users = load_users()

    username = None
    user = None

    # Try identifier as username
    if identifier in users:
        username = identifier
        user = users[username]
    else:
        # Try identifier as email
        for uname, data in users.items():
            if data.get("email", "").lower() == identifier.lower():
                username = uname
                user = data
                break

    if user is None:
        return False, "User not found.", None

    # Check password against stored hash
    if not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
        return False, "Incorrect password.", None

    return True, "Login successful.", username
