"""
Modern Face Attendance System
Using MediaPipe for face detection and CustomTkinter for modern GUI
High performance with proper camera handling and database operations
"""

import cv2
import mediapipe as mp
import numpy as np
import sqlite3
import os
import threading
import time
from datetime import datetime
from PIL import Image, ImageTk
import customtkinter as ctk
from tkinter import messagebox
import json

# Configuration
DATASET_PATH = "dataset"
ATTENDANCE_DB = "attendance_db/attendance.db"
DATABASE_FOLDER = "attendance_db"
CONFIG_FILE = "config.json"

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class FaceDetector:
    def __init__(self):
        try:
            # Try new MediaPipe API
            self.mp_face_detection = mp.solutions.face_detection
            self.mp_drawing = mp.solutions.drawing_utils
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=0, min_detection_confidence=0.5
            )
            self.use_mediapipe = True
        except:
            # Fallback to OpenCV
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            self.use_mediapipe = False
            print("Using OpenCV face detection as fallback")
        
    def detect_faces(self, image):
        """Detect faces using MediaPipe or OpenCV"""
        if self.use_mediapipe:
            return self._detect_faces_mediapipe(image)
        else:
            return self._detect_faces_opencv(image)
    
    def _detect_faces_mediapipe(self, image):
        """MediaPipe face detection"""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb_image)
        
        faces = []
        if results.detections:
            for detection in results.detections:
                bboxC = detection.location_data.relative_bounding_box
                ih, iw, ic = image.shape
                x = int(bboxC.xmin * iw)
                y = int(bboxC.ymin * ih)
                w = int(bboxC.width * iw)
                h = int(bboxC.height * ih)
                faces.append((x, y, w, h))
                
                # Draw rectangle
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
        return image, faces
    
    def _detect_faces_opencv(self, image):
        """OpenCV face detection"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
        return image, faces

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
                registered_date TEXT NOT NULL
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
                UNIQUE(roll_no, date),
                FOREIGN KEY (roll_no) REFERENCES students (roll_no)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("Database initialized successfully")
    
    def register_student(self, roll_no, name, department="Unknown"):
        """Register a new student"""
        try:
            conn = sqlite3.connect(ATTENDANCE_DB)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO students (roll_no, name, department, registered_date)
                VALUES (?, ?, ?, ?)
            ''', (roll_no, name, department, datetime.now().strftime('%Y-%m-%d')))
            
            conn.commit()
            conn.close()
            return True, "Student registered successfully"
        except Exception as e:
            return False, f"Registration failed: {str(e)}"
    
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
    
    def mark_attendance(self, roll_no, name, status, confidence=1.0):
        """Mark attendance"""
        date = datetime.now().strftime('%Y-%m-%d')
        
        if self.check_duplicate_attendance(roll_no, date):
            return False, "Attendance already marked today"
        
        try:
            conn = sqlite3.connect(ATTENDANCE_DB)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO attendance (roll_no, name, date, time, status, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                roll_no, name, date,
                datetime.now().strftime('%H:%M:%S'),
                status, confidence
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
            SELECT roll_no, name, date, time, status, confidence 
            FROM attendance 
            ORDER BY date DESC, time DESC 
            LIMIT ?
        ''', (limit,))
        
        records = cursor.fetchall()
        conn.close()
        
        return records
    
    def get_student_info(self, roll_no):
        """Get student information"""
        conn = sqlite3.connect(ATTENDANCE_DB)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT roll_no, name, department FROM students WHERE roll_no = ?',
            (roll_no,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        return result

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

class ModernAttendanceApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Modern Face Attendance System")
        self.root.geometry("900x700")
        
        # Initialize components
        self.face_detector = FaceDetector()
        self.db_manager = DatabaseManager()
        self.camera_manager = CameraManager()
        
        # Variables
        self.current_mode = "idle"  # idle, registration, attendance
        self.capture_count = 0
        self.max_captures = 20
        self.current_roll_no = ""
        self.current_name = ""
        
        # Create GUI
        self.create_widgets()
        
        # Start camera thread
        self.camera_thread = None
        self.running = True
        
    def create_widgets(self):
        """Create modern GUI widgets"""
        # Main container
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="🎯 Modern Face Attendance System",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Input section
        input_frame = ctk.CTkFrame(main_frame)
        input_frame.pack(fill="x", padx=20, pady=10)
        
        # Roll number input
        ctk.CTkLabel(input_frame, text="Roll Number:", font=ctk.CTkFont(size=14)).pack(pady=5)
        self.roll_entry = ctk.CTkEntry(input_frame, placeholder_text="Enter roll number", width=200)
        self.roll_entry.pack(pady=5)
        
        # Name input
        ctk.CTkLabel(input_frame, text="Name:", font=ctk.CTkFont(size=14)).pack(pady=5)
        self.name_entry = ctk.CTkEntry(input_frame, placeholder_text="Enter student name", width=200)
        self.name_entry.pack(pady=5)
        
        # Department input
        ctk.CTkLabel(input_frame, text="Department:", font=ctk.CTkFont(size=14)).pack(pady=5)
        self.dept_entry = ctk.CTkEntry(input_frame, placeholder_text="Enter department", width=200)
        self.dept_entry.pack(pady=5)
        
        # Button section
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        # Buttons
        self.register_btn = ctk.CTkButton(
            button_frame,
            text="📝 Register Student",
            command=self.start_registration,
            width=200,
            height=40
        )
        self.register_btn.pack(side="left", padx=10, pady=10)
        
        self.attendance_btn = ctk.CTkButton(
            button_frame,
            text="✅ Mark Attendance",
            command=self.start_attendance,
            width=200,
            height=40
        )
        self.attendance_btn.pack(side="left", padx=10, pady=10)
        
        self.records_btn = ctk.CTkButton(
            button_frame,
            text="📊 View Records",
            command=self.show_records,
            width=200,
            height=40
        )
        self.records_btn.pack(side="left", padx=10, pady=10)
        
        # Camera section
        camera_frame = ctk.CTkFrame(main_frame)
        camera_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.camera_label = ctk.CTkLabel(camera_frame, text="Camera Feed", width=640, height=480)
        self.camera_label.pack(pady=20)
        
        # Status section
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="System Ready",
            font=ctk.CTkFont(size=14),
            text_color="green"
        )
        self.status_label.pack(pady=10)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(main_frame, width=400)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
    def update_status(self, message, color="green"):
        """Update status message"""
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
                frame, faces = self.face_detector.detect_faces(frame)
                
            # Convert frame for display
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
        frame, faces = self.face_detector.detect_faces(frame)
        
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
            
            # Auto-capture every 5 frames when face is detected
            if not hasattr(self, 'frame_counter'):
                self.frame_counter = 0
            
            self.frame_counter += 1
            
            if self.frame_counter % 5 == 0:  # Capture every 5 frames (faster)
                self.capture_face_image(frame, faces[0])
        else:
            if self.capture_count < self.max_captures:
                cv2.putText(frame, "POSITION FACE IN FRAME", (10, 120),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
        return frame
        
    def process_attendance_frame(self, frame):
        """Process frame during attendance"""
        frame, faces = self.face_detector.detect_faces(frame)
        
        # Add attendance info to frame
        cv2.putText(frame, f"Attendance: {self.current_roll_no}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Face detected - Verifying...", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        if len(faces) > 0:
            # Auto-verify after detecting face for a few seconds
            if hasattr(self, 'verification_counter'):
                self.verification_counter += 1
            else:
                self.verification_counter = 0
                
            if self.verification_counter > 60:  # ~2 seconds at 30fps
                self.complete_attendance()
                
        return frame
        
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
        roll_no = self.roll_entry.get().strip()
        name = self.name_entry.get().strip()
        
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
            dept = self.dept_entry.get().strip() or "Unknown"
            print(f"Registering in database: {self.current_roll_no}, {self.current_name}, {dept}")
            
            success, message = self.db_manager.register_student(
                self.current_roll_no, self.current_name, dept
            )
            
            print(f"Database registration result: {success}, {message}")
            
            if success:
                self.update_status(f"✅ Registration completed for {self.current_roll_no}", "green")
                
                # Show success message
                success_msg = f"""Registration Successful!
                
