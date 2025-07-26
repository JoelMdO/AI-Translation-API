"""
Test utilities for API testing
Includes fake Google ID token generation for Postman testing
"""
import jwt
import json
from datetime import datetime, timedelta
from typing import Dict, Any


class FakeGoogleTokenGenerator:
    """
    Generates fake Google ID tokens for testing purposes
    DO NOT USE IN PRODUCTION - Only for development and testing
    """
    
    def __init__(self):
        # Fake Google signing key (for testing only)
        self.fake_secret = "fake-google-secret-key-for-testing-only"
        self.fake_client_id = "your-google-client-id-from-console"
    
    def generate_fake_google_token(
        self, 
        user_id: str = "123456789",
        email: str = "test@example.com",
        name: str = "Test User",
        email_verified: bool = True,
        expires_in_minutes: int = 60
    ) -> str:
        """
        Generate a fake Google ID token for testing
        
        Args:
            user_id: Fake user ID
            email: Test email address
            name: Test user name
            email_verified: Whether email is verified
            expires_in_minutes: Token expiration time
            
        Returns:
            Fake JWT token that mimics Google ID token structure
        """
        now = datetime.now()
        exp = now + timedelta(minutes=expires_in_minutes)
        
        # Mimic Google ID token payload structure
        payload: object = {}
        payload = {
            "iss": "accounts.google.com",  # Google issuer
            "aud": self.fake_client_id,     # Your app's client ID
            "sub": user_id,                 # User ID
            "email": email,                 # User email
            "email_verified": email_verified, # Email verification status
            "name": name,                   # User name
            "picture": f"https://lh3.googleusercontent.com/fake-{user_id}",
            "iat": int(now.timestamp()),    # Issued at
            "exp": int(exp.timestamp()),    # Expires at
        }
        
        # Generate fake JWT token
        token = jwt.encode(payload, self.fake_secret, algorithm="HS256") # type: ignore
        return token
    
    def generate_postman_examples(self) -> Dict[str, Any]:
        """
        Generate example tokens for different test scenarios
        
        Returns:
            Dictionary with different test tokens
        """
        return {
            "valid_verified_user": {
                "token": self.generate_fake_google_token(),
                "description": "Valid token with verified email",
                "user_info": {
                    "user_id": "123456789",
                    "email": "test@example.com",
                    "name": "Test User",
                    "verified": True
                }
            },
            "unverified_user": {
                "token": self.generate_fake_google_token(
                    email="unverified@example.com",
                    email_verified=False
                ),
                "description": "Valid token but email not verified (should be rejected)",
                "user_info": {
                    "user_id": "123456790",
                    "email": "unverified@example.com",
                    "name": "Unverified User",
                    "verified": False
                }
            },
            "expired_token": {
                "token": self.generate_fake_google_token(expires_in_minutes=-30),
                "description": "Expired token (should be rejected)",
                "user_info": {
                    "user_id": "123456791",
                    "email": "expired@example.com",
                    "name": "Expired User",
                    "verified": True
                }
            }
        }


def create_postman_collection():
    """
    Create a Postman collection configuration for testing
    
    Returns:
        Dictionary that can be exported as Postman collection
    """
    token_generator = FakeGoogleTokenGenerator()
    examples = token_generator.generate_postman_examples()
    collection: Dict[str, Any] = {}
    collection = {
        "info": {
            "name": "Ollama Translation API Tests",
            "description": "Test collection for translation API with fake Google tokens",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "variable": [
            {
                "key": "base_url",
                "value": "https://localhost:443",
                "type": "string"
            },
            {
                "key": "valid_token",
                "value": examples["valid_verified_user"]["token"],
                "type": "string"
            },
            {
                "key": "unverified_token", 
                "value": examples["unverified_user"]["token"],
                "type": "string"
            }
        ],
        "item": [
            {
                "name": "Health Check",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{base_url}}/health",
                        "host": ["{{base_url}}"],
                        "path": ["health"]
                    }
                },
                "response": []
            },
            {
                "name": "Translation - Valid Token",
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        },
                        {
                            "key": "Authorization",
                            "value": "Bearer {{valid_token}}"
                        },
                        {
                            "key": "X-Request-Type",
                            "value": "translation"
                        },
                        {
                            "key": "X-Service",
                            "value": "cms-translate"
                        },
                        {
                            "key": "X-Source-DB",
                            "value": "db"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "title": "Test Article",
                            "body": "Hello world, this is a test translation.",
                            "section": "content",
                            "target_language": "spanish"
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{base_url}}/translate",
                        "host": ["{{base_url}}"],
                        "path": ["translate"]
                    }
                },
                "response": []
            },
            {
                "name": "Translation - Unverified Email (Should Fail)",
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        },
                        {
                            "key": "Authorization",
                            "value": "Bearer {{unverified_token}}"
                        },
                        {
                            "key": "X-Request-Type",
                            "value": "translation"
                        },
                        {
                            "key": "X-Service",
                            "value": "cms-translate"
                        },
                        {
                            "key": "X-Source-DB",
                            "value": "db"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "title": "Test Article",
                            "body": "This should fail due to unverified email.",
                            "section": "content",
                            "target_language": "french"
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{base_url}}/translate",
                        "host": ["{{base_url}}"],
                        "path": ["translate"]
                    }
                },
                "response": []
            }
        ]
    }
    
    return collection


if __name__ == "__main__":
    # Generate test tokens
    generator = FakeGoogleTokenGenerator()
    examples = generator.generate_postman_examples()
    
    print("🧪 FAKE GOOGLE TOKENS FOR TESTING")
    print("=" * 50)
    
    for scenario, data in examples.items():
        print(f"\n📋 {scenario.upper()}:")
        print(f"Description: {data['description']}")
        print(f"Token: {data['token']}")
        print(f"User Info: {json.dumps(data['user_info'], indent=2)}")
    
    print("\n" + "=" * 50)
    print("🚀 POSTMAN USAGE:")
    print("1. Copy the 'valid_verified_user' token")
    print("2. In Postman, set Authorization header:")
    print("   Bearer <paste_token_here>")
    print("3. Test your /translate endpoint")
    
    # Generate Postman collection
    collection = create_postman_collection()
    with open("postman_collection.json", "w") as f:
        json.dump(collection, f, indent=2)
    
    print("\n✅ Generated: postman_collection.json")
    print("   Import this file into Postman for ready-to-use tests!")
