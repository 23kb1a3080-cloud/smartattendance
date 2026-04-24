"""
Student Face Attendance System
Advanced face recognition system where students only need roll number for attendance
"""

import cv2
import numpy as np
import sqlite3
import os
import threading
import time
from datetime import datetime
from PIL import Image, ImageTk
import customtkinter as ctk
from tkinter import messagebox, simpledialog
import pickle
import json

# Try to import face_recognition, use fallback if not available
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("Warning: face_recognition library not available. Using basic OpenCV matching.")

# Import dashboard system
from dashboard_system import dashboard_manager

# Configuration
DATASET_PATH = "dataset"
ATTENDANCE_DB = "attendance_db/attendance.db"
DATABASE_FOLDER = "attendance_db"
ENCODINGS_PATH = "encodings/face_encodings.pkl"
ENCODINGS_FOLDER = "encodings"

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Custom color scheme
COLORS = {
    "primary": "#1f538d",
    "secondary": "#14375e", 
    "success": "#2d5a27",
    "warning": "#8b5a00",
    "danger": "#8b2635",
    "info": "#1e3a5f",
    "light": "#f8f9fa",
    "dark": "#212529",
    "background": "#0d1117",
    "surface": "#161b22",
    "accent": "#58a6ff"
}

class FaceRecognitionSystem:
    def __init__(self):
        self.known_encodings = []
        self.known_roll_numbers = []
        self.known_names = []
        self.face_recognition_available = self._check_face_recognition()
        
    def _check_face_recognition(self):
        """Check if face_recognition library is available"""
        return FACE_RECOGNITION_AVAILABLE
    
    def load_encodings(self):
        """Load face encodings from file"""
        if os.path.exists(ENCODINGS_PATH):
            try:
                with open(ENCODINGS_PATH, 'rb') as f:
                    data = pickle.load(f)
                    self.known_encodings = data['encodings']
                    self.known_roll_numbers = data['roll_numbers']
                    self.known_names = data['names']
                print(f"Loaded {len(self.known_encodings)} face encodings")
                return True
            except Exception as e:
                print(f"Error loading encodings: {e}")
                return False
        return False
    
    def generate_encodings_for_student(self, roll_number):
        """Generate face encodings for a specific student"""
        if not self.face_recognition_available:
            print("Face recognition not available, using basic matching")
            return True
            
        student_path = os.path.join(DATASET_PATH, roll_number)
        if not os.path.exists(student_path):
            return False
            
        images = [f for f in os.listdir(student_path) if f.endswith(('.jpg', '.jpeg', '.png'))]
        if not images:
            return False
            
        encodings = []
        for image_file in images[:10]:  # Use first 10 images
            image_path = os.path.join(student_path, image_file)
            try:
                image = face_recognition.load_image_file(image_path)
                face_locations = face_recognition.face_locations(image)
                if face_locations:
                    encoding = face_recognition.face_encodings(image, face_locations)[0]
                    encodings.append(encoding)
            except Exception as e:
                print(f"Error processing {image_file}: {e}")
                continue
        
        if encodings:
            # Average the encodings for better accuracy
            avg_encoding = np.mean(encodings, axis=0)
            return avg_encoding
        return None
    
    def update_encodings(self, roll_number, name):
        """Update encodings with new student"""
        if not self.face_recognition_available:
            # For basic mode, just return True as we'll use template matching
            print(f"Basic mode: Student {roll_number} ready for template matching")
            return True
            
        encoding = self.generate_encodings_for_student(roll_number)
        if encoding is not None:
            # Load existing encodings
            self.load_encodings()
            
            # Add new encoding
            self.known_encodings.append(encoding)
            self.known_roll_numbers.append(roll_number)
            self.known_names.append(name)
            
            # Save updated encodings
            os.makedirs(ENCODINGS_FOLDER, exist_ok=True)
            data = {
                'encodings': self.known_encodings,
                'roll_numbers': self.known_roll_numbers,
                'names': self.known_names
            }
            
            with open(ENCODINGS_PATH, 'wb') as f:
                pickle.dump(data, f)
            
            print(f"Updated encodings for {roll_number}")
            return True
        return False
    
    def recognize_face(self, frame, target_roll_number):
        """Recognize face and verify against target roll number"""
        if not self.face_recognition_available:
            # Fallback to basic face detection with simple matching
            return self._basic_face_matching(frame, target_roll_number)
            
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find faces
            face_locations = face_recognition.face_locations(rgb_frame)
            if not face_locations:
                return False, 0.0, "No face detected"
            
            # Get encodings
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            if not face_encodings:
                return False, 0.0, "Could not encode face"
            
            # Compare with known faces
            for face_encoding in face_encodings:
                distances = face_recognition.face_distance(self.known_encodings, face_encoding)
                
                if len(distances) > 0:
                    min_distance = min(distances)
                    best_match_index = np.argmin(distances)
                    
                    if min_distance < 0.5:  # Threshold for recognition
                        matched_roll = self.known_roll_numbers[best_match_index]
                        confidence = 1 - min_distance
                        
                        if matched_roll == target_roll_number:
                            return True, confidence, f"Verified: {matched_roll}"
                        else:
                            return False, confidence, f"Face matches {matched_roll}, not {target_roll_number}"
            
            return False, 0.0, "Face not recognized"
            
        except Exception as e:
            return False, 0.0, f"Recognition error: {str(e)}"
    
    def _basic_face_matching(self, frame, target_roll_number):
        """Basic face matching using template matching"""
        # Check if student has registered images
        student_path = os.path.join(DATASET_PATH, target_roll_number)
        if not os.path.exists(student_path):
            return False, 0.0, "Student not registered"
        
        # Get reference images
        images = [f for f in os.listdir(student_path) if f.endswith(('.jpg', '.jpeg', '.png'))]
        if not images:
            return False, 0.0, "No reference images found"
        
        # Detect face in current frame
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            return False, 0.0, "No face detected"
        
        # Use the largest face
        largest_face = max(faces, key=lambda x: x[2] * x[3])
        x, y, w, h = largest_face
        
        # Extract face region
        face_roi = gray[y:y+h, x:x+w]
        
        # Compare with reference images using template matching
        max_confidence = 0.0
        
        try:
            # Load and compare with first few reference images
            for i, img_file in enumerate(images[:5]):  # Use first 5 images
                ref_path = os.path.join(student_path, img_file)
                ref_img = cv2.imread(ref_path, cv2.IMREAD_GRAYSCALE)
                
                if ref_img is not None:
                    # Resize reference image to match detected face size
                    ref_resized = cv2.resize(ref_img, (w, h))
                    
                    # Calculate similarity using normalized correlation
                    result = cv2.matchTemplate(face_roi, ref_resized, cv2.TM_CCOEFF_NORMED)
                    confidence = result[0][0]
                    
                    if confidence > max_confidence:
                        max_confidence = confidence
            
            # Threshold for basic matching (lower than face_recognition)
            if max_confidence > 0.3:  # Adjusted threshold for template matching
                return True, max_confidence, f"Face matched (basic mode)"
            else:
                return False, max_confidence, "Face not recognized (basic mode)"
                
        except Exception as e:
            return False, 0.0, f"Basic matching error: {str(e)}"

