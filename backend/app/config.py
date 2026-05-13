"""
Configuration settings using pydantic-settings
Covers: Environment Variables, Security, Database, Redis
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Smart Attendance System"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # Security / JWT
    SECRET_KEY: str = "smartattendance-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # Database (SQLite default, PostgreSQL in production)
    DATABASE_URL: str = "sqlite:///./attendance_db/attendance.db"

    # MongoDB (NoSQL)
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "smart_attendance"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    ALLOWED_ORIGINS: list = [
        "http://localhost",
        "http://localhost:80",
        "http://localhost:3000",
        "http://127.0.0.1:5500",
        "*"
    ]

    # File Storage
    DATASET_PATH: str = "../FaceAttendance/dataset"
    ENCODINGS_PATH: str = "../FaceAttendance/encodings/encodings.pkl"
    UPLOAD_DIR: str = "./uploads"

    # Face Recognition
    MATCH_THRESHOLD: float = 0.45
    NUM_IMAGES: int = 20

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
