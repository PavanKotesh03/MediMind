import sys
import os

# ---------------------------------------------------------
# Make backend importable
# ---------------------------------------------------------
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import pytest
from fastapi.testclient import TestClient

from api.main import app
from database.connection import get_db
from auth.jwt_bearer import JWTBearer

# ---------------------------------------------------------
# Fake DB
# ---------------------------------------------------------
class FakeDB:
    def close(self):
        pass


def override_get_db():
    yield FakeDB()


from fastapi import Request

# ---------------------------------------------------------
# 🔥 GLOBAL JWT BYPASS (THIS FIXES CHAT)
# ---------------------------------------------------------
async def fake_jwt_call(self, request: Request):
    return "test@example.com"


JWTBearer.__call__ = fake_jwt_call


# Apply overrides
app.dependency_overrides[get_db] = override_get_db


# ---------------------------------------------------------
# Test client
# ---------------------------------------------------------
@pytest.fixture
def client():
    return TestClient(app)