class DatabaseManager:
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database"""
        os.makedirs(DATABASE_FOLDER, exist_ok=True)
        
        conn = sqlite3.connect(ATTENDANCE_DB)
        cursor = conn.cursor()
        
        # Create students table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                department TEXT,
                registered_date TEXT NOT NULL,
                face_encoded INTEGER DEFAULT 0
            )
        ''')
        
        # Create attendance table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no TEXT NOT NULL,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                verification_method TEXT DEFAULT 'face_recognition',
                UNIQUE(roll_no, date),
                FOREIGN KEY (roll_no) REFERENCES students (roll_no)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_student(self, roll_no, name, department="Unknown"):
        """Register a new student"""
        try:
            conn = sqlite3.connect(ATTENDANCE_DB)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO students (roll_no, name, department, registered_date, face_encoded)
                VALUES (?, ?, ?, ?, 0)
            ''', (roll_no, name, department, datetime.now().strftime('%Y-%m-%d')))
            
            conn.commit()
            conn.close()
            return True, "Student registered successfully"
        except Exception as e:
            return False, f"Registration failed: {str(e)}"
    
    def update_face_encoded_status(self, roll_no, status=1):
        """Update face encoding status for student"""
        try:
            conn = sqlite3.connect(ATTENDANCE_DB)
            cursor = conn.cursor()
            
            cursor.execute(
                'UPDATE students SET face_encoded = ? WHERE roll_no = ?',
                (status, roll_no)
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating face encoded status: {e}")
            return False
    
    def get_student_info(self, roll_no):
        """Get student information"""
        conn = sqlite3.connect(ATTENDANCE_DB)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT roll_no, name, department, face_encoded FROM students WHERE roll_no = ?',
            (roll_no,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        return result
    
    def check_duplicate_attendance(self, roll_no, date):
        """Check if attendance already marked"""
        conn = sqlite3.connect(ATTENDANCE_DB)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id FROM attendance WHERE roll_no = ? AND date = ?',
            (roll_no, date)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
    
    def mark_attendance(self, roll_no, name, status, confidence=1.0, method="face_recognition"):
        """Mark attendance"""
        date = datetime.now().strftime('%Y-%m-%d')
        
        if self.check_duplicate_attendance(roll_no, date):
            return False, "Attendance already marked today"
        
        try:
            conn = sqlite3.connect(ATTENDANCE_DB)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO attendance (roll_no, name, date, time, status, confidence, verification_method)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                roll_no, name, date,
                datetime.now().strftime('%H:%M:%S'),
                status, confidence, method
            ))
            
            conn.commit()
            conn.close()
            return True, "Attendance marked successfully"
        except Exception as e:
            return False, f"Failed to mark attendance: {str(e)}"
    
    def get_attendance_records(self, limit=100):
        """Get attendance records"""
        conn = sqlite3.connect(ATTENDANCE_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT roll_no, name, date, time, status, confidence, verification_method 
            FROM attendance 
            ORDER BY date DESC, time DESC 
            LIMIT ?
        ''', (limit,))
        
        records = cursor.fetchall()
        conn.close()
        
        return records

class CameraManager:
    def __init__(self):
        self.cap = None
        self.is_running = False
        
    def start_camera(self, camera_index=0):
        """Start camera capture"""
        try:
            self.cap = cv2.VideoCapture(camera_index)
            if not self.cap.isOpened():
                return False, "Could not open camera"
            
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.is_running = True
            return True, "Camera started successfully"
        except Exception as e:
            return False, f"Camera error: {str(e)}"
    
    def read_frame(self):
        """Read frame from camera"""
        if self.cap and self.is_running:
            ret, frame = self.cap.read()
            if ret:
                return cv2.flip(frame, 1)  # Mirror effect
        return None
    
    def stop_camera(self):
        """Stop camera capture"""
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None

class StudentFaceAttendanceApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Student Face Attendance System")
        self.root.geometry("1000x800")
        
        # Set custom background colors
        self.root.configure(fg_color=COLORS["background"])
        
        # Initialize components
        self.face_recognition_system = FaceRecognitionSystem()
        self.db_manager = DatabaseManager()
        self.camera_manager = CameraManager()
        
        # Load existing face encodings
        self.face_recognition_system.load_encodings()
        
        # Variables
        self.current_mode = "idle"  # idle, registration, attendance
        self.capture_count = 0
        self.max_captures = 20
        self.current_roll_no = ""
        self.current_name = ""
        self.verification_frames = 0
        self.required_verification_frames = 30  # ~1 second at 30fps
        self.dashboard_session = None  # Dashboard session token
        self.detected_students = []  # Store detected students for dashboard
        
        # Create GUI
        self.create_widgets()
        
        # Start camera thread
        self.camera_thread = None
        self.running = True
        
    def create_widgets(self):
        """Create modern GUI widgets with custom colors"""
        # Main container with custom background
        main_frame = ctk.CTkFrame(self.root, fg_color=COLORS["surface"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title with accent color
        title_label = ctk.CTkLabel(
            main_frame,
            text="🎓 Student Face Attendance System",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["accent"]
        )
        title_label.pack(pady=20)
        
        # Mode selection with custom colors
        mode_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["primary"])
        mode_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            mode_frame, 
            text="Select Mode:", 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["light"]
        ).pack(pady=10)
        
        mode_buttons_frame = ctk.CTkFrame(mode_frame, fg_color="transparent")
        mode_buttons_frame.pack(pady=10)
        
        self.registration_mode_btn = ctk.CTkButton(
            mode_buttons_frame,
            text="📝 Student Registration",
            command=self.switch_to_registration_mode,
            width=200,
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["success"],
            hover_color=COLORS["secondary"]
        )
        self.registration_mode_btn.pack(side="left", padx=10)
        
        self.attendance_mode_btn = ctk.CTkButton(
            mode_buttons_frame,
            text="✅ Face Attendance",
            command=self.switch_to_attendance_mode,
            width=200,
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["info"],
            hover_color=COLORS["secondary"]
        )
        self.attendance_mode_btn.pack(side="left", padx=10)
        
        self.dashboard_mode_btn = ctk.CTkButton(
            mode_buttons_frame,
            text="📊 Dashboard (Locked)",
            command=self.open_dashboard,
            width=200,
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["danger"],
            hover_color=COLORS["warning"]
        )
        self.dashboard_mode_btn.pack(side="left", padx=10)
        
        # Input section with custom background
        self.input_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["dark"])
        self.input_frame.pack(fill="x", padx=20, pady=10)
        
        # Registration inputs (initially visible)
        self.registration_inputs = ctk.CTkFrame(self.input_frame, fg_color=COLORS["success"])
        self.registration_inputs.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            self.registration_inputs, 
            text="Student Registration", 
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["light"]
        ).pack(pady=10)
        
        reg_input_frame = ctk.CTkFrame(self.registration_inputs, fg_color="transparent")
        reg_input_frame.pack(pady=10)
        
        ctk.CTkLabel(
            reg_input_frame, 
            text="Roll Number:", 
            font=ctk.CTkFont(size=14),
            text_color=COLORS["light"]
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.reg_roll_entry = ctk.CTkEntry(
            reg_input_frame, 
            placeholder_text="Enter roll number", 
            width=200,
            fg_color=COLORS["light"],
            text_color=COLORS["dark"]
        )
        self.reg_roll_entry.grid(row=0, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(
            reg_input_frame, 
            text="Name:", 
            font=ctk.CTkFont(size=14),
            text_color=COLORS["light"]
        ).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.reg_name_entry = ctk.CTkEntry(
            reg_input_frame, 
            placeholder_text="Enter student name", 
            width=200,
            fg_color=COLORS["light"],
            text_color=COLORS["dark"]
        )
        self.reg_name_entry.grid(row=1, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(
            reg_input_frame, 
            text="Department:", 
            font=ctk.CTkFont(size=14),
            text_color=COLORS["light"]
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.reg_dept_entry = ctk.CTkEntry(
            reg_input_frame, 
            placeholder_text="Enter department", 
            width=200,
            fg_color=COLORS["light"],
            text_color=COLORS["dark"]
        )
        self.reg_dept_entry.grid(row=2, column=1, padx=10, pady=5)
        
        self.start_registration_btn = ctk.CTkButton(
            self.registration_inputs,
            text="📸 Start Registration",
            command=self.start_registration,
            width=250,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["primary"]
        )
        self.start_registration_btn.pack(pady=10)
        
        # Attendance inputs (initially hidden)
        self.attendance_inputs = ctk.CTkFrame(self.input_frame, fg_color=COLORS["info"])
        
        ctk.CTkLabel(
            self.attendance_inputs, 
            text="Face Attendance Verification", 
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["light"]
        ).pack(pady=10)
        
        att_input_frame = ctk.CTkFrame(self.attendance_inputs, fg_color="transparent")
        att_input_frame.pack(pady=10)
        
        ctk.CTkLabel(
            att_input_frame, 
            text="Roll Number:", 
            font=ctk.CTkFont(size=14),
            text_color=COLORS["light"]
        ).pack(side="left", padx=10)
        self.att_roll_entry = ctk.CTkEntry(
            att_input_frame, 
            placeholder_text="Enter your roll number", 
            width=200,
            fg_color=COLORS["light"],
            text_color=COLORS["dark"]
        )
        self.att_roll_entry.pack(side="left", padx=10)
        
        self.start_attendance_btn = ctk.CTkButton(
            self.attendance_inputs,
            text="🔍 Verify Face & Mark Attendance",
            command=self.start_attendance,
            width=300,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["primary"]
        )
        self.start_attendance_btn.pack(pady=10)
        
        # Camera section with dark background
        camera_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["dark"])
        camera_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.camera_label = ctk.CTkLabel(
            camera_frame, 
            text="Camera Feed", 
            width=640, 
            height=480,
            fg_color=COLORS["background"]
        )
        self.camera_label.pack(pady=20)
        
        # Control buttons with custom colors
        control_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["secondary"])
        control_frame.pack(fill="x", padx=20, pady=10)
        
        self.records_btn = ctk.CTkButton(
            control_frame,
            text="📊 View Attendance Records",
            command=self.show_records,
            width=200,
            height=40,
            fg_color=COLORS["info"],
            hover_color=COLORS["primary"]
        )
        self.records_btn.pack(side="left", padx=10)
        
        self.stop_btn = ctk.CTkButton(
            control_frame,
            text="⏹️ Stop Camera",
            command=self.stop_current_operation,
            width=150,
            height=40,
            fg_color=COLORS["danger"],
            hover_color=COLORS["warning"]
        )
        self.stop_btn.pack(side="right", padx=10)
        
        # Status section with accent color
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="System Ready - Select a mode to begin",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["accent"]
        )
        self.status_label.pack(pady=10)
        
        # Progress bar with custom color
        self.progress_bar = ctk.CTkProgressBar(
            main_frame, 
            width=600,
            progress_color=COLORS["accent"]
        )
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        # Initially show registration mode
        self.switch_to_registration_mode()
        
    def switch_to_registration_mode(self):
        """Switch to registration mode"""
        self.attendance_inputs.pack_forget()
        self.registration_inputs.pack(fill="x", pady=10)
        self.update_status("Registration Mode - Enter student details and start registration", COLORS["accent"])
        
    def switch_to_attendance_mode(self):
        """Switch to attendance mode"""
        self.registration_inputs.pack_forget()
        self.attendance_inputs.pack(fill="x", pady=10)
        self.update_status("Attendance Mode - Enter roll number for face verification", COLORS["accent"])
        
    def update_status(self, message, color=None):
        """Update status message with color"""
        if color is None:
            color = COLORS["accent"]
        self.status_label.configure(text=message, text_color=color)
        self.root.update()
        
    def start_camera_thread(self):
        """Start camera processing thread"""
        if self.camera_thread and self.camera_thread.is_alive():
            return
            
        self.camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
        self.camera_thread.start()
        
    def camera_loop(self):
        """Main camera processing loop"""
        success, message = self.camera_manager.start_camera()
        if not success:
            self.update_status(f"Camera Error: {message}", "red")
            return
            
        while self.running and self.camera_manager.is_running:
            frame = self.camera_manager.read_frame()
            if frame is None:
                continue
                
            # Process frame based on current mode
            if self.current_mode == "registration":
                frame = self.process_registration_frame(frame)
            elif self.current_mode == "attendance":
                frame = self.process_attendance_frame(frame)
            else:
                # Idle mode - just show camera feed
                cv2.putText(frame, "Camera Ready", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
            # Display frame
            self.display_frame(frame)
            time.sleep(0.03)  # ~30 FPS
            
        self.camera_manager.stop_camera()
        
    def display_frame(self, frame):
        """Display frame in GUI"""
        try:
            # Resize frame to fit display
            frame = cv2.resize(frame, (640, 480))
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(rgb_frame)
            
            # Convert to CTkImage for better compatibility
            ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(640, 480))
            
            # Update label
            self.camera_label.configure(image=ctk_image, text="")
            self.camera_label.image = ctk_image  # Keep a reference
        except Exception as e:
            print(f"Display error: {e}")
            # Fallback to text display
            self.camera_label.configure(text="Camera Active", image=None)
            
    def process_registration_frame(self, frame):
        """Process frame during registration"""
        # Detect faces for registration
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        # Draw rectangles around faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Add registration info to frame
        cv2.putText(frame, f"Registration: {self.current_roll_no}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Captured: {self.capture_count}/{self.max_captures}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(frame, f"Name: {self.current_name}", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        
        if len(faces) > 0 and self.capture_count < self.max_captures:
            # Show face detected
            cv2.putText(frame, "FACE DETECTED - CAPTURING", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Auto-capture every 3 frames when face is detected
            if not hasattr(self, 'frame_counter'):
                self.frame_counter = 0
            
            self.frame_counter += 1
            
            if self.frame_counter % 3 == 0:  # Capture every 3 frames
                self.capture_face_image(frame, faces[0])
        else:
            if self.capture_count < self.max_captures:
                cv2.putText(frame, "POSITION FACE IN FRAME", (10, 120),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
        return frame
        
    def process_attendance_frame(self, frame):
        """Process frame during attendance verification"""
        # Add attendance info to frame
        cv2.putText(frame, f"Verifying: {self.current_roll_no}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Name: {self.current_name}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Perform face recognition
        recognized, confidence, message = self.face_recognition_system.recognize_face(frame, self.current_roll_no)
        
        if recognized:
            cv2.putText(frame, f"VERIFIED! Confidence: {confidence:.2%}", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, "Hold still for attendance...", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Save detected student to dashboard
            self.save_detected_student(self.current_roll_no, self.current_name, confidence)
            
            self.verification_frames += 1
            
            # Show countdown
            remaining = max(0, self.required_verification_frames - self.verification_frames)
            cv2.putText(frame, f"Countdown: {remaining//10 + 1}", (10, 150),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            if self.verification_frames >= self.required_verification_frames:
                self.complete_attendance(confidence)
        else:
            cv2.putText(frame, f"Status: {message}", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.putText(frame, "Position face clearly in frame", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            self.verification_frames = 0  # Reset counter
                
        return frame
    
    def save_detected_student(self, roll_no, name, confidence):
        """Save detected student information to dashboard database (only once per roll number per day)"""
        from datetime import datetime
        
        # Check if already detected today
        if self.is_student_already_detected_today(roll_no):
            print(f"Student {roll_no} already detected today - skipping duplicate")
            return
        
        # Save to in-memory list for immediate display
        detection_info = {
            "roll_no": roll_no,
            "name": name,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "status": "detected"
        }
        
        # Add to detected students list (keep last 10)
        self.detected_students.append(detection_info)
        if len(self.detected_students) > 10:
            self.detected_students.pop(0)
        
        # Save to database
        try:
            import sqlite3
            conn = sqlite3.connect("attendance_db/dashboard_data.db")
            cursor = conn.cursor()
            
            # Ensure table exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detected_students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    roll_no TEXT NOT NULL,
                    name TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    detection_time TEXT NOT NULL,
                    date TEXT NOT NULL,
                    status TEXT DEFAULT 'detected',
                    UNIQUE(roll_no, date)
                )
            ''')
            
            # Insert detection data (only if not exists for today)
            cursor.execute('''
                INSERT OR IGNORE INTO detected_students 
                (roll_no, name, confidence, detection_time, date, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                roll_no, 
                name, 
                float(confidence), 
                datetime.now().isoformat(),
                datetime.now().strftime('%Y-%m-%d'),
                "detected"
            ))
            
            if cursor.rowcount > 0:
                conn.commit()
                print(f"✅ Detected student saved to database: {roll_no} - {name} ({confidence:.1%})")
            else:
                print(f"ℹ️ Student {roll_no} already detected today - database not updated")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error saving detected student to database: {e}")
        
        # Log detection event (only once)
        dashboard_manager.log_system_event(
            "face_detection",
            roll_no,
            f"Student {name} detected with {confidence:.1%} confidence",
            confidence,
            "success"
        )
        
        print(f"Detected student saved: {roll_no} - {name} ({confidence:.1%})")
    
    def is_student_already_detected_today(self, roll_no):
        """Check if student is already detected today"""
        try:
            import sqlite3
            conn = sqlite3.connect("attendance_db/dashboard_data.db")
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute(
                'SELECT id FROM detected_students WHERE roll_no = ? AND date = ?',
                (roll_no, today)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
            
        except Exception as e:
            print(f"Error checking detection status: {e}")
            return False
        
    def capture_face_image(self, frame, face_coords):
        """Capture and save face image"""
        try:
            x, y, w, h = face_coords
            
            # Extract face region with padding
            padding = 20
            y_start = max(0, y-padding)
            y_end = min(frame.shape[0], y+h+padding)
            x_start = max(0, x-padding)
            x_end = min(frame.shape[1], x+w+padding)
            
            face_img = frame[y_start:y_end, x_start:x_end]
            
            if face_img.size > 0:
                # Create student directory
                student_dir = os.path.join(DATASET_PATH, self.current_roll_no)
                os.makedirs(student_dir, exist_ok=True)
                
                # Save image
                filename = f"{self.current_roll_no}_{self.capture_count+1:03d}.jpg"
                filepath = os.path.join(student_dir, filename)
                
                # Save with high quality
                success = cv2.imwrite(filepath, face_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                
                if success:
                    self.capture_count += 1
                    print(f"Captured image {self.capture_count}/{self.max_captures}: {filename}")
                    
                    # Update progress
                    progress = self.capture_count / self.max_captures
                    self.progress_bar.set(progress)
                    
                    # Update status
                    self.update_status(f"Captured {self.capture_count}/{self.max_captures} images", "orange")
                    
                    if self.capture_count >= self.max_captures:
                        self.complete_registration()
                else:
                    print(f"Failed to save image: {filepath}")
            else:
                print("Invalid face region extracted")
                
        except Exception as e:
            print(f"Error capturing face image: {e}")
            
    def start_registration(self):
        """Start student registration process"""
        roll_no = self.reg_roll_entry.get().strip()
        name = self.reg_name_entry.get().strip()
        
        if not roll_no or not name:
            messagebox.showerror("Input Error", "Please enter roll number and name")
            return
        
        # Check if student already exists
        existing_student = self.db_manager.get_student_info(roll_no)
        if existing_student:
            response = messagebox.askyesno(
                "Student Exists", 
                f"Student {roll_no} already exists. Re-register?"
            )
            if not response:
                return
        
        self.current_roll_no = roll_no
        self.current_name = name
        self.current_mode = "registration"
        self.capture_count = 0
        self.frame_counter = 0
        
        # Clear progress
        self.progress_bar.set(0)
        
        self.update_status(f"Starting registration for {roll_no}...", "orange")
        print(f"Starting registration: {roll_no} - {name}")
        
        self.start_camera_thread()
        
    def complete_registration(self):
        """Complete registration process"""
        try:
            print(f"Completing registration for {self.current_roll_no}...")
            
            # Stop camera first
            self.current_mode = "idle"
            
            # Register in database
            dept = self.reg_dept_entry.get().strip() or "Unknown"
            print(f"Registering in database: {self.current_roll_no}, {self.current_name}, {dept}")
            
            success, message = self.db_manager.register_student(
                self.current_roll_no, self.current_name, dept
            )
            
            print(f"Database registration result: {success}, {message}")
            
            if success:
                # Generate face encodings
                encoding_success = self.face_recognition_system.update_encodings(
                    self.current_roll_no, self.current_name
                )
                
                if encoding_success:
                    self.db_manager.update_face_encoded_status(self.current_roll_no, 1)
                    print("Face encodings generated successfully")
                
                # Log system event
                dashboard_manager.log_system_event(
                    "student_registration",
                    self.current_roll_no,
                    f"Student {self.current_name} registered successfully",
                    status="success"
                )
                
                self.update_status(f"✅ Registration completed for {self.current_roll_no}", "green")
                
                # Show success message
                success_msg = f"""Registration Successful!
                
