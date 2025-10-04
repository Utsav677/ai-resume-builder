"""SQLAlchemy models for database tables"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from .database import Base


class User(Base):
    """User authentication table"""
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UserProfile(Base):
    """User profile data - structured resume information"""
    __tablename__ = "user_profiles"
    
    profile_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, unique=True)
    
    # Contact Information
    full_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    location = Column(String(255))
    linkedin_url = Column(String(255))
    github_url = Column(String(255))
    portfolio_url = Column(String(255))
    
    # Structured data as JSON
    education = Column(JSON)  # List of education entries
    experience = Column(JSON)  # List of work experiences
    projects = Column(JSON)  # List of projects
    technical_skills = Column(JSON)  # Skills categorized
    awards = Column(JSON)  # Optional awards list
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ResumeGeneration(Base):
    """History of generated resumes"""
    __tablename__ = "resume_generations"
    
    generation_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    
    # Job information
    job_title = Column(String(255))
    company_name = Column(String(255))
    job_description = Column(Text)
    
    # Generated content
    tailored_content = Column(JSON)  # The customized resume content
    ats_keywords = Column(JSON)  # Keywords used
    ats_score = Column(Float)  # ATS optimization score
    
    # Output files
    latex_code = Column(Text)
    pdf_path = Column(String(500))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ConversationThread(Base):
    """LangGraph conversation threads for checkpoint persistence"""
    __tablename__ = "conversation_threads"
    
    thread_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    session_type = Column(String(50))  # 'profile_setup' or 'resume_generation'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
