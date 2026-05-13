"""
Database Connection Module
Covers: SQLAlchemy ORM, SQLite (dev), PostgreSQL (prod), MongoDB (NoSQL)
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# ─── SQLAlchemy (SQL) ────────────────────────────────────────────────────────
os.makedirs("attendance_db", exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency: yields a database session, closes after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── MongoDB (NoSQL) ─────────────────────────────────────────────────────────
try:
    import motor.motor_asyncio
    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
    mongo_db = mongo_client[settings.MONGODB_DB]

    async def get_mongo_db():
        """Dependency: returns MongoDB database instance."""
        return mongo_db

except Exception:
    mongo_client = None
    mongo_db = None

    async def get_mongo_db():
        return None


# ─── Redis ───────────────────────────────────────────────────────────────────
try:
    import redis
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception:
    redis_client = None
