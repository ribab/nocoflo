import sqlite3
import bcrypt
from nicegui import app
from typing import Optional, Dict

import metadata

def verify_password(password: str, hash: str) -> bool:
    """
    Verify password against hash
    
    Args:
        password: Plain text password
        hash: Hashed password
        
    Returns:
        True if password matches hash, False otherwise
    """
    return bcrypt.checkpw(password.encode(), hash.encode())

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def authenticate_user(email: str, password: str) -> Optional[Dict]:
    """
    Authenticate a user with email and password
    
    Args:
        email: User's email address
        password: User's password
        
    Returns:
        User dictionary if authentication successful, None otherwise
    """
    user = metadata.get_user_by_email(email)
    if user and verify_password(password, user['password_hash']):
        return user
    return None

def login_user(user: Dict) -> None:
    """
    Log in a user by setting session data
    
    Args:
        user: User dictionary with user data
    """
    # Clear existing session
    for k in list(app.storage.user):
        del app.storage.user[k]
    
    # Set new session data
    for k, v in user.items():
        app.storage.user[k] = v

def logout_user() -> None:
    """Log out the current user by clearing session data"""
    for k in list(app.storage.user):
        del app.storage.user[k]

def is_authenticated() -> bool:
    """
    Check if user is currently authenticated
    
    Returns:
        True if user is logged in, False otherwise
    """
    return bool(app.storage.user)

def get_current_user() -> Optional[Dict]:
    """
    Get the current authenticated user
    
    Returns:
        User dictionary if authenticated, None otherwise
    """
    if is_authenticated():
        return dict(app.storage.user)
    return None

def require_auth():
    """
    Decorator to require authentication for a page
    
    Usage:
        @require_auth
        def my_page():
            # Page content
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not is_authenticated():
                app.navigate.to('/login')
                return
            return func(*args, **kwargs)
        return wrapper
    return decorator 