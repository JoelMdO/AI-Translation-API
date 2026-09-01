import os
import sys

# Ensure both repo root and app/ are on sys.path before importing app modules.
# - ROOT must be present so tests can use `from app.xxx import yyy` style imports.
# - APP_PATH must be present so internal app imports (e.g. `from schemas.xxx import …`)
#   continue to resolve correctly when running inside the app package.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # repo root
APP_PATH = os.path.join(ROOT, 'app')  # repo root/app
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if APP_PATH not in sys.path:
    sys.path.insert(1, APP_PATH)

# Set env vars before importing config so DEV_MODE and ALLOWED_ORIGINS are available
os.environ.setdefault('DEV_MODE', 'true')
os.environ.setdefault('ALLOWED_ORIGINS', '["*"]')
os.environ.setdefault('OLLAMA_DEFAULT_MODEL', 'test-model')
os.environ.setdefault('OLLAMA_BASE_URL', 'http://localhost:11434')

import pytest
from httpx import AsyncClient, ASGITransport

# Import the FastAPI app after environment is set and path configured
from app.main import app

# Bridge the "double import" gap: internal app code uses bare imports
# (e.g. `from utils.translation.xxx import yyy`) while tests use the `app.xxx`
# prefix.  Register every bare-name module that came from app/ under its
# `app.<name>` alias so that both paths point to the same module object.
# This makes monkeypatching via `app.utils.xxx` work correctly for service code
# that holds a reference obtained through the bare `utils.xxx` path.
for _key in list(sys.modules.keys()):
    if not _key.startswith('app.') and sys.modules[_key] is not None:
        _mod = sys.modules[_key]
        if hasattr(_mod, '__file__') and _mod.__file__ and APP_PATH in (_mod.__file__ or ''):
            _app_key = 'app.' + _key
            if _app_key not in sys.modules:
                sys.modules[_app_key] = _mod

@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
