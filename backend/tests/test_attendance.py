"""
Attendance API Tests
Covers: Pytest, Unit Testing, API Testing, Debugging
"""
import pytest
from datetime import date


def test_mark_attendance(client, auth_headers):
    """Test marking attendance for a student."""
    # Create student first
    client.post("/api/students/", json={
        "roll_no": "ATT001",
        "name": "Attendance Student"
    }, headers=auth_headers)

    response = client.post("/api/attendance/mark", json={
        "roll_no": "ATT001",
        "name": "Attendance Student",
        "date": "2026-05-13",
        "time": "09:00:00",
        "status": "Present",
        "confidence": 0.95
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["roll_no"] == "ATT001"
    assert data["status"] == "Present"


def test_duplicate_attendance(client, auth_headers):
    """Test duplicate attendance is rejected (409)."""
    response = client.post("/api/attendance/mark", json={
        "roll_no": "ATT001",
        "name": "Attendance Student",
        "date": "2026-05-13",
        "time": "10:00:00",
        "status": "Present"
    }, headers=auth_headers)
    assert response.status_code == 409


def test_list_attendance(client, auth_headers):
    """Test listing attendance records."""
    response = client.get("/api/attendance/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_today_attendance(client, auth_headers):
    """Test getting today's attendance."""
    response = client.get("/api/attendance/today", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_attendance_stats(client, auth_headers):
    """Test attendance statistics endpoint."""
    response = client.get("/api/attendance/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_students" in data
    assert "present_today" in data
    assert "attendance_rate" in data


def test_student_attendance_history(client, auth_headers):
    """Test getting attendance history for a student."""
    response = client.get("/api/attendance/student/ATT001", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_export_json(client, auth_headers):
    """Test JSON export endpoint."""
    response = client.get("/api/attendance/export/json", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "records" in data
    assert "total_records" in data


def test_attendance_for_nonexistent_student(client, auth_headers):
    """Test marking attendance for non-existent student returns 404."""
    response = client.post("/api/attendance/mark", json={
        "roll_no": "GHOST999",
        "name": "Ghost",
        "date": "2026-05-13",
        "time": "09:00:00"
    }, headers=auth_headers)
    assert response.status_code == 404
