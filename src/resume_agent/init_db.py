"""Initialize database tables"""
import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.resume_agent.database import engine, Base
from src.resume_agent.models import User, UserProfile, ResumeGeneration, ConversationThread


def init_database():
    """Create all tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_database()