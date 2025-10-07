"""Authentication endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from firebase_admin import auth as firebase_auth

from ..dependencies import get_db, get_current_user_from_firebase
from ...resume_agent.models import User
from ...resume_agent.user_service import UserService
from ..firebase_auth import verify_firebase_token
from ..password_utils import hash_password, verify_password


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


class EmailPasswordRequest(BaseModel):
    """Request body for email/password authentication"""
    email: EmailStr
    password: str


class EmailAuthResponse(BaseModel):
    """Response for email/password authentication"""
    success: bool
    custom_token: str
    user: dict


@router.post("/email/signup", response_model=EmailAuthResponse)
async def signup_with_email_password(
    request: EmailPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Sign up with email and password (server-side only)

    This endpoint:
    1. Creates user in Firebase with Admin SDK
    2. Stores hashed password in our database
    3. Generates a Firebase custom token
    4. Returns the token for client-side authentication
    """
    try:
        # Check if user already exists in our database
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create user in Firebase
        firebase_user = firebase_auth.create_user(
            email=request.email,
            password=request.password,
            email_verified=False
        )

        # Hash password and store in our database
        hashed_pw = hash_password(request.password)
        user = User(
            user_id=firebase_user.uid,
            email=request.email,
            hashed_password=hashed_pw
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Generate custom token for client
        custom_token = firebase_auth.create_custom_token(firebase_user.uid)

        return EmailAuthResponse(
            success=True,
            custom_token=custom_token.decode('utf-8'),
            user={
                "uid": firebase_user.uid,
                "email": firebase_user.email
            }
        )

    except firebase_auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered in Firebase"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/email/login", response_model=EmailAuthResponse)
async def login_with_email_password(
    request: EmailPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Login with email and password (server-side only)

    This endpoint:
    1. Verifies password against our database hash
    2. Gets Firebase user by email
    3. Generates a Firebase custom token
    4. Returns the token for client-side authentication
    """
    try:
        # Get user from our database
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Verify password
        if not verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Get Firebase user
        try:
            firebase_user = firebase_auth.get_user_by_email(request.email)
        except firebase_auth.UserNotFoundError:
            # Create Firebase user if doesn't exist (shouldn't happen normally)
            firebase_user = firebase_auth.create_user(
                email=request.email,
                password=request.password
            )

        # Generate custom token
        custom_token = firebase_auth.create_custom_token(firebase_user.uid)

        return EmailAuthResponse(
            success=True,
            custom_token=custom_token.decode('utf-8'),
            user={
                "uid": firebase_user.uid,
                "email": firebase_user.email
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
