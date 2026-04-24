"""
Dashboard System with Data Lock
Requires "SRINIVAS" password to access dashboard data
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
import hashlib

class DashboardDataManager:
    def __init__(self):
        self.dashboard_db = "attendance_db/dashboard_data.db"
        self.lock_file = "attendance_db/dashboard_lock.json"
        self.master_key = "SRINIVAS"
        self.init_dashboard_db()
        self.init_lock_system()
    
    def init_dashboard_db(self):
        """Initialize dashboard database"""
        conn = sqlite3.connect(self.dashboard_db)
        cursor = conn.cursor()
        
        # Dashboard statistics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dashboard_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_students INTEGER DEFAULT 0,
                total_attendance INTEGER DEFAULT 0,
                present_today INTEGER DEFAULT 0,
                attendance_rate REAL DEFAULT 0.0,
                new_registrations INTEGER DEFAULT 0,
                face_verifications INTEGER DEFAULT 0,
                system_uptime TEXT,
                last_updated TEXT
            )
        ''')
        
        # Daily summary table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                students_present INTEGER DEFAULT 0,
                students_absent INTEGER DEFAULT 0,
                attendance_percentage REAL DEFAULT 0.0,
                peak_attendance_time TEXT,
                first_attendance_time TEXT,
                last_attendance_time TEXT,
                total_face_verifications INTEGER DEFAULT 0,
                average_confidence REAL DEFAULT 0.0
            )
        ''')
        
        # System logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                roll_no TEXT,
                description TEXT,
                confidence REAL,
                status TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def init_lock_system(self):
        """Initialize dashboard lock system"""
        if not os.path.exists(self.lock_file):
            lock_data = {
                "master_key_hash": hashlib.sha256(self.master_key.encode()).hexdigest(),
                "access_attempts": 0,
                "last_access": None,
                "locked_until": None,
                "authorized_sessions": []
            }
            
            with open(self.lock_file, 'w') as f:
                json.dump(lock_data, f, indent=2)
    
    def verify_access(self, password):
        """Verify access with password"""
        with open(self.lock_file, 'r') as f:
            lock_data = json.load(f)
        
        # Check if system is temporarily locked
        if lock_data.get("locked_until"):
            lock_time = datetime.fromisoformat(lock_data["locked_until"])
            if datetime.now() < lock_time:
                remaining = (lock_time - datetime.now()).seconds
                return False, f"System locked for {remaining} seconds due to failed attempts"
        
        # Verify password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if password_hash == lock_data["master_key_hash"]:
            # Successful access
            lock_data["access_attempts"] = 0
            lock_data["last_access"] = datetime.now().isoformat()
            lock_data["locked_until"] = None
            
            # Create session token
            session_token = hashlib.sha256(f"{password}{datetime.now()}".encode()).hexdigest()[:16]
            lock_data["authorized_sessions"].append({
                "token": session_token,
                "created": datetime.now().isoformat(),
                "expires": (datetime.now() + timedelta(hours=2)).isoformat()
            })
            
            with open(self.lock_file, 'w') as f:
                json.dump(lock_data, f, indent=2)
            
            return True, session_token
        else:
            # Failed access
            lock_data["access_attempts"] += 1
            
            # Lock system after 3 failed attempts
            if lock_data["access_attempts"] >= 3:
                lock_data["locked_until"] = (datetime.now() + timedelta(minutes=5)).isoformat()
                
            with open(self.lock_file, 'w') as f:
                json.dump(lock_data, f, indent=2)
            
            return False, f"Access denied. Attempts: {lock_data['access_attempts']}/3"
    
    def is_session_valid(self, session_token):
        """Check if session token is valid"""
        try:
            with open(self.lock_file, 'r') as f:
                lock_data = json.load(f)
            
            for session in lock_data.get("authorized_sessions", []):
                if session["token"] == session_token:
                    expires = datetime.fromisoformat(session["expires"])
                    if datetime.now() < expires:
                        return True
            return False
        except:
            return False
    
    def log_system_event(self, event_type, roll_no=None, description="", confidence=None, status="success"):
        """Log system events"""
        conn = sqlite3.connect(self.dashboard_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO system_logs (timestamp, event_type, roll_no, description, confidence, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            event_type,
            roll_no,
            description,
            confidence,
            status
        ))
        
        conn.commit()
        conn.close()
    
    def update_dashboard_stats(self):
        """Update dashboard statistics"""
        from student_face_attendance import DatabaseManager
        
        db_manager = DatabaseManager()
        
        # Get current statistics
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Count total students
        conn = sqlite3.connect("attendance_db/attendance.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM students")
        total_students = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM attendance")
        total_attendance = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM attendance WHERE date = ?", (today,))
        present_today = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM students WHERE registered_date = ?", (today,))
        new_registrations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM attendance WHERE date = ? AND verification_method = 'face_recognition'", (today,))
        face_verifications = cursor.fetchone()[0]
        
        conn.close()
        
        # Calculate attendance rate
        attendance_rate = (present_today / total_students * 100) if total_students > 0 else 0
        
        # Update dashboard database
        dash_conn = sqlite3.connect(self.dashboard_db)
        dash_cursor = dash_conn.cursor()
        
        dash_cursor.execute('''
            INSERT OR REPLACE INTO dashboard_stats 
            (date, total_students, total_attendance, present_today, attendance_rate, 
             new_registrations, face_verifications, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            today,
            total_students,
            total_attendance,
            present_today,
            attendance_rate,
            new_registrations,
            face_verifications,
            datetime.now().isoformat()
        ))
        
        dash_conn.commit()
        dash_conn.close()
        
        return {
            "total_students": total_students,
            "total_attendance": total_attendance,
            "present_today": present_today,
            "attendance_rate": attendance_rate,
            "new_registrations": new_registrations,
            "face_verifications": face_verifications
        }
    
    def get_dashboard_data(self, session_token):
        """Get dashboard data (requires valid session)"""
        if not self.is_session_valid(session_token):
            return None, "Session expired or invalid"
        
        try:
            # Update stats first
            current_stats = self.update_dashboard_stats()
            
            # Get historical data
            conn = sqlite3.connect(self.dashboard_db)
            cursor = conn.cursor()
            
            # Get last 7 days stats
            cursor.execute('''
                SELECT date, present_today, attendance_rate 
                FROM dashboard_stats 
                ORDER BY date DESC 
                LIMIT 7
            ''')
            weekly_data = cursor.fetchall()
            
            # Get recent system logs
            cursor.execute('''
                SELECT timestamp, event_type, roll_no, description, status 
                FROM system_logs 
                ORDER BY timestamp DESC 
                LIMIT 20
            ''')
            recent_logs = cursor.fetchall()
            
            # Get today's attendance details
            att_conn = sqlite3.connect("attendance_db/attendance.db")
            att_cursor = att_conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            att_cursor.execute('''
                SELECT roll_no, name, time, confidence, verification_method 
                FROM attendance 
                WHERE date = ? 
                ORDER BY time DESC
            ''', (today,))
            todays_attendance = att_cursor.fetchall()
            
            att_conn.close()
            conn.close()
            
            dashboard_data = {
                "current_stats": current_stats,
                "weekly_data": weekly_data,
                "recent_logs": recent_logs,
                "todays_attendance": todays_attendance,
                "last_updated": datetime.now().isoformat()
            }
            
            return dashboard_data, "Success"
            
        except Exception as e:
            return None, f"Error retrieving dashboard data: {str(e)}"
    
    def get_detailed_reports(self, session_token, report_type="weekly"):
        """Get detailed reports (requires valid session)"""
        if not self.is_session_valid(session_token):
            return None, "Session expired or invalid"
        
        try:
            conn = sqlite3.connect("attendance_db/attendance.db")
            cursor = conn.cursor()
            
            if report_type == "weekly":
                # Last 7 days detailed report
                week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                
                cursor.execute('''
                    SELECT date, COUNT(*) as present_count,
                           AVG(confidence) as avg_confidence
                    FROM attendance 
                    WHERE date >= ? 
                    GROUP BY date 
                    ORDER BY date DESC
                ''', (week_ago,))
                
                weekly_report = cursor.fetchall()
                
                # Student-wise attendance
                cursor.execute('''
                    SELECT s.roll_no, s.name, s.department,
                           COUNT(a.id) as days_present,
                           AVG(a.confidence) as avg_confidence
                    FROM students s
                    LEFT JOIN attendance a ON s.roll_no = a.roll_no 
                    AND a.date >= ?
                    GROUP BY s.roll_no, s.name, s.department
                    ORDER BY days_present DESC
                ''', (week_ago,))
                
                student_report = cursor.fetchall()
                
                conn.close()
                
                return {
                    "report_type": "weekly",
                    "period": f"Last 7 days (from {week_ago})",
                    "daily_summary": weekly_report,
                    "student_summary": student_report,
                    "generated_at": datetime.now().isoformat()
                }, "Success"
            
            elif report_type == "monthly":
                # Last 30 days report
                month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                
                cursor.execute('''
                    SELECT date, COUNT(*) as present_count
                    FROM attendance 
                    WHERE date >= ? 
                    GROUP BY date 
                    ORDER BY date DESC
                ''', (month_ago,))
                
                monthly_data = cursor.fetchall()
                
                conn.close()
                
                return {
                    "report_type": "monthly",
                    "period": f"Last 30 days (from {month_ago})",
                    "daily_data": monthly_data,
                    "generated_at": datetime.now().isoformat()
                }, "Success"
            
        except Exception as e:
            return None, f"Error generating report: {str(e)}"
    
    def export_data(self, session_token, export_type="all"):
        """Export data to JSON (requires valid session)"""
        if not self.is_session_valid(session_token):
            return None, "Session expired or invalid"
        
        try:
            export_data = {}
            
            # Export students data
            conn = sqlite3.connect("attendance_db/attendance.db")
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM students")
            students = cursor.fetchall()
            export_data["students"] = students
            
            cursor.execute("SELECT * FROM attendance")
            attendance = cursor.fetchall()
            export_data["attendance"] = attendance
            
            conn.close()
            
            # Export dashboard data
            dash_conn = sqlite3.connect(self.dashboard_db)
            dash_cursor = dash_conn.cursor()
            
            dash_cursor.execute("SELECT * FROM dashboard_stats")
            dashboard_stats = dash_cursor.fetchall()
            export_data["dashboard_stats"] = dashboard_stats
            
            dash_cursor.execute("SELECT * FROM system_logs")
            system_logs = dash_cursor.fetchall()
            export_data["system_logs"] = system_logs
            
            dash_conn.close()
            
            # Save to file
            export_filename = f"attendance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            export_path = os.path.join("attendance_db", export_filename)
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return export_path, "Data exported successfully"
            
        except Exception as e:
            return None, f"Error exporting data: {str(e)}"

# Initialize dashboard system
dashboard_manager = DashboardDataManager()