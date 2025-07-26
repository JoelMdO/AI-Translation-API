"""
Google Authentication utilities with testing support
Handles Google OAuth token validation for NextJS app integration
"""
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.auth.transport import requests
from google.oauth2 import id_token
from dotenv import load_dotenv
from app.schemas.testUser import GoogleUser
from app.config import GOOGLE_CLIENT_ID

load_dotenv()

# Security scheme
security = HTTPBearer()


def verify_google_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> GoogleUser:
    """
    Verify Google ID token from Authorization header
    Supports both real Google tokens and fake tokens for testing
    """
    try:
        # Extract token from Bearer format
        token = credentials.credentials
            # Production mode: verify real Google tokens
            payload = id_token.verify_oauth2_token( # type: ignore
                token, 
                requests.Request(), 
                GOOGLE_CLIENT_ID
            )
            
            # Check if token is from correct issuer
            if payload['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token issuer",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        # Return user information as structured object
        return GoogleUser(
            user_id=payload.get("sub"),
            email=payload.get("email"),
            name=payload.get("name"),
            verified=payload.get("email_verified", False)
        )
        
    except ValueError as e:
        # Invalid token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def check_user_permissions(user_info: GoogleUser) -> bool:
    """
    Check if user has permission to use the translation service
    """
    # Check if email is verified
    if not user_info.verified:
        return False
    
    # Example: Add domain restrictions if needed
    # allowed_domains = ["yourdomain.com", "anotherdomain.com"]
    # if not any(user_info.email.endswith(f"@{domain}") for domain in allowed_domains):
    #     return False
    
    return True


def verify_user_access(credentials: HTTPAuthorizationCredentials = Depends(security)) -> GoogleUser:
    """
    Complete user verification including Google token and permissions
    """
    # Verify Google token
    user_info = verify_google_token(credentials)
    
    # Check permissions
    if not check_user_permissions(user_info):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for translation service"
        )
    
    return user_info