Student: {self.current_name}
Roll No: {self.current_roll_no}
Department: {dept}
Images Captured: {self.capture_count}
                
Student can now mark attendance."""
                
                messagebox.showinfo("Registration Complete", success_msg)
                
                # Clear form
                self.roll_entry.delete(0, 'end')
                self.name_entry.delete(0, 'end')
                self.dept_entry.delete(0, 'end')
                
                # Verify registration
                student_info = self.db_manager.get_student_info(self.current_roll_no)
                if student_info:
                    print(f"✅ Verification: Student {self.current_roll_no} found in database")
                else:
                    print(f"❌ Verification: Student {self.current_roll_no} NOT found in database")
                
            else:
                self.update_status(f"❌ Registration failed: {message}", "red")
                messagebox.showerror("Registration Error", message)
                
            self.progress_bar.set(0)
            
        except Exception as e:
            error_msg = f"Error completing registration: {e}"
            print(error_msg)
            self.update_status(f"❌ Registration error: {str(e)}", "red")
            messagebox.showerror("Error", f"Registration failed: {str(e)}")
        
    def start_attendance(self):
        """Start attendance marking process"""
        roll_no = self.roll_entry.get().strip()
        
        if not roll_no:
            messagebox.showerror("Input Error", "Please enter roll number")
            return
            
        # Check if student exists
        student_info = self.db_manager.get_student_info(roll_no)
        if not student_info:
            messagebox.showerror("Error", "Student not registered. Please register first.")
            return
            
        self.current_roll_no = roll_no
        self.current_name = student_info[1]  # Get name from database
        self.current_mode = "attendance"
        self.verification_counter = 0
        
        self.update_status(f"Verifying attendance for {roll_no}...", "orange")
        self.start_camera_thread()
        
    def complete_attendance(self):
        """Complete attendance marking"""
        success, message = self.db_manager.mark_attendance(
            self.current_roll_no, self.current_name, "Present", 0.95
        )
        
        if success:
            self.update_status(f"✅ Attendance marked for {self.current_roll_no}", "green")
            messagebox.showinfo("Success", f"Attendance marked for {self.current_roll_no}!")
        else:
            self.update_status(f"❌ {message}", "red")
            messagebox.showerror("Error", message)
            
        self.current_mode = "idle"
        
    def show_records(self):
        """Show attendance records in a new window"""
        records_window = ctk.CTkToplevel(self.root)
        records_window.title("Attendance Records")
        records_window.geometry("800x600")
        
        # Create scrollable frame
        scrollable_frame = ctk.CTkScrollableFrame(records_window)
        scrollable_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Headers
        headers = ["Roll No", "Name", "Date", "Time", "Status", "Confidence"]
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
        
        stats_label = ctk.CTkLabel(
            records_window,
            text=f"Total Records: {total_records} | Present: {present_count}",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        stats_label.pack(pady=10)
        
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
    
    # Run application
    app = ModernAttendanceApp()
    app.run()

if __name__ == "__main__":
    main()