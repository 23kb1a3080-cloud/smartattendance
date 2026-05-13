"""
Dashboard & Analytics Routes
Covers: Analytics, Reports, System Logs, WebSocket
"""
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import date, timedelta
import json, asyncio

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# ─── WebSocket Connection Manager ─────────────────────────────────────────────
class ConnectionManager:
    """Manages active WebSocket connections for real-time updates."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@router.get("/summary", response_model=schemas.DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Full dashboard summary with stats, recent records, weekly data.
    Covers: Analytics, Aggregation, Joins
    """
    today = date.today().strftime("%Y-%m-%d")
    total_students = db.query(models.Student).filter(models.Student.is_active == True).count()
    present_today = db.query(models.Attendance).filter(models.Attendance.date == today).count()
    absent_today = total_students - present_today
    total_records = db.query(models.Attendance).count()
    attendance_rate = round((present_today / total_students * 100) if total_students > 0 else 0, 2)

    stats = {
        "total_students": total_students,
        "present_today": present_today,
        "absent_today": absent_today,
        "attendance_rate": attendance_rate,
        "total_records": total_records,
    }

    # Recent attendance (last 10)
    recent = db.query(models.Attendance).order_by(
        models.Attendance.id.desc()
    ).limit(10).all()

    # Top students by attendance count
    top_students = db.query(
        models.Attendance.roll_no,
        models.Attendance.name,
        func.count(models.Attendance.id).label("count")
    ).group_by(models.Attendance.roll_no).order_by(
        func.count(models.Attendance.id).desc()
    ).limit(5).all()

    # Weekly data (last 7 days)
    weekly_data = []
    for i in range(6, -1, -1):
        day = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
        count = db.query(models.Attendance).filter(models.Attendance.date == day).count()
        weekly_data.append({"date": day, "count": count})

    return {
        "stats": stats,
        "recent_attendance": recent,
        "top_students": [
            {"roll_no": s.roll_no, "name": s.name, "count": s.count}
            for s in top_students
        ],
        "weekly_data": weekly_data,
    }


@router.get("/logs", response_model=List[schemas.SystemLogOut])
def get_system_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get recent system logs. Covers: Audit Trail, Logging."""
    return db.query(models.SystemLog).order_by(
        models.SystemLog.timestamp.desc()
    ).limit(limit).all()


@router.get("/weekly-report")
def get_weekly_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Generate a weekly attendance report."""
    report = []
    for i in range(6, -1, -1):
        day = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
        total = db.query(models.Student).filter(models.Student.is_active == True).count()
        present = db.query(models.Attendance).filter(models.Attendance.date == day).count()
        report.append({
            "date": day,
            "total_students": total,
            "present": present,
            "absent": total - present,
            "rate": round((present / total * 100) if total > 0 else 0, 2)
        })
    return {"report": report, "generated_at": date.today().isoformat()}


# ─── WebSocket: Real-time Attendance Feed ─────────────────────────────────────
@router.websocket("/ws/live")
async def websocket_live_attendance(websocket: WebSocket):
    """
    WebSocket endpoint for real-time attendance updates.
    Covers: WebSockets, Real-time Communication
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back with timestamp
            await websocket.send_json({
                "type": "ping",
                "message": "connected",
                "data": data
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def broadcast_attendance_update(record: dict):
    """Broadcast new attendance to all WebSocket clients."""
    await manager.broadcast({
        "type": "attendance_update",
        "data": record
    })
