"""
Pytest Configuration & Fixtures
Covers: Pytest, Unit Testing, Test Setup
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.auth import hash_password
from app import models

# ─── Test Database (in-memory SQLite) ────────────────────────────────────────
TEST_DATABASE_URL = "sqlite:///./test_attendance.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables before tests, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture(scope="session")
def db():
    """Test database session."""
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="session")
def admin_token(client, db):
    """Create admin user and return JWT token."""
    # Create admin user
    admin = models.User(
        username="testadmin",
        email="testadmin@test.com",
        full_name="Test Admin",
        hashed_password=hash_password("testpass123"),
        role="admin"
    )
    db.add(admin)
    db.commit()

    # Login
    response = client.post("/api/auth/login", json={
        "username": "testadmin",
        "password": "testpass123"
    })
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(admin_token):
    """Authorization headers with JWT token."""
    return {"Authorization": f"Bearer {admin_token}"}
