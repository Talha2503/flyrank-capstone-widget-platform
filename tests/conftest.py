import os
os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:dev@localhost:5433/widgets_test"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["FORCE_PROVIDER_A_DOWN"] = "false"
os.environ["FORCE_PROVIDER_B_DOWN"] = "false"
os.environ["FORCE_NOTIFY_DOWN"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from main import app

TEST_DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def clean_db():
    """Wipes and recreates all tables before every single test function."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="function", autouse=True)
def reset_rate_limiter():
    """Resets slowapi's in-memory rate-limit counters before every test,
    so one test's requests don't eat into another test's budget."""
    from app.routers.submissions import limiter
    limiter.reset()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Signs up a fresh tenant and returns ready-to-use auth headers."""
    client.post("/api/auth/signup", json={"email": "test@example.com", "password": "testpass123"})
    resp = client.post("/api/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def widget_id(client, auth_headers):
    """Creates a widget and returns its id, for tests that need one."""
    resp = client.post(
        "/api/widgets",
        headers=auth_headers,
        json={
            "type": "signup_form",
            "title": "Test Widget",
            "fields": [{"name": "email", "label": "Email", "type": "email", "required": True}],
            "button_text": "Go",
        },
    )
    return resp.json()["id"]