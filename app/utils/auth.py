"""
Google Access Token Authentication utilities
Handles Google OAuth access token validation for NextJS app integration
"""
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from dotenv import load_dotenv
# from schemas.testUser import GoogleUser
# from config import GOOGLE_CLIENT_ID, DEV_MODE

##//TODO change app before deploying 
from schemas.testUser import GoogleUser
from config import GOOGLE_CLIENT_ID, DEV_MODE

load_dotenv()

# Security scheme
security = HTTPBearer()



async def verify_google_access_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> GoogleUser:
    """
    Verify Google Access Token from Authorization header
    Validates Google OAuth access tokens from NextAuth.js sessions
    """
    if DEV_MODE:
        # Bypass token validation in development mode
        return GoogleUser(
            user_id="dev_user",
            email="dev@localhost",
            name="Developer",
            verified=True
        )
    try:
        # Extract token from Bearer format
        token = credentials.credentials
        # Debug logging to see what token we received
        print(f"DEBUG: Received token: {token[:50]}..." if len(token) > 50 else f"DEBUG: Received token: {token}")
        print(f"DEBUG: Token type: Google Access Token")
        # Validate Google access token using Google's tokeninfo endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={token}")
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google access token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            token_info = response.json()
            # Verify the token audience (client_id) if available
            if GOOGLE_CLIENT_ID and token_info.get("audience") != GOOGLE_CLIENT_ID:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token not issued for this client",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        # For access tokens, we need to get user info separately
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={token}"
            )
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not fetch user information",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            user_info = user_response.json()
            return GoogleUser(
                user_id=str(user_info.get("id", "")),
                email=str(user_info.get("email", "")),
                name=str(user_info.get("name", "")),
                verified=bool(user_info.get("verified_email", False))
            )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
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


async def verify_user_access(credentials: HTTPAuthorizationCredentials = Depends(security)) -> GoogleUser:
    """
    Complete user verification including Google access token and permissions
    """
    # Verify Google access token
    user_info = await verify_google_access_token(credentials)
    
    # Check permissions
    if not check_user_permissions(user_info):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for translation service"
        )
    
    return user_info
