"""
Authentication Tests
Covers: Pytest, Unit Testing, API Testing
"""
import pytest


def test_signup(client):
    """Test user registration."""
    response = client.post("/api/auth/signup", json={
        "username": "teacher1",
        "email": "teacher1@test.com",
        "full_name": "Teacher One",
        "password": "pass1234",
        "role": "teacher"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "teacher1"
    assert data["role"] == "teacher"
    assert "hashed_password" not in data


def test_signup_duplicate(client):
    """Test duplicate username is rejected."""
    client.post("/api/auth/signup", json={
        "username": "dupuser",
        "email": "dup@test.com",
        "full_name": "Dup User",
        "password": "pass1234"
    })
    response = client.post("/api/auth/signup", json={
        "username": "dupuser",
        "email": "dup2@test.com",
        "full_name": "Dup User 2",
        "password": "pass1234"
    })
    assert response.status_code == 400


def test_login_success(client):
    """Test successful login returns JWT token."""
    # Create user first
    client.post("/api/auth/signup", json={
        "username": "logintest",
        "email": "logintest@test.com",
        "full_name": "Login Test",
        "password": "mypassword"
    })
    response = client.post("/api/auth/login", json={
        "username": "logintest",
        "password": "mypassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data


def test_login_wrong_password(client):
    """Test wrong password returns 401."""
    response = client.post("/api/auth/login", json={
        "username": "testadmin",
        "password": "wrongpassword"
    })
    assert response.status_code == 401


def test_get_me(client, auth_headers):
    """Test /me endpoint returns current user."""
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testadmin"


def test_protected_without_token(client):
    """Test protected endpoint without token returns 401."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