Student: {self.current_name}
Roll No: {self.current_roll_no}
Department: {dept}
Images Captured: {self.capture_count}
Face Encodings: {'✅ Generated' if encoding_success else '❌ Failed'}
                
Student can now use face attendance system."""
                
                messagebox.showinfo("Registration Complete", success_msg)
                
                # Clear form
                self.reg_roll_entry.delete(0, 'end')
                self.reg_name_entry.delete(0, 'end')
                self.reg_dept_entry.delete(0, 'end')
                
            else:
                # Log failure
                dashboard_manager.log_system_event(
                    "student_registration",
                    self.current_roll_no,
                    f"Registration failed: {message}",
                    status="failed"
                )
                
                self.update_status(f"❌ Registration failed: {message}", "red")
                messagebox.showerror("Registration Error", message)
                
            self.progress_bar.set(0)
            
        except Exception as e:
            error_msg = f"Error completing registration: {e}"
            print(error_msg)
            
            # Log error
            dashboard_manager.log_system_event(
                "system_error",
                self.current_roll_no,
                error_msg,
                status="error"
            )
            
            self.update_status(f"❌ Registration error: {str(e)}", "red")
            messagebox.showerror("Error", f"Registration failed: {str(e)}")
            
    def start_attendance(self):
        """Start attendance verification process"""
        roll_no = self.att_roll_entry.get().strip()
        
        if not roll_no:
            messagebox.showerror("Input Error", "Please enter roll number")
            return
            
        # Check if student exists and is registered
        student_info = self.db_manager.get_student_info(roll_no)
        if not student_info:
            messagebox.showerror("Error", "Student not registered. Please register first.")
            return
            
        if student_info[3] == 0:  # face_encoded status
            messagebox.showwarning("Warning", "Student face not encoded. Please re-register.")
            return
        
        self.current_roll_no = roll_no
        self.current_name = student_info[1]  # Get name from database
        self.current_mode = "attendance"
        self.verification_frames = 0
        
        self.update_status(f"Verifying face for {roll_no}...", "orange")
        self.start_camera_thread()
        
    def complete_attendance(self, confidence):
        """Complete attendance marking"""
        try:
            success, message = self.db_manager.mark_attendance(
                self.current_roll_no, self.current_name, "Present", confidence, "face_recognition"
            )
            
            if success:
                # Log successful attendance
                dashboard_manager.log_system_event(
                    "face_attendance",
                    self.current_roll_no,
                    f"Attendance marked for {self.current_name}",
                    confidence,
                    "success"
                )
                
                self.update_status(f"✅ Attendance marked for {self.current_roll_no}", "green")
                
                success_msg = f"""Attendance Marked Successfully!
                
