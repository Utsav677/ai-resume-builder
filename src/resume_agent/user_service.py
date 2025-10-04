"""User management service"""
from sqlalchemy.orm import Session
from typing import Optional
from .models import User, UserProfile
from .schemas import UserCreate, UserProfileSchema
from .auth import get_password_hash, verify_password, create_access_token
import json


class UserService:
    """Handle user operations"""
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            hashed_password=hashed_password
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate a user"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.user_id == user_id).first()
    
    @staticmethod
    def get_user_profile(db: Session, user_id: str) -> Optional[dict]:
        """Get user's profile data"""
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            return None
        
        return {
            "contact": {
                "full_name": profile.full_name,
                "email": profile.email,
                "phone": profile.phone,
                "linkedin": profile.linkedin_url,
                "github": profile.github_url,
                "portfolio": profile.portfolio_url,
            },
            "education": profile.education or [],
            "experience": profile.experience or [],
            "projects": profile.projects or [],
            "technical_skills": profile.technical_skills or {},
            "awards": profile.awards or []
        }
    
    @staticmethod
    def save_user_profile(db: Session, user_id: str, profile_data: dict) -> UserProfile:
        """Save or update user profile"""
        # Check if profile exists
        existing_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        contact = profile_data.get("contact", {})
        
        if existing_profile:
            # Update existing profile
            existing_profile.full_name = contact.get("full_name")
            existing_profile.email = contact.get("email")
            existing_profile.phone = contact.get("phone")
            existing_profile.linkedin_url = contact.get("linkedin")
            existing_profile.github_url = contact.get("github")
            existing_profile.portfolio_url = contact.get("portfolio")
            existing_profile.education = profile_data.get("education", [])
            existing_profile.experience = profile_data.get("experience", [])
            existing_profile.projects = profile_data.get("projects", [])
            existing_profile.technical_skills = profile_data.get("technical_skills", {})
            existing_profile.awards = profile_data.get("awards", [])
            
            db.commit()
            db.refresh(existing_profile)
            return existing_profile
        else:
            # Create new profile
            new_profile = UserProfile(
                user_id=user_id,
                full_name=contact.get("full_name"),
                email=contact.get("email"),
                phone=contact.get("phone"),
                linkedin_url=contact.get("linkedin"),
                github_url=contact.get("github"),
                portfolio_url=contact.get("portfolio"),
                education=profile_data.get("education", []),
                experience=profile_data.get("experience", []),
                projects=profile_data.get("projects", []),
                technical_skills=profile_data.get("technical_skills", {}),
                awards=profile_data.get("awards", [])
            )
            
            db.add(new_profile)
            db.commit()
            db.refresh(new_profile)
            return new_profile
    
    @staticmethod
    def profile_exists(db: Session, user_id: str) -> bool:
        """Check if user has a complete profile"""
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            return False
        
        # Check if profile has minimum required data
        has_contact = bool(profile.full_name and profile.email and profile.phone)
        has_experience = bool(profile.experience and len(profile.experience) > 0)
        has_skills = bool(profile.technical_skills)
        
        return has_contact and has_experience and has_skills