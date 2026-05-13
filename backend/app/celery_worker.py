"""
Celery Background Tasks
Covers: Celery, Async Tasks, Background Processing
"""
from celery import Celery
from app.config import settings

# ─── Celery App ───────────────────────────────────────────────────────────────
celery_app = Celery(
    "smart_attendance",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
)
