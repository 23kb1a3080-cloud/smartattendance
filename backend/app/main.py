"""
Smart Attendance System - FastAPI Main Application
Covers: FastAPI, REST APIs, Swagger Docs, Async APIs, CORS, Routing
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os

from app.config import settings
from app.database import Base, engine
from app import models
from app.routes import auth, students, attendance, dashboard

# ─── Create all DB tables ─────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Smart Face Attendance System API

A full-stack attendance management system with:
- 🔐 JWT Authentication
- 👤 Student Management
- 📋 Attendance Tracking
- 📊 Dashboard Analytics
- 🔴 Real-time WebSocket Updates
- 🐳 Docker Deployment Ready

### Tech Stack
- **Backend**: FastAPI + SQLAlchemy + SQLite/PostgreSQL
- **Auth**: JWT + bcrypt password hashing
- **Real-time**: WebSockets
- **Cache**: Redis
- **NoSQL**: MongoDB
    """,
    docs_url="/docs",          # Swagger UI
    redoc_url="/redoc",        # ReDoc UI
    openapi_url="/openapi.json"
)

# ─── CORS Middleware ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Include Routers ──────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(attendance.router)
app.include_router(dashboard.router)

# ─── Startup Event ────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    """Create default admin user on first run."""
    from app.database import SessionLocal
    from app.auth import hash_password

    db = SessionLocal()
    try:
        admin = db.query(models.User).filter(models.User.username == "admin").first()
        if not admin:
            admin_user = models.User(
                username="admin",
                email="admin@smartattendance.com",
                full_name="System Administrator",
                hashed_password=hash_password("admin123"),
                role="admin",
            )
            db.add(admin_user)

            # Default departments
            departments = [
                models.Department(name="Computer Science", code="CSE"),
                models.Department(name="Electronics", code="ECE"),
                models.Department(name="Mechanical", code="MECH"),
                models.Department(name="Civil", code="CIVIL"),
            ]
            db.add_all(departments)
            db.commit()
            print("✅ Default admin user created: admin / admin123")
            print("✅ Default departments created")
    except Exception as e:
        print(f"Startup warning: {e}")
    finally:
        db.close()


# ─── Root Endpoint ────────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "running"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for Docker/deployment."""
    return {"status": "healthy", "version": settings.APP_VERSION}
