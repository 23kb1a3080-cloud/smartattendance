"""
Attendance Routes
Covers: REST API, CRUD, HTTP Methods, JSON responses
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import date, datetime

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])


@router.post("/mark", response_model=schemas.AttendanceOut, status_code=201)
def mark_attendance(
    data: schemas.AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Mark attendance for a student.
    Covers: POST, CRUD Create, Duplicate Prevention
    """
    # Verify student exists
    student = db.query(models.Student).filter(models.Student.roll_no == data.roll_no).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Check duplicate
    existing = db.query(models.Attendance).filter(
        and_(models.Attendance.roll_no == data.roll_no,
             models.Attendance.date == data.date)
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Attendance already marked for {data.roll_no} on {data.date}"
        )

    record = models.Attendance(**data.model_dump())
    db.add(record)

    # Log event
    log = models.SystemLog(
        event_type="attendance_marked",
        roll_no=data.roll_no,
        description=f"Attendance marked for {data.name}",
        confidence=data.confidence,
        status="success"
    )
    db.add(log)
    db.commit()
    db.refresh(record)
    return record


@router.get("/", response_model=List[schemas.AttendanceOut])
def list_attendance(
    date_filter: Optional[str] = Query(None, alias="date"),
    roll_no: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    List attendance records with filters.
    Covers: GET, Query Parameters, Filtering
    """
    query = db.query(models.Attendance)

    if date_filter:
        query = query.filter(models.Attendance.date == date_filter)
    if roll_no:
        query = query.filter(models.Attendance.roll_no == roll_no)

    return query.order_by(models.Attendance.date.desc()).offset(skip).limit(limit).all()


@router.get("/today", response_model=List[schemas.AttendanceOut])
def get_today_attendance(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get today's attendance records."""
    today = date.today().strftime("%Y-%m-%d")
    return db.query(models.Attendance).filter(models.Attendance.date == today).all()


@router.get("/stats", response_model=schemas.AttendanceStats)
def get_attendance_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get attendance statistics.
    Covers: Aggregation, Analytics
    """
    today = date.today().strftime("%Y-%m-%d")
    total_students = db.query(models.Student).filter(models.Student.is_active == True).count()
    present_today = db.query(models.Attendance).filter(models.Attendance.date == today).count()
    absent_today = total_students - present_today
    total_records = db.query(models.Attendance).count()
    attendance_rate = round((present_today / total_students * 100) if total_students > 0 else 0, 2)

    return {
        "total_students": total_students,
        "present_today": present_today,
        "absent_today": absent_today,
        "attendance_rate": attendance_rate,
        "total_records": total_records,
    }


@router.get("/student/{roll_no}", response_model=List[schemas.AttendanceOut])
def get_student_attendance(
    roll_no: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all attendance records for a specific student."""
    return db.query(models.Attendance).filter(
        models.Attendance.roll_no == roll_no
    ).order_by(models.Attendance.date.desc()).all()


@router.delete("/{attendance_id}", response_model=schemas.MessageResponse)
def delete_attendance(
    attendance_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete an attendance record. Covers: DELETE HTTP Method."""
    record = db.query(models.Attendance).filter(models.Attendance.id == attendance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    db.delete(record)
    db.commit()
    return {"message": "Attendance record deleted", "success": True}


@router.get("/export/json")
def export_attendance_json(
    date_filter: Optional[str] = Query(None, alias="date"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Export attendance data as JSON.
    Covers: JSON, Data Export
    """
    query = db.query(models.Attendance)
    if date_filter:
        query = query.filter(models.Attendance.date == date_filter)

    records = query.all()
    return {
        "exported_at": datetime.now().isoformat(),
        "total_records": len(records),
        "records": [
            {
                "id": r.id, "roll_no": r.roll_no, "name": r.name,
                "date": r.date, "time": r.time, "status": r.status,
                "confidence": r.confidence
            }
            for r in records
        ]
    }
