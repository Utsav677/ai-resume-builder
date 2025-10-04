"""Configuration and utilities"""
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resume_builder.db")

# Paths
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "templates")
STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "storage")
RESUMES_DIR = os.path.join(STORAGE_DIR, "resumes")

# Ensure directories exist
os.makedirs(RESUMES_DIR, exist_ok=True)
