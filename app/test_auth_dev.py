"""
Test for DEV_MODE bypass in authentication
"""
import os
import pytest
from fastapi import HTTPException
from utils.auth import verify_google_access_token
from fastapi.security import HTTPAuthorizationCredentials

class DummyCreds:
    def __init__(self, token):
        self.credentials = token

@pytest.mark.asyncio
async def test_dev_mode_bypass(monkeypatch):
    os.environ["DEV_MODE"] = "true"
    from importlib import reload
    import config
    reload(config)
    import utils.auth as auth_mod
    reload(auth_mod)
    creds = DummyCreds("anytoken")
    user = await auth_mod.verify_google_access_token(creds)
    assert user.email == "dev@localhost"
    assert user.verified is True
