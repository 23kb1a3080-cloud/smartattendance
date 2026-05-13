"""
SQLAlchemy ORM Models
Covers: Database Models, Relationships, Keys, Joins
"""
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """Admin/Teacher user accounts with authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="teacher")   # admin | teacher | student
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete")


class UserSession(Base):
    """JWT session tracking (OAuth-style)."""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_jti = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)

    user = relationship("User", back_populates="sessions")


class Department(Base):
    """Academic departments."""
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    students = relationship("Student", back_populates="department")


class Student(Base):
    """Registered students with face data."""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    roll_no = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    phone = Column(String(20), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    year = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    face_registered = Column(Boolean, default=False)
    face_encoding_path = Column(String(255), nullable=True)
    registered_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    department = relationship("Department", back_populates="students")
    attendance_records = relationship("Attendance", back_populates="student", cascade="all, delete")


class Attendance(Base):
    """Attendance records with face confidence scores."""
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    roll_no = Column(String(50), ForeignKey("students.roll_no"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    date = Column(String(20), nullable=False, index=True)
    time = Column(String(20), nullable=False)
    status = Column(String(20), default="Present")
    confidence = Column(Float, nullable=True)
    verification_method = Column(String(50), default="face_recognition")
    marked_by = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    # Unique: one attendance per student per day
    __table_args__ = (UniqueConstraint("roll_no", "date", name="uq_student_date"),)

    student = relationship("Student", back_populates="attendance_records")


class SystemLog(Base):
    """System event logs for audit trail."""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    event_type = Column(String(50), nullable=False)
    roll_no = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    status = Column(String(20), nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
