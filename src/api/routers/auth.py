"""Authentication endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from ..dependencies import get_db, get_current_user_from_firebase
from ...resume_agent.models import User
from ...resume_agent.user_service import UserService
from ..firebase_auth import verify_firebase_token


router = APIRouter()


class FirebaseLoginRequest(BaseModel):
    """Request body for Firebase login"""
    firebase_token: str


class LoginResponse(BaseModel):
    """Response for successful login"""
    user_id: str
    email: str
    full_name: str
    message: str


@router.post("/login", response_model=LoginResponse)
async def login_with_firebase(
    request: FirebaseLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login or register user with Firebase ID token

    This endpoint:
    1. Verifies the Firebase ID token
    2. Gets user info from Firebase
    3. Creates user in database if doesn't exist
    4. Returns user info

    Frontend flow:
    1. User signs in with Firebase (Google, email/password)
    2. Frontend gets Firebase ID token
    3. Frontend sends token to this endpoint
    4. Backend verifies token and returns user info
    5. Frontend stores user info and includes token in subsequent requests
    """
    # Verify Firebase token
    firebase_user = await verify_firebase_token(request.firebase_token)
    if not firebase_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase token"
        )

    # Get or create user
    user = UserService.get_user_by_email(db, firebase_user["email"])

    if not user:
        # Auto-register new user
        user = UserService.create_user(
            db=db,
            email=firebase_user["email"],
            password="",  # No password for Firebase auth
            full_name=firebase_user.get("name", firebase_user["email"].split("@")[0])
        )
        message = "Account created successfully"
    else:
        message = "Login successful"

    return LoginResponse(
        user_id=user.user_id,
        email=user.email,
        full_name=user.full_name,
        message=message
    )


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user_from_firebase)
):
    """Get current authenticated user info"""
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }


@router.post("/logout")
async def logout():
    """
    Logout endpoint (mainly for consistency)

    Since we're using Firebase auth, actual logout happens on the client side.
    This endpoint is here for completeness.
    """
    return {"message": "Logged out successfully. Clear Firebase token on client."}
