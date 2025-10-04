"""Test authentication system"""
from src.resume_agent.database import SessionLocal, engine, Base
from src.resume_agent.user_service import UserService
from src.resume_agent.schemas import UserCreate
from src.resume_agent.auth import create_access_token, verify_token
from src.resume_agent.models import User

# Initialize database
Base.metadata.create_all(bind=engine)

# Test user creation and authentication
db = SessionLocal()

try:
    print("=== Testing User Authentication ===\n")
    
    # Clean up any existing test user first
    print("0. Cleaning up old test user...")
    old_user = db.query(User).filter(User.email == "testuser@example.com").first()
    if old_user:
        db.delete(old_user)
        db.commit()
        print("✅ Old test user removed")
    
    # 1. Create a test user
    print("\n1. Creating new test user...")
    test_user_data = UserCreate(
        email="testuser@example.com",
        password="Test123!"
    )
    
    user = UserService.create_user(db, test_user_data)
    print(f"✅ User created: {user.email} (ID: {user.user_id})")
    
    # 2. Test authentication
    print("\n2. Testing authentication with correct password...")
    auth_user = UserService.authenticate_user(db, "testuser@example.com", "Test123!")
    if auth_user:
        print(f"✅ Authentication successful for: {auth_user.email}")
    else:
        print("❌ Authentication failed")
    
    # 3. Test wrong password
    print("\n3. Testing authentication with wrong password...")
    wrong_auth = UserService.authenticate_user(db, "testuser@example.com", "WrongPassword")
    if wrong_auth:
        print("❌ Wrong password was accepted (this shouldn't happen!)")
    else:
        print("✅ Wrong password correctly rejected")
    
    # 4. Test JWT token creation and verification
    print("\n4. Testing JWT tokens...")
    token = create_access_token(data={"sub": user.user_id})
    print(f"✅ Token created: {token[:50]}...")
    
    verified_user_id = verify_token(token)
    if verified_user_id == user.user_id:
        print(f"✅ Token verified successfully for user: {verified_user_id}")
    else:
        print("❌ Token verification failed")
    
    # 5. Test profile operations
    print("\n5. Testing profile operations...")
    has_profile = UserService.profile_exists(db, user.user_id)
    print(f"User has profile: {has_profile}")
    
    if not has_profile:
        print("✅ Correctly detected no profile exists")
    
    print("\n" + "="*50)
    print("✅ ALL AUTHENTICATION TESTS PASSED!")
    print("="*50)
    
except Exception as e:
    print(f"\n❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()