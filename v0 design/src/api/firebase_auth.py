"""Firebase Admin SDK integration for token verification"""
import os
import json
from typing import Optional
from dotenv import load_dotenv
from firebase_admin import credentials, auth, initialize_app
from firebase_admin.exceptions import FirebaseError

# Load environment variables
load_dotenv()


# Initialize Firebase Admin SDK
def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Try to load from environment variable (JSON string or file path)
        creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        creds_json = os.getenv("FIREBASE_CREDENTIALS_JSON")

        if creds_json:
            # Parse JSON string
            cred_dict = json.loads(creds_json)
            cred = credentials.Certificate(cred_dict)
        elif creds_path and os.path.exists(creds_path):
            # Load from file
            cred = credentials.Certificate(creds_path)
        elif os.getenv("FIREBASE_PROJECT_ID"):
            # Build credentials from individual env vars
            cred_dict = {
                "type": "service_account",
                "project_id": os.getenv("FIREBASE_PROJECT_ID"),
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": os.getenv("FIREBASE_PRIVATE_KEY"),
                "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                "auth_uri": os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
                "token_uri": os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
                "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"),
                "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
            }
            cred = credentials.Certificate(cred_dict)
        else:
            print("WARNING: Firebase credentials not found. Using test mode.")
            # For local testing without Firebase
            return None

        initialize_app(cred)
        print("Firebase Admin SDK initialized successfully")
        return cred
    except Exception as e:
        print(f"WARNING: Could not initialize Firebase: {e}")
        return None


# Initialize on module load
firebase_cred = init_firebase()


async def verify_firebase_token(id_token: str) -> Optional[dict]:
    """
    Verify Firebase ID token and return user info

    Args:
        id_token: Firebase ID token from frontend

    Returns:
        dict with user info: {uid, email, name, email_verified}
        None if verification fails
    """
    if not firebase_cred:
        # Test mode - extract user info from token without verification
        # WARNING: Only for local development!
        print("WARNING: Running in test mode without Firebase verification!")
        import jwt
        try:
            # Decode without verification (INSECURE - testing only)
            decoded = jwt.decode(id_token, options={"verify_signature": False})
            return {
                "uid": decoded.get("sub", "test_user"),
                "email": decoded.get("email", "test@example.com"),
                "name": decoded.get("name", "Test User"),
                "email_verified": True
            }
        except:
            return None

    try:
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(id_token)

        # Extract user information
        uid = decoded_token["uid"]
        user_record = auth.get_user(uid)

        return {
            "uid": uid,
            "email": user_record.email,
            "name": user_record.display_name or user_record.email.split("@")[0],
            "email_verified": user_record.email_verified,
            "photo_url": user_record.photo_url,
            "provider": decoded_token.get("firebase", {}).get("sign_in_provider", "unknown")
        }
    except FirebaseError as e:
        print(f"Firebase verification error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during token verification: {e}")
        return None


async def create_custom_token(uid: str) -> Optional[str]:
    """
    Create a custom Firebase token (if needed)

    Args:
        uid: User ID

    Returns:
        Custom token string or None
    """
    if not firebase_cred:
        return None

    try:
        custom_token = auth.create_custom_token(uid)
        return custom_token.decode('utf-8')
    except Exception as e:
        print(f"Error creating custom token: {e}")
        return None
