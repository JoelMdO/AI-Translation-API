import os
import sys

# Ensure API/app is on sys.path before importing app modules
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # API/
APP_PATH = os.path.join(ROOT, 'app')  # API/app
sys.path.insert(0, APP_PATH)

# Set env vars before importing config so DEV_MODE and ALLOWED_ORIGINS are available
os.environ.setdefault('DEV_MODE', 'true')
os.environ.setdefault('ALLOWED_ORIGINS', '["*"]')
os.environ.setdefault('OLLAMA_DEFAULT_MODEL', 'test-model')

import pytest
from httpx import AsyncClient, ASGITransport

# Import the FastAPI app after environment is set and path configured
from main import app

@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
