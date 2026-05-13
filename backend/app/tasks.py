"""
Celery Background Tasks
Covers: Celery, Background Jobs, Async Processing
"""
from app.celery_worker import celery_app
import os, pickle
import numpy as np


@celery_app.task(name="train_face_encodings")
def train_face_encodings_task(dataset_path: str, encodings_path: str):
    """
    Background task: Train face encodings from dataset.
    Runs asynchronously so the API doesn't block.
    Covers: Celery Tasks, Background Processing
    """
    try:
        import cv2
        try:
            import face_recognition
            use_face_recognition = True
        except ImportError:
            use_face_recognition = False

        known_encodings = []
        known_roll_numbers = []
        known_names = []

        if not os.path.exists(dataset_path):
            return {"status": "error", "message": f"Dataset path not found: {dataset_path}"}

        for roll_no in os.listdir(dataset_path):
            student_path = os.path.join(dataset_path, roll_no)
            if not os.path.isdir(student_path):
                continue

            for img_file in os.listdir(student_path):
                if not img_file.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue

                img_path = os.path.join(student_path, img_file)

                if use_face_recognition:
                    image = face_recognition.load_image_file(img_path)
                    encodings = face_recognition.face_encodings(image)
                    if encodings:
                        known_encodings.append(encodings[0])
                        known_roll_numbers.append(roll_no)
                        known_names.append(roll_no)
                else:
                    img = cv2.imread(img_path)
                    if img is not None:
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        resized = cv2.resize(gray, (128, 128))
                        known_encodings.append(resized.flatten().astype(np.float64))
                        known_roll_numbers.append(roll_no)
                        known_names.append(roll_no)

        os.makedirs(os.path.dirname(encodings_path), exist_ok=True)
        data = {
            "encodings": known_encodings,
            "roll_numbers": known_roll_numbers,
            "names": known_names
        }
        with open(encodings_path, "wb") as f:
            pickle.dump(data, f)

        return {
            "status": "success",
            "message": f"Trained {len(known_encodings)} encodings",
            "students": len(set(known_roll_numbers))
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


@celery_app.task(name="generate_daily_report")
def generate_daily_report_task(date_str: str):
    """
    Background task: Generate daily attendance report.
    Covers: Celery Scheduled Tasks
    """
    from app.database import SessionLocal
    from app import models

    db = SessionLocal()
    try:
        records = db.query(models.Attendance).filter(
            models.Attendance.date == date_str
        ).all()

        total = db.query(models.Student).filter(models.Student.is_active == True).count()
        present = len(records)

        return {
            "status": "success",
            "date": date_str,
            "total_students": total,
            "present": present,
            "absent": total - present,
            "rate": round((present / total * 100) if total > 0 else 0, 2)
        }
    finally:
        db.close()