Student: {self.current_name}
Roll No: {self.current_roll_no}
Time: {datetime.now().strftime('%H:%M:%S')}
Date: {datetime.now().strftime('%Y-%m-%d')}
Confidence: {confidence:.1%}
Method: Face Recognition"""
                
                messagebox.showinfo("Attendance Success", success_msg)
                
                # Clear form
                self.att_roll_entry.delete(0, 'end')
                
            else:
                # Log failed attendance
                dashboard_manager.log_system_event(
                    "face_attendance",
                    self.current_roll_no,
                    f"Attendance failed: {message}",
                    confidence,
                    "failed"
                )
                
                self.update_status(f"❌ {message}", "red")
                messagebox.showerror("Attendance Error", message)
                
            self.current_mode = "idle"
            
        except Exception as e:
            error_msg = f"Error marking attendance: {e}"
            print(error_msg)
            
            # Log error
            dashboard_manager.log_system_event(
                "system_error",
                self.current_roll_no,
                error_msg,
                status="error"
            )
            
            self.update_status(f"❌ Attendance error: {str(e)}", "red")
            messagebox.showerror("Error", f"Attendance failed: {str(e)}")
            
    def stop_current_operation(self):
        """Stop current camera operation"""
        self.current_mode = "idle"
        self.camera_manager.stop_camera()
        self.update_status("Operation stopped", "blue")
        
    def show_records(self):
        """Show attendance records in a new window"""
        records_window = ctk.CTkToplevel(self.root)
        records_window.title("Attendance Records")
        records_window.geometry("1000x700")
        
        # Create scrollable frame
        scrollable_frame = ctk.CTkScrollableFrame(records_window)
        scrollable_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Headers
        headers = ["Roll No", "Name", "Date", "Time", "Status", "Confidence", "Method"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(scrollable_frame, text=header, font=ctk.CTkFont(weight="bold"))
            label.grid(row=0, column=i, padx=10, pady=5, sticky="w")
            
        # Get and display records
        records = self.db_manager.get_attendance_records()
        
        for i, record in enumerate(records, 1):
            for j, value in enumerate(record):
                if j == 5:  # Confidence column
                    value = f"{value:.1%}" if value else "N/A"
                label = ctk.CTkLabel(scrollable_frame, text=str(value))
                label.grid(row=i, column=j, padx=10, pady=2, sticky="w")
                
        # Stats
        total_records = len(records)
        present_count = len([r for r in records if r[4] == "Present"])
        face_recognition_count = len([r for r in records if r[6] == "face_recognition"])
        
        stats_label = ctk.CTkLabel(
            records_window,
            text=f"Total Records: {total_records} | Present: {present_count} | Face Recognition: {face_recognition_count}",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        stats_label.pack(pady=10)
    
    def open_dashboard(self):
        """Open dashboard with password protection"""
        # Check if already authenticated
        if self.dashboard_session and dashboard_manager.is_session_valid(self.dashboard_session):
            self.show_dashboard()
            return
        
        # Request password
        password = simpledialog.askstring(
            "Dashboard Access", 
            "Enter password to access dashboard:",
            show='*'
        )
        
        if password:
            success, result = dashboard_manager.verify_access(password)
            
            if success:
                self.dashboard_session = result
                self.dashboard_mode_btn.configure(
                    text="📊 Dashboard (Unlocked)",
                    fg_color=COLORS["success"],
                    hover_color=COLORS["info"]
                )
                self.show_dashboard()
            else:
                messagebox.showerror("Access Denied", result)
    
    def show_dashboard(self):
        """Show dashboard window"""
        if not self.dashboard_session or not dashboard_manager.is_session_valid(self.dashboard_session):
            messagebox.showerror("Session Error", "Session expired. Please login again.")
            self.dashboard_session = None
            self.dashboard_mode_btn.configure(
                text="📊 Dashboard (Locked)",
                fg_color=COLORS["danger"],
                hover_color=COLORS["warning"]
            )
            return
        
        # Create dashboard window with custom colors
        dashboard_window = ctk.CTkToplevel(self.root)
        dashboard_window.title("📊 SRINIVAS Dashboard - Student Attendance System")
        dashboard_window.geometry("1200x800")
        dashboard_window.configure(fg_color=COLORS["background"])
        
        # Main dashboard frame
        main_frame = ctk.CTkFrame(dashboard_window, fg_color=COLORS["surface"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title with custom colors
        title_label = ctk.CTkLabel(
            main_frame,
            text="📊 SRINIVAS DASHBOARD",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["accent"]
        )
        title_label.pack(pady=20)
        
        # Get dashboard data
        dashboard_data, message = dashboard_manager.get_dashboard_data(self.dashboard_session)
        
        if not dashboard_data:
            error_label = ctk.CTkLabel(
                main_frame, 
                text=f"Error: {message}", 
                text_color=COLORS["danger"]
            )
            error_label.pack(pady=20)
            return
        
        # Create tabview for different sections with custom colors
        tabview = ctk.CTkTabview(main_frame, fg_color=COLORS["primary"])
        tabview.pack(fill="both", expand=True, pady=20)
        
        # Overview Tab
        overview_tab = tabview.add("📈 Overview")
        self.create_overview_tab(overview_tab, dashboard_data)
        
        # Detected Students Tab (NEW)
        detected_tab = tabview.add("👥 Detected Students")
        self.create_detected_students_tab(detected_tab)
        
        # Today's Attendance Tab
        attendance_tab = tabview.add("✅ Today's Attendance")
        self.create_attendance_tab(attendance_tab, dashboard_data)
        
        # System Logs Tab
        logs_tab = tabview.add("📋 System Logs")
        self.create_logs_tab(logs_tab, dashboard_data)
        
        # Reports Tab
        reports_tab = tabview.add("📊 Reports")
        self.create_reports_tab(reports_tab)
        
        # Data Export Tab
        export_tab = tabview.add("💾 Export Data")
        self.create_export_tab(export_tab)
        
        # Back button and session info frame
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=10)
        
        # Back button to return to main interface
        back_btn = ctk.CTkButton(
            bottom_frame,
            text="🏠 Back to Home",
            command=lambda: self.close_dashboard_and_return_home(dashboard_window),
            width=150,
            height=35,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLORS["secondary"],
            hover_color=COLORS["primary"]
        )
        back_btn.pack(side="left", padx=10)
        
        # Session info with custom color
        session_label = ctk.CTkLabel(
            bottom_frame,
            text=f"Session Active | Last Updated: {dashboard_data['last_updated'][:19]}",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["info"]
        )
        session_label.pack(side="right", padx=10)
    
    def create_overview_tab(self, parent, dashboard_data):
        """Create overview tab content with custom colors"""
        stats = dashboard_data["current_stats"]
        
        # Stats cards frame with custom background
        stats_frame = ctk.CTkFrame(parent, fg_color=COLORS["dark"])
        stats_frame.pack(fill="x", padx=20, pady=20)
        
        # Create stat cards with custom colors
        stat_cards = [
            ("👥 Total Students", stats["total_students"], COLORS["info"]),
            ("📊 Total Attendance", stats["total_attendance"], COLORS["success"]),
            ("✅ Present Today", stats["present_today"], COLORS["warning"]),
            ("📈 Attendance Rate", f"{stats['attendance_rate']:.1f}%", COLORS["accent"]),
            ("🆕 New Registrations", stats["new_registrations"], COLORS["secondary"]),
            ("🔍 Face Verifications", stats["face_verifications"], COLORS["primary"])
        ]
        
        for i, (title, value, color) in enumerate(stat_cards):
            card = ctk.CTkFrame(stats_frame, fg_color=COLORS["surface"])
            card.grid(row=i//3, column=i%3, padx=10, pady=10, sticky="ew")
            
            title_label = ctk.CTkLabel(
                card, 
                text=title, 
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS["light"]
            )
            title_label.pack(pady=5)
            
            value_label = ctk.CTkLabel(
                card, 
                text=str(value), 
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color=color
            )
            value_label.pack(pady=5)
        
        # Configure grid weights
        for i in range(3):
            stats_frame.grid_columnconfigure(i, weight=1)
        
        # Weekly trend with custom colors
        trend_frame = ctk.CTkFrame(parent, fg_color=COLORS["primary"])
        trend_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        trend_label = ctk.CTkLabel(
            trend_frame,
            text="📈 Weekly Attendance Trend",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["light"]
        )
        trend_label.pack(pady=10)
        
        # Weekly data display
        weekly_data = dashboard_data["weekly_data"]
        if weekly_data:
            for date, present, rate in weekly_data:
                day_frame = ctk.CTkFrame(trend_frame, fg_color=COLORS["secondary"])
                day_frame.pack(fill="x", padx=10, pady=2)
                
                day_info = f"{date}: {present} students present ({rate:.1f}%)"
                day_label = ctk.CTkLabel(
                    day_frame, 
                    text=day_info,
                    text_color=COLORS["light"]
                )
                day_label.pack(pady=5)
    
    def create_detected_students_tab(self, parent):
        """Create detected students tab showing real-time detections from database"""
        detected_frame = ctk.CTkScrollableFrame(parent, fg_color=COLORS["dark"])
        detected_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            detected_frame,
            text="👥 Recently Detected Students",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["accent"]
        )
        title_label.pack(pady=10)
        
        # Info label
        info_label = ctk.CTkLabel(
            detected_frame,
            text="Students detected during face verification (Last 10 detections from database)",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["info"]
        )
        info_label.pack(pady=5)
        
        # Headers with custom colors
        header_frame = ctk.CTkFrame(detected_frame, fg_color=COLORS["primary"])
        header_frame.pack(fill="x", pady=10)
        
        headers = ["Roll Number", "Student Name", "Confidence", "Detection Time", "Status"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                header_frame, 
                text=header, 
                font=ctk.CTkFont(weight="bold"),
                text_color=COLORS["light"]
            )
            label.grid(row=0, column=i, padx=10, pady=5, sticky="w")
        
        # Get detected students data from database
        detected_students_db = self.get_detected_students_from_db()
        
        if detected_students_db:
            for i, detection in enumerate(detected_students_db):
                record_frame = ctk.CTkFrame(detected_frame, fg_color=COLORS["surface"])
                record_frame.pack(fill="x", pady=2)
                
                # Format data
                roll_no = detection["roll_no"]
                name = detection["name"]
                confidence = f"{detection['confidence']:.1%}"
                timestamp = detection["detection_time"][:19].replace('T', ' ')
                status = "✅ Detected"
                
                # Color code based on confidence
                conf_value = detection["confidence"]
                conf_color = COLORS["success"] if conf_value > 0.8 else COLORS["warning"] if conf_value > 0.5 else COLORS["danger"]
                
                values = [roll_no, name, confidence, timestamp, status]
                colors = [COLORS["accent"], COLORS["light"], conf_color, COLORS["info"], COLORS["success"]]
                
                for j, (value, color) in enumerate(zip(values, colors)):
                    label = ctk.CTkLabel(
                        record_frame, 
                        text=str(value),
                        text_color=color
                    )
                    label.grid(row=0, column=j, padx=10, pady=5, sticky="w")
        else:
            no_data_label = ctk.CTkLabel(
                detected_frame, 
                text="No students detected yet. Start face verification to see detections here.",
                text_color=COLORS["warning"]
            )
            no_data_label.pack(pady=20)
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            detected_frame,
            text="🔄 Refresh Detections",
            command=lambda: self.refresh_detected_students_tab(detected_frame),
            fg_color=COLORS["accent"],
            hover_color=COLORS["primary"]
        )
        refresh_btn.pack(pady=10)
    
    def get_detected_students_from_db(self):
        """Get detected students data from database"""
        try:
            import sqlite3
            conn = sqlite3.connect("attendance_db/dashboard_data.db")
            cursor = conn.cursor()
            
            # Get last 10 detections
            cursor.execute('''
                SELECT roll_no, name, confidence, detection_time, date, status
                FROM detected_students 
                ORDER BY detection_time DESC 
                LIMIT 10
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to list of dictionaries
            detected_students = []
            for row in rows:
                detected_students.append({
                    "roll_no": row[0],
                    "name": row[1],
                    "confidence": float(row[2]),
                    "detection_time": row[3],
                    "date": row[4],
                    "status": row[5]
                })
            
            return detected_students
            
        except Exception as e:
            print(f"Error getting detected students from database: {e}")
            return []
    
    def refresh_detected_students_tab(self, parent):
        """Refresh the detected students tab"""
        # Clear and recreate the tab content
        for widget in parent.winfo_children():
            widget.destroy()
        self.create_detected_students_tab(parent.master)
    
    def create_attendance_tab(self, parent, dashboard_data):
        """Create today's attendance tab"""
        attendance_frame = ctk.CTkScrollableFrame(parent)
        attendance_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            attendance_frame,
            text="✅ Today's Attendance Records",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=10)
        
        # Headers
        headers = ["Roll No", "Name", "Time", "Confidence", "Method"]
        header_frame = ctk.CTkFrame(attendance_frame)
        header_frame.pack(fill="x", pady=5)
        
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(header_frame, text=header, font=ctk.CTkFont(weight="bold"))
            label.grid(row=0, column=i, padx=10, pady=5, sticky="w")
        
        # Attendance records
        todays_attendance = dashboard_data["todays_attendance"]
        
        if todays_attendance:
            for i, (roll_no, name, time, confidence, method) in enumerate(todays_attendance):
                record_frame = ctk.CTkFrame(attendance_frame)
                record_frame.pack(fill="x", pady=2)
                
                # Format confidence
                conf_text = f"{float(confidence):.1%}" if confidence and confidence != b'' else "N/A"
                
                values = [roll_no, name, time, conf_text, method]
                for j, value in enumerate(values):
                    label = ctk.CTkLabel(record_frame, text=str(value))
                    label.grid(row=0, column=j, padx=10, pady=5, sticky="w")
        else:
            no_data_label = ctk.CTkLabel(attendance_frame, text="No attendance records for today")
            no_data_label.pack(pady=20)
    
    def create_logs_tab(self, parent, dashboard_data):
        """Create system logs tab"""
        logs_frame = ctk.CTkScrollableFrame(parent)
        logs_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            logs_frame,
            text="📋 Recent System Logs",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=10)
        
        # Headers
        headers = ["Timestamp", "Event Type", "Roll No", "Description", "Status"]
        header_frame = ctk.CTkFrame(logs_frame)
        header_frame.pack(fill="x", pady=5)
        
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(header_frame, text=header, font=ctk.CTkFont(weight="bold"))
            label.grid(row=0, column=i, padx=10, pady=5, sticky="w")
        
        # Log records
        recent_logs = dashboard_data["recent_logs"]
        
        if recent_logs:
            for timestamp, event_type, roll_no, description, status in recent_logs:
                log_frame = ctk.CTkFrame(logs_frame)
                log_frame.pack(fill="x", pady=2)
                
                # Format timestamp
                time_str = timestamp[:19] if timestamp else "N/A"
                roll_str = roll_no if roll_no else "System"
                
                # Color code status
                status_color = "green" if status == "success" else "red" if status == "failed" else "orange"
                
                values = [time_str, event_type, roll_str, description]
                for j, value in enumerate(values):
                    label = ctk.CTkLabel(log_frame, text=str(value))
                    label.grid(row=0, column=j, padx=10, pady=5, sticky="w")
                
                # Status with color
                status_label = ctk.CTkLabel(log_frame, text=status, text_color=status_color)
                status_label.grid(row=0, column=4, padx=10, pady=5, sticky="w")
        else:
            no_logs_label = ctk.CTkLabel(logs_frame, text="No system logs available")
            no_logs_label.pack(pady=20)
    
    def create_reports_tab(self, parent):
        """Create reports tab"""
        reports_frame = ctk.CTkFrame(parent)
        reports_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            reports_frame,
            text="📊 Generate Reports",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Report buttons
        weekly_btn = ctk.CTkButton(
            reports_frame,
            text="📅 Weekly Report",
            command=lambda: self.generate_report("weekly"),
            width=200,
            height=40
        )
        weekly_btn.pack(pady=10)
        
        monthly_btn = ctk.CTkButton(
            reports_frame,
            text="📆 Monthly Report",
            command=lambda: self.generate_report("monthly"),
            width=200,
            height=40
        )
        monthly_btn.pack(pady=10)
    
    def create_export_tab(self, parent):
        """Create data export tab"""
        export_frame = ctk.CTkFrame(parent)
        export_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            export_frame,
            text="💾 Export Data",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=20)
        
        info_label = ctk.CTkLabel(
            export_frame,
            text="Export all system data to JSON format for backup or analysis",
            font=ctk.CTkFont(size=12)
        )
        info_label.pack(pady=10)
        
        export_btn = ctk.CTkButton(
            export_frame,
            text="📤 Export All Data",
            command=self.export_dashboard_data,
            width=200,
            height=40
        )
        export_btn.pack(pady=20)
    
    def generate_report(self, report_type):
        """Generate and display report"""
        if not self.dashboard_session or not dashboard_manager.is_session_valid(self.dashboard_session):
            messagebox.showerror("Session Error", "Session expired. Please login again.")
            return
        
        report_data, message = dashboard_manager.get_detailed_reports(self.dashboard_session, report_type)
        
        if report_data:
            # Create report window
            report_window = ctk.CTkToplevel(self.root)
            report_window.title(f"📊 {report_type.title()} Report")
            report_window.geometry("800x600")
            
            # Report content
            content_frame = ctk.CTkScrollableFrame(report_window)
            content_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Title
            title_label = ctk.CTkLabel(
                content_frame,
                text=f"📊 {report_type.title()} Report",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title_label.pack(pady=10)
            
            # Period
            period_label = ctk.CTkLabel(
                content_frame,
                text=f"Period: {report_data['period']}",
                font=ctk.CTkFont(size=12)
            )
            period_label.pack(pady=5)
            
            # Report data display
            if report_type == "weekly":
                # Daily summary
                daily_label = ctk.CTkLabel(
                    content_frame,
                    text="📅 Daily Summary:",
                    font=ctk.CTkFont(size=14, weight="bold")
                )
                daily_label.pack(pady=10)
                
                for date, present, avg_conf in report_data["daily_summary"]:
                    day_text = f"{date}: {present} students present (Avg confidence: {avg_conf:.1%})"
                    day_label = ctk.CTkLabel(content_frame, text=day_text)
                    day_label.pack(pady=2)
                
                # Student summary
                student_label = ctk.CTkLabel(
                    content_frame,
                    text="👥 Student Summary:",
                    font=ctk.CTkFont(size=14, weight="bold")
                )
                student_label.pack(pady=10)
                
                for roll_no, name, dept, days_present, avg_conf in report_data["student_summary"]:
                    student_text = f"{roll_no} - {name} ({dept}): {days_present} days present"
                    student_label = ctk.CTkLabel(content_frame, text=student_text)
                    student_label.pack(pady=2)
            
        else:
            messagebox.showerror("Report Error", message)
    
    def close_dashboard_and_return_home(self, dashboard_window):
        """Close dashboard window and return to main interface"""
        try:
            # Close the dashboard window
            dashboard_window.destroy()
            
            # Update the dashboard button to show it's locked again (optional - keeps session active)
            # Uncomment the lines below if you want to lock the dashboard again when returning home
            # self.dashboard_session = None
            # self.dashboard_mode_btn.configure(
            #     text="📊 Dashboard (Locked)",
            #     fg_color=COLORS["danger"],
            #     hover_color=COLORS["warning"]
            # )
            
            # Bring main window to front
            self.root.lift()
            self.root.focus_force()
            
            # Update status to show user is back at home
            self.update_status("Returned to main interface from dashboard", COLORS["accent"])
            
            print("✅ Successfully returned to main interface from dashboard")
            
        except Exception as e:
            print(f"❌ Error closing dashboard: {e}")
            # Fallback - just try to bring main window to front
            try:
                self.root.lift()
                self.root.focus_force()
            except:
                pass
    
    def export_dashboard_data(self):
        """Export dashboard data"""
        if not self.dashboard_session or not dashboard_manager.is_session_valid(self.dashboard_session):
            messagebox.showerror("Session Error", "Session expired. Please login again.")
            return
        
        export_path, message = dashboard_manager.export_data(self.dashboard_session)
        
        if export_path:
            messagebox.showinfo("Export Success", f"Data exported successfully to:\n{export_path}")
        else:
            messagebox.showerror("Export Error", message)
        
    def on_closing(self):
        """Handle application closing"""
        self.running = False
        self.camera_manager.stop_camera()
        if self.camera_thread and self.camera_thread.is_alive():
            self.camera_thread.join(timeout=1)
        self.root.destroy()
        
    def run(self):
        """Run the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def main():
    """Main function"""
    # Create required directories
    os.makedirs(DATASET_PATH, exist_ok=True)
    os.makedirs(DATABASE_FOLDER, exist_ok=True)
    os.makedirs(ENCODINGS_FOLDER, exist_ok=True)
    
    # Run application
    app = StudentFaceAttendanceApp()
    app.run()

if __name__ == "__main__":
    main()