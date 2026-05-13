# 🎓 Smart Face Attendance System

A **full-stack** face recognition attendance system covering the complete developer roadmap — from Python basics to Docker deployment.

---

## 🗺️ Roadmap Coverage

| # | Topic | Implementation |
|---|-------|---------------|
| 1 | Computer Basics | VS Code, Command Line, OS |
| 2 | Python Basics | Variables, Loops, Functions, File Handling |
| 3 | Advanced Python | OOP, Modules, Decorators, Virtual Env |
| 4 | Git & GitHub | Version control, branches, CI/CD |
| 5 | Frontend (HTML/CSS/JS) | Responsive dashboard, Flexbox, Grid, Animations |
| 6 | Frontend Framework | Vanilla JS modules (React-ready structure) |
| 7 | Databases | SQLite + PostgreSQL (SQLAlchemy) + MongoDB |
| 8 | Python Backend | **FastAPI** REST API + Celery background tasks |
| 9 | APIs & Backend Services | REST, JSON, HTTP Methods, JWT Auth, Postman |
| 10 | Database Connection | SQLAlchemy ORM + Motor (MongoDB async) |
| 11 | Authentication | Login/Signup, bcrypt, JWT Tokens, Sessions |
| 12 | Testing | Pytest, Unit Tests, API Tests |
| 13 | Deployment | Docker, Nginx, Gunicorn/Uvicorn, CI/CD |
| 14 | Hosting | Render, Railway, Vercel configs included |
| 15 | Advanced Concepts | Redis, Celery, WebSockets, Microservices |

---

## 🏗️ Architecture

```
smartattendance/
├── FaceAttendance/          ← Desktop App (CustomTkinter + OpenCV)
│   ├── modern_attendance.py ← Main desktop GUI
│   ├── registration.py      ← Face capture
│   ├── train_model.py       ← Face encoding
│   └── attendance.py        ← Face recognition
│
├── backend/                 ← FastAPI REST API
│   ├── app/
│   │   ├── main.py          ← FastAPI app + Swagger docs
│   │   ├── models.py        ← SQLAlchemy ORM models
│   │   ├── schemas.py       ← Pydantic validation
│   │   ├── database.py      ← SQLite + MongoDB + Redis
│   │   ├── auth.py          ← JWT + bcrypt
│   │   ├── tasks.py         ← Celery background tasks
│   │   └── routes/
│   │       ├── auth.py      ← Login, Signup, JWT
│   │       ├── students.py  ← Student CRUD
│   │       ├── attendance.py← Attendance CRUD
│   │       └── dashboard.py ← Analytics + WebSocket
│   └── tests/               ← Pytest test suite
│
├── frontend/                ← HTML/CSS/JS Web App
│   ├── index.html           ← Login/Signup
│   ├── dashboard.html       ← Analytics dashboard
│   ├── students.html        ← Student management
│   ├── attendance.html      ← Attendance records
│   ├── reports.html         ← Weekly reports + charts
│   ├── logs.html            ← System audit logs
│   ├── css/style.css        ← Full responsive CSS
│   └── js/
│       ├── api.js           ← API client + WebSocket
│       └── layout.js        ← Shared navbar/sidebar
│
├── nginx/nginx.conf         ← Reverse proxy config
├── docker-compose.yml       ← Full stack Docker setup
├── .github/workflows/       ← CI/CD pipeline
├── render.yaml              ← Render hosting
├── railway.config.json      ← Railway hosting
└── vercel.config.json       ← Vercel hosting
```

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)
```bash
# Start everything with one command
docker-compose up --build

# Access:
# Web App:    http://localhost
# API Docs:   http://localhost/docs
# ReDoc:      http://localhost/redoc
```

### Option 2: Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
# Open frontend/index.html in browser
# Or use Live Server in VS Code
```

**Desktop App:**
```bash
cd FaceAttendance
pip install -r ../requirements.txt
python modern_attendance.py
```

---

## 🔐 Default Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin |

> ⚠️ Change the password after first login in production!

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup` | Register new user |
| POST | `/api/auth/login` | Login + get JWT |
| GET | `/api/auth/me` | Current user |
| GET | `/api/students/` | List students |
| POST | `/api/students/` | Add student |
| PUT | `/api/students/{roll_no}` | Update student |
| DELETE | `/api/students/{roll_no}` | Delete student |
| POST | `/api/attendance/mark` | Mark attendance |
| GET | `/api/attendance/today` | Today's records |
| GET | `/api/attendance/stats` | Statistics |
| GET | `/api/attendance/export/json` | Export data |
| GET | `/api/dashboard/summary` | Dashboard data |
| GET | `/api/dashboard/weekly-report` | Weekly report |
| WS | `/api/dashboard/ws/live` | Real-time feed |

Full interactive docs: **http://localhost:8000/docs**

---

## 🧪 Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## 🐳 Docker Services

| Service | Port | Description |
|---------|------|-------------|
| nginx | 80 | Reverse proxy |
| frontend | — | HTML/CSS/JS app |
| backend | 8000 | FastAPI API |
| celery_worker | — | Background tasks |
| redis | 6379 | Cache + task broker |
| mongo | 27017 | NoSQL database |

---

## ☁️ Hosting

### Render
```bash
# Push to GitHub, connect repo at render.com
# render.yaml is pre-configured
```

### Railway
```bash
railway login
railway up
```

### Vercel (Frontend only)
```bash
vercel --cwd frontend
```

---

## 🛠️ Tech Stack

**Backend:** Python 3.11, FastAPI, SQLAlchemy, Pydantic, JWT, bcrypt, Celery  
**Database:** SQLite (dev), PostgreSQL (prod), MongoDB, Redis  
**Frontend:** HTML5, CSS3, Vanilla JS, Chart.js  
**Desktop:** Python, OpenCV, face_recognition, CustomTkinter, MediaPipe  
**DevOps:** Docker, Docker Compose, Nginx, GitHub Actions, CI/CD  
**Hosting:** Render, Railway, Vercel  

---

## 📄 License

MIT License — Free to use for educational purposes.
