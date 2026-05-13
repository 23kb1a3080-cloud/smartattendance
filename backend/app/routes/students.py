"""
Student Management Routes
Covers: REST API, CRUD, HTTP Methods, SQLAlchemy ORM
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os, shutil

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db
from app.config import settings

router = APIRouter(prefix="/api/students", tags=["Students"])


# ─── Departments ──────────────────────────────────────────────────────────────
@router.post("/departments", response_model=schemas.DepartmentOut, status_code=201)
def create_department(
    dept: schemas.DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new department."""
    existing = db.query(models.Department).filter(models.Department.code == dept.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department code already exists")
    new_dept = models.Department(name=dept.name, code=dept.code)
    db.add(new_dept)
    db.commit()
    db.refresh(new_dept)
    return new_dept


@router.get("/departments", response_model=List[schemas.DepartmentOut])
def list_departments(db: Session = Depends(get_db)):
    """List all departments."""
    return db.query(models.Department).all()


# ─── Students CRUD ────────────────────────────────────────────────────────────
@router.post("/", response_model=schemas.StudentOut, status_code=201)
def create_student(
    student: schemas.StudentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Register a new student. Covers: POST HTTP Method, CRUD Create."""
    if db.query(models.Student).filter(models.Student.roll_no == student.roll_no).first():
        raise HTTPException(status_code=400, detail="Roll number already registered")

    new_student = models.Student(**student.model_dump())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    # Log event
    log = models.SystemLog(
        event_type="student_registered",
        roll_no=student.roll_no,
        description=f"Student {student.name} registered via API",
        status="success"
    )
    db.add(log)
    db.commit()

    return new_student


@router.get("/", response_model=List[schemas.StudentOut])
def list_students(
    skip: int = 0,
    limit: int = 100,
    department_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    List all students with optional filters.
    Covers: GET HTTP Method, Query Parameters, Joins
    """
    query = db.query(models.Student)

    if department_id:
        query = query.filter(models.Student.department_id == department_id)

    if search:
        query = query.filter(
            (models.Student.name.ilike(f"%{search}%")) |
            (models.Student.roll_no.ilike(f"%{search}%"))
        )

    return query.offset(skip).limit(limit).all()


@router.get("/{roll_no}", response_model=schemas.StudentOut)
def get_student(
    roll_no: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a single student by roll number. Covers: GET by ID."""
    student = db.query(models.Student).filter(models.Student.roll_no == roll_no).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.put("/{roll_no}", response_model=schemas.StudentOut)
def update_student(
    roll_no: str,
    update_data: schemas.StudentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update student details. Covers: PUT HTTP Method, CRUD Update."""
    student = db.query(models.Student).filter(models.Student.roll_no == roll_no).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(student, field, value)

    db.commit()
    db.refresh(student)
    return student


@router.delete("/{roll_no}", response_model=schemas.MessageResponse)
def delete_student(
    roll_no: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a student. Covers: DELETE HTTP Method, CRUD Delete."""
    student = db.query(models.Student).filter(models.Student.roll_no == roll_no).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    db.delete(student)
    db.commit()
    return {"message": f"Student {roll_no} deleted successfully", "success": True}


@router.post("/{roll_no}/upload-face", response_model=schemas.MessageResponse)
async def upload_face_image(
    roll_no: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Upload a face image for a student. Covers: File Upload, Multipart."""
    student = db.query(models.Student).filter(models.Student.roll_no == roll_no).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Save image to dataset folder
    student_dir = os.path.join(settings.DATASET_PATH, roll_no)
    os.makedirs(student_dir, exist_ok=True)

    existing = len([f for f in os.listdir(student_dir) if f.endswith(".jpg")])
    filename = f"{roll_no}_{existing + 1:03d}.jpg"
    filepath = os.path.join(student_dir, filename)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    student.face_registered = True
    db.commit()

    return {
        "message": f"Face image uploaded: {filename}",
        "success": True,
        "data": {"filename": filename, "path": filepath}
    }
