"""
Pydantic Schemas for request/response validation
Covers: Data validation, serialization, API contracts
"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime


# ─── Auth Schemas ─────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    role: str = "teacher"

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


# ─── Department Schemas ───────────────────────────────────────────────────────
class DepartmentCreate(BaseModel):
    name: str
    code: str


class DepartmentOut(BaseModel):
    id: int
    name: str
    code: str

    class Config:
        from_attributes = True


# ─── Student Schemas ──────────────────────────────────────────────────────────
class StudentCreate(BaseModel):
    roll_no: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    department_id: Optional[int] = None
    year: Optional[int] = None


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department_id: Optional[int] = None
    year: Optional[int] = None
    is_active: Optional[bool] = None


class StudentOut(BaseModel):
    id: int
    roll_no: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    year: Optional[int]
    is_active: bool
    face_registered: bool
    registered_date: datetime
    department: Optional[DepartmentOut] = None

    class Config:
        from_attributes = True


# ─── Attendance Schemas ───────────────────────────────────────────────────────
class AttendanceCreate(BaseModel):
    roll_no: str
    name: str
    date: str
    time: str
    status: str = "Present"
    confidence: Optional[float] = None
    verification_method: str = "face_recognition"
    notes: Optional[str] = None


class AttendanceOut(BaseModel):
    id: int
    roll_no: str
    name: str
    date: str
    time: str
    status: str
    confidence: Optional[float]
    verification_method: str

    class Config:
        from_attributes = True


class AttendanceStats(BaseModel):
    total_students: int
    present_today: int
    absent_today: int
    attendance_rate: float
    total_records: int


# ─── Dashboard Schemas ────────────────────────────────────────────────────────
class DashboardSummary(BaseModel):
    stats: AttendanceStats
    recent_attendance: List[AttendanceOut]
    top_students: List[dict]
    weekly_data: List[dict]


# ─── System Log Schemas ───────────────────────────────────────────────────────
class SystemLogOut(BaseModel):
    id: int
    timestamp: datetime
    event_type: str
    roll_no: Optional[str]
    description: Optional[str]
    status: Optional[str]

    class Config:
        from_attributes = True


# ─── Generic Response ─────────────────────────────────────────────────────────
class MessageResponse(BaseModel):
    message: str
    success: bool = True
    data: Optional[dict] = None
