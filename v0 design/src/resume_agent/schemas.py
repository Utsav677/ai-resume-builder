"""Pydantic models for data validation and structured output"""
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field


class ContactInfo(BaseModel):
    """Contact information"""
    full_name: str
    phone: str
    email: EmailStr
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None


class Education(BaseModel):
    """Education entry"""
    institution: str
    location: str
    degree: str
    gpa: Optional[str] = None
    dates: str  # e.g., "Aug. 2023 – May 2027"
    coursework: Optional[list[str]] = None


class Experience(BaseModel):
    """Work experience entry"""
    title: str
    dates: str
    organization: str
    location: str
    bullets: list[str] = Field(description="Quantified achievement bullets")


class Project(BaseModel):
    """Project entry"""
    name: str
    technologies: str  # Comma-separated: "Python, Flask, React"
    dates: str
    bullets: list[str]


class TechnicalSkills(BaseModel):
    """Technical skills categorized"""
    languages: list[str]
    frameworks: list[str]
    developer_tools: list[str]
    libraries: list[str]
    technologies: Optional[list[str]] = None


class Award(BaseModel):
    """Award or honor"""
    title: str
    description: Optional[str] = None


class UserProfileSchema(BaseModel):
    """Complete user profile matching resume template"""
    contact: ContactInfo
    education: list[Education]
    experience: list[Experience]
    projects: list[Project]
    technical_skills: TechnicalSkills
    awards: Optional[list[Award]] = None


class JobAnalysis(BaseModel):
    """Structured job description analysis"""
    job_title: str
    company: str
    required_skills: list[str]
    preferred_skills: list[str]
    experience_requirements: str
    key_responsibilities: list[str]
    ats_keywords: list[str] = Field(description="20-30 critical ATS keywords")
    company_values: list[str]


class ExperienceMatch(BaseModel):
    """Ranked experience with relevance score"""
    experience: Experience
    relevance_score: float = Field(ge=0, le=10)
    matching_requirements: list[str]
    improved_bullets: list[str]


# User authentication schemas
class UserCreate(BaseModel):
    """User registration"""
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    """User login"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """JWT token payload"""
    user_id: Optional[str] = None
