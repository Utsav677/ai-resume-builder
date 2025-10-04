"""Configuration for LangGraph Studio"""
from .database import SessionLocal
from .models import User

def get_default_user_id():
    """Get the test user ID for Studio"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "testuser@example.com").first()
        if user:
            return user.user_id
        else:
            raise ValueError("Test user not found. Run test_auth.py first!")
    finally:
        db.close()

# Set default user for Studio
DEFAULT_USER_ID = get_default_user_id()
