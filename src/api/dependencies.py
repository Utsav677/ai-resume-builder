"""FastAPI dependencies for authentication and authorization"""
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from ..resume_agent.database import SessionLocal
from ..resume_agent.models import User
from ..resume_agent.user_service import UserService
from .firebase_auth import verify_firebase_token


security = HTTPBearer()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user_from_firebase(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current user from Firebase ID token

    Expects header: Authorization: Bearer <firebase_id_token>
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )

    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )

    # Verify Firebase token
    firebase_user = await verify_firebase_token(token)
    if not firebase_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    # Get or create user in database
    user = UserService.get_user_by_email(db, firebase_user["email"])

    if not user:
        # Auto-register user on first login
        user = UserService.create_user(
            db=db,
            email=firebase_user["email"],
            password="",  # No password needed for Firebase auth
            full_name=firebase_user.get("name", "")
        )
        print(f"✓ Auto-registered new user: {firebase_user['email']}")

    return user


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Optional authentication - returns None if no token"""
    if not authorization:
        return None

    try:
        return await get_current_user_from_firebase(authorization, db)
    except HTTPException:
        return None
