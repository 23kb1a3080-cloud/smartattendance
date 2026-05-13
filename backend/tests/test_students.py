"""
Student API Tests
Covers: Pytest, Unit Testing, CRUD Testing
"""
import pytest


def test_create_student(client, auth_headers):
    """Test creating a new student."""
    response = client.post("/api/students/", json={
        "roll_no": "TEST001",
        "name": "Test Student",
        "email": "test001@college.com",
        "year": 2
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["roll_no"] == "TEST001"
    assert data["name"] == "Test Student"
    assert data["face_registered"] == False


def test_create_duplicate_student(client, auth_headers):
    """Test duplicate roll number is rejected."""
    client.post("/api/students/", json={
        "roll_no": "DUP001",
        "name": "Dup Student"
    }, headers=auth_headers)
    response = client.post("/api/students/", json={
        "roll_no": "DUP001",
        "name": "Dup Student 2"
    }, headers=auth_headers)
    assert response.status_code == 400


def test_list_students(client, auth_headers):
    """Test listing students."""
    response = client.get("/api/students/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_student(client, auth_headers):
    """Test getting a specific student."""
    response = client.get("/api/students/TEST001", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["roll_no"] == "TEST001"


def test_get_nonexistent_student(client, auth_headers):
    """Test 404 for missing student."""
    response = client.get("/api/students/NOTEXIST", headers=auth_headers)
    assert response.status_code == 404


def test_update_student(client, auth_headers):
    """Test updating student details."""
    response = client.put("/api/students/TEST001", json={
        "name": "Updated Name",
        "year": 3
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


def test_create_department(client, auth_headers):
    """Test creating a department."""
    response = client.post("/api/students/departments", json={
        "name": "Test Department",
        "code": "TDEPT"
    }, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["code"] == "TDEPT"


def test_list_departments(client, auth_headers):
    """Test listing departments."""
    response = client.get("/api/students/departments", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
