"""
Simple test token generator for Postman testing
Run this script to get fake Google ID tokens for testing your API
"""
import jwt
import json
from datetime import datetime, timedelta


def generate_fake_google_token(
    user_id: str = "123456789",
    email: str = "test@example.com", 
    name: str = "Test User",
    email_verified: bool = True
) -> str:
    """Generate a fake Google ID token for testing"""
    
    # Fake secret (only for testing)
    fake_secret = "fake-google-secret-for-testing"
    
    # Token payload mimicking Google ID token structure
    now = datetime.now()
    exp = now + timedelta(hours=1)
    payload: object={}
    payload = {
        "iss": "accounts.google.com",
        "aud": "your-google-client-id-from-console", 
        "sub": user_id,
        "email": email,
        "email_verified": email_verified,
        "name": name,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp())
    }
    
    return jwt.encode(payload, fake_secret, algorithm="HS256") # type: ignore


if __name__ == "__main__":
    print("🧪 FAKE GOOGLE TOKENS FOR POSTMAN TESTING")
    print("=" * 60)
    
    # Generate different test scenarios
    scenarios: object={}
    scenarios = {
        "✅ Valid User (Email Verified)": {
            "token": generate_fake_google_token(),
            "should_work": True
        },
        "❌ Unverified Email": {
            "token": generate_fake_google_token(
                email="unverified@example.com",
                email_verified=False
            ),
            "should_work": False
        },
        "✅ Another Valid User": {
            "token": generate_fake_google_token(
                user_id="987654321",
                email="user2@example.com",
                name="Jane Doe"
            ),
            "should_work": True
        }
    }
    
    for scenario_name, data in scenarios.items():
        print(f"\n{scenario_name}")
        print(f"Token: {data['token']}")
        print(f"Expected result: {'Should work' if data['should_work'] else 'Should be rejected'}")
        print("-" * 60)
    
    print("\n🚀 POSTMAN USAGE INSTRUCTIONS:")
    print("1. Copy any 'Valid User' token above")
    print("2. In Postman, create a POST request to: https://localhost:443/translate")
    print("3. Add headers:")
    print("   - Authorization: Bearer <paste_token_here>")
    print("   - Content-Type: application/json")
    print("   - X-Request-Type: translation")
    print("   - X-Service: cms-translate") 
    print("   - X-Source-DB: db")
    print("4. Add JSON body:")
    
    sample_body = {
        "title": "Test Article",
        "body": "Hello world, please translate this text.",
        "section": "content", 
        "target_language": "spanish"
    }
    
    print(json.dumps(sample_body, indent=2))
    
    print("\n✅ The valid tokens should return a translation")
    print("❌ The unverified email token should return 403 Forbidden")
