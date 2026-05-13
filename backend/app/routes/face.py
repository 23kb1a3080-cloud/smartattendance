"""
Face Recognition Attendance Route
Covers: REST API, File Upload, OpenCV, face_recognition, Real-time verification
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import date, datetime
import numpy as np
import pickle
import os
import io

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db
from app.config import settings

router = APIRouter(prefix="/api/face", tags=["Face Recognition"])

# ─── Lazy-load heavy libs so server starts even without them ──────────────────
def _load_cv2():
    import cv2
    return cv2

def _load_face_recognition():
    try:
        import face_recognition
        return face_recognition
    except ImportError:
        return None

def _load_encodings():
    """Load face encodings from pickle file."""
    paths_to_try = [
        settings.ENCODINGS_PATH,
        "../FaceAttendance/encodings/encodings.pkl",
        "FaceAttendance/encodings/encodings.pkl",
        os.path.join(os.path.dirname(__file__), "../../../../FaceAttendance/encodings/encodings.pkl"),
    ]
    for path in paths_to_try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return pickle.load(f)
    return None


@router.post("/verify")
async def verify_face(
    frame: UploadFile = File(..., description="JPEG frame from webcam"),
    roll_no: str = Form(..., description="Student roll number to verify"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Verify a face frame against stored encodings.
    Returns match status, confidence, and bounding box.
    Called every ~500ms from the browser webcam feed.
    """
    cv2 = _load_cv2()
    fr = _load_face_recognition()

    if fr is None:
        # Fallback: OpenCV-only detection (no recognition, just detect)
        contents = await frame.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))

        if len(faces) == 0:
            return {"detected": False, "matched": False, "confidence": 0,
                    "message": "No face detected", "box": None}

        x, y, w, h = [int(v) for v in faces[0]]
        return {
            "detected": True,
            "matched": False,
            "confidence": 0,
            "message": "Face detected (face_recognition not installed — install dlib for matching)",
            "box": {"x": x, "y": y, "w": w, "h": h},
            "roll_no": roll_no,
        }

    # ── Full face_recognition path ────────────────────────────────────────────
    contents = await frame.read()
    nparr = np.frombuffer(contents, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise HTTPException(status_code=400, detail="Invalid image data")

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # Detect faces
    face_locations = fr.face_locations(img_rgb, model="hog")
    if not face_locations:
        return {"detected": False, "matched": False, "confidence": 0,
                "message": "No face detected", "box": None}

    # Encode detected face
    encodings = fr.face_encodings(img_rgb, face_locations)
    if not encodings:
        return {"detected": False, "matched": False, "confidence": 0,
                "message": "Could not encode face", "box": None}

    detected_encoding = encodings[0]
    top, right, bottom, left = face_locations[0]
    box = {"x": left, "y": top, "w": right - left, "h": bottom - top}

    # Load known encodings
    data = _load_encodings()
    if data is None:
        return {
            "detected": True, "matched": False, "confidence": 0,
            "message": "No trained encodings found. Please train the model first.",
            "box": box,
        }

    known_encodings = data.get("encodings", [])
    known_rolls = data.get("roll_numbers", [])

    if not known_encodings:
        return {"detected": True, "matched": False, "confidence": 0,
                "message": "Encodings file is empty", "box": box}

    # Compare
    distances = fr.face_distance(known_encodings, detected_encoding)
    min_idx = int(np.argmin(distances))
    min_dist = float(distances[min_idx])
    confidence = round(float(1 - min_dist), 4)
    matched_roll = known_rolls[min_idx]

    THRESHOLD = settings.MATCH_THRESHOLD  # 0.45

    if min_dist > THRESHOLD:
        return {
            "detected": True, "matched": False,
            "confidence": confidence,
            "message": f"Face not recognized (distance {min_dist:.3f})",
            "box": box,
        }

    if matched_roll != roll_no:
        return {
            "detected": True, "matched": False,
            "confidence": confidence,
            "message": f"Face belongs to {matched_roll}, not {roll_no}",
            "box": box,
            "matched_roll": matched_roll,
        }

    # ── Match confirmed ───────────────────────────────────────────────────────
    return {
        "detected": True,
        "matched": True,
        "confidence": confidence,
        "message": f"Identity verified ✓",
        "box": box,
        "roll_no": roll_no,
        "distance": round(min_dist, 4),
    }


@router.post("/mark-verified", response_model=schemas.AttendanceOut, status_code=201)
async def mark_verified_attendance(
    roll_no: str = Form(...),
    confidence: float = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Mark attendance after face has been verified.
    Called once after successful face match.
    """
    student = db.query(models.Student).filter(models.Student.roll_no == roll_no).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student {roll_no} not found in web system. Add them in Students page first.")

    today = date.today().strftime("%Y-%m-%d")
    now   = datetime.now().strftime("%H:%M:%S")

    existing = db.query(models.Attendance).filter(
        models.Attendance.roll_no == roll_no,
        models.Attendance.date == today,
    ).first()

    if existing:
        # Return existing record — already marked
        return existing

    record = models.Attendance(
        roll_no=roll_no,
        name=student.name,
        date=today,
        time=now,
        status="Present",
        confidence=confidence,
        verification_method="face_recognition",
    )
    db.add(record)

    log = models.SystemLog(
        event_type="attendance_marked",
        roll_no=roll_no,
        description=f"Face-verified attendance for {student.name} (conf={confidence:.2%})",
        confidence=confidence,
        status="success",
    )
    db.add(log)
    db.commit()
    db.refresh(record)
    return record


@router.get("/status")
def face_recognition_status():
    """Check if face_recognition library is available."""
    fr = _load_face_recognition()
    data = _load_encodings()
    enrolled = 0
    if data:
        enrolled = len(set(data.get("roll_numbers", [])))
    return {
        "face_recognition_available": fr is not None,
        "encodings_found": data is not None,
        "enrolled_students": enrolled,
    }
