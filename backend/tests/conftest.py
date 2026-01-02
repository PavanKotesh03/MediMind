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
from api.routers.history import get_current_user


# ---------------------------------------------------------
# Fake DB
# ---------------------------------------------------------
class FakeDB:
    def close(self):
        pass


def override_get_db():
    yield FakeDB()


# ---------------------------------------------------------
# 🔥 GLOBAL JWT BYPASS (THIS FIXES CHAT)
# ---------------------------------------------------------
def fake_jwt_call(self, *args, **kwargs):
    return "test@example.com"


JWTBearer.__call__ = fake_jwt_call


# History router auth override
def override_current_user():
    return "test@example.com"


# Apply overrides
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_current_user


# ---------------------------------------------------------
# Test client
# ---------------------------------------------------------
@pytest.fixture
def client():
    return TestClient(app)
