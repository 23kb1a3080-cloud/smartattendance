"""
Simple Attendance System using OpenCV only
Works without face_recognition library for basic demonstration.
"""

import cv2
import os
import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# Configuration
DATASET_PATH = "dataset"
ATTENDANCE_DB = "attendance_db/attendance.db"
DATABASE_FOLDER = "attendance_db"


def init_database():
    """Initialize SQLite database for attendance."""
    os.makedirs(DATABASE_FOLDER, exist_ok=True)
    
    conn = sqlite3.connect(ATTENDANCE_DB)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL,
            UNIQUE(roll_no, date)
        )
    ''')
    
    conn.commit()
    conn.close()


def check_duplicate(roll_no, date):
    """Check if attendance already marked for this student on this date."""
    conn = sqlite3.connect(ATTENDANCE_DB)
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT id FROM attendance WHERE roll_no = ? AND date = ?',
        (roll_no, date)
    )
    
    result = cursor.fetchone()
    conn.close()
    
    return result is not None


def mark_attendance(roll_no, name, status):
    """Mark attendance in database."""
    if check_duplicate(roll_no, datetime.now().strftime('%Y-%m-%d')):
        return False, "Attendance already marked today"
    
    conn = sqlite3.connect(ATTENDANCE_DB)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO attendance (roll_no, name, date, time, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        roll_no,
        name,
        datetime.now().strftime('%Y-%m-%d'),
        datetime.now().strftime('%H:%M:%S'),
        status
    ))
    
    conn.commit()
    conn.close()
    
    return True, "Attendance marked successfully"


def capture_student_images(roll_number, num_images=10):
    """Capture face images for student registration."""
    student_path = os.path.join(DATASET_PATH, roll_number)
    os.makedirs(student_path, exist_ok=True)
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        return False, "Could not open webcam"
    
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    image_count = 0
    
    print(f"Capturing {num_images} images for {roll_number}")
    print("Press SPACE to capture, ESC to exit")
    
    while image_count < num_images:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        cv2.putText(frame, f"Roll: {roll_number}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Images: {image_count}/{num_images}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(frame, "Press SPACE to capture", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        cv2.imshow('Registration - Press SPACE to capture, ESC to exit', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 32:  # Space key
            if len(faces) > 0:
                filename = f"{roll_number}_{image_count+1}.jpg"
                filepath = os.path.join(student_path, filename)
                cv2.imwrite(filepath, frame)
                image_count += 1
                print(f"Captured image {image_count}/{num_images}")
            else:
                print("No face detected. Please position your face in the frame.")
        elif key == 27:  # ESC key
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    return image_count >= 5, f"Captured {image_count} images"


def verify_attendance(roll_number):
    """Simple attendance verification using face detection."""
    # Check if student is registered
    student_path = os.path.join(DATASET_PATH, roll_number)
    if not os.path.exists(student_path):
        return False, "Student not registered"
    
    # Check if already marked today
    if check_duplicate(roll_number, datetime.now().strftime('%Y-%m-%d')):
        return False, "Attendance already marked today"
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        return False, "Could not open webcam"
    
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    print(f"Verifying attendance for {roll_number}")
    print("Press SPACE when your face is detected, ESC to cancel")
    
    verified = False
    
    while not verified:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, "Face Detected", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        cv2.putText(frame, f"Roll: {roll_number}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Press SPACE to mark attendance", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        cv2.imshow('Attendance Verification - Press SPACE to confirm, ESC to cancel', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 32:  # Space key
            if len(faces) > 0:
                success, message = mark_attendance(roll_number, roll_number, 'Present')
                verified = True
                cap.release()
                cv2.destroyAllWindows()
                return success, message
            else:
                print("No face detected. Please position your face in the frame.")
        elif key == 27:  # ESC key
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    return False, "Verification cancelled"


class SimpleAttendanceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Face Attendance System")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        self.create_widgets()
        init_database()
    
    def create_widgets(self):
        # Title
        title_label = ttk.Label(
            self.root,
            text="Simple Face Attendance System",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # Roll Number Input
        input_frame = ttk.Frame(self.root)
        input_frame.pack(pady=20)
        
        ttk.Label(input_frame, text="Roll Number:").pack(side=tk.LEFT, padx=5)
        
        self.roll_var = tk.StringVar()
        self.roll_entry = ttk.Entry(input_frame, textvariable=self.roll_var, width=20)
        self.roll_entry.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=20)
        
        ttk.Button(
            button_frame,
            text="📝 Register Student",
            command=self.register_student,
            width=20
        ).pack(pady=5)
        
        ttk.Button(
            button_frame,
            text="✅ Mark Attendance",
            command=self.mark_attendance,
            width=20
        ).pack(pady=5)
        
        ttk.Button(
            button_frame,
            text="📊 View Records",
            command=self.view_records,
            width=20
        ).pack(pady=5)
        
        # Status
        self.status_var = tk.StringVar(value="System Ready")
        status_label = ttk.Label(self.root, textvariable=self.status_var, foreground="green")
        status_label.pack(pady=10)
    
    def register_student(self):
        roll_number = self.roll_var.get().strip()
        if not roll_number:
            messagebox.showwarning("Input Error", "Please enter a roll number")
            return
        
        self.status_var.set("Registration in progress...")
        self.root.update()
        
        def register():
            success, message = capture_student_images(roll_number)
            self.root.after(0, lambda: self.on_register_complete(success, message))
        
        threading.Thread(target=register, daemon=True).start()
    
    def on_register_complete(self, success, message):
        if success:
            self.status_var.set("Registration completed successfully")
            messagebox.showinfo("Success", message)
        else:
            self.status_var.set("Registration failed")
            messagebox.showerror("Error", message)
    
    def mark_attendance(self):
        roll_number = self.roll_var.get().strip()
        if not roll_number:
            messagebox.showwarning("Input Error", "Please enter a roll number")
            return
        
        self.status_var.set("Attendance verification in progress...")
        self.root.update()
        
        def verify():
            success, message = verify_attendance(roll_number)
            self.root.after(0, lambda: self.on_attendance_complete(success, message))
        
        threading.Thread(target=verify, daemon=True).start()
    
    def on_attendance_complete(self, success, message):
        if success:
            self.status_var.set("Attendance marked successfully")
            messagebox.showinfo("Success", f"✅ {message}")
        else:
            self.status_var.set("Attendance verification failed")
            messagebox.showerror("Error", f"❌ {message}")
    
    def view_records(self):
        conn = sqlite3.connect(ATTENDANCE_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT roll_no, name, date, time, status 
            FROM attendance 
            ORDER BY date DESC, time DESC
        ''')
        
        records = cursor.fetchall()
        conn.close()
        
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title("Attendance Records")
        popup.geometry("600x400")
        
        # Treeview
        columns = ('Roll No', 'Name', 'Date', 'Time', 'Status')
        tree = ttk.Treeview(popup, columns=columns, show='headings')
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(popup, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add records
        for record in records:
            tree.insert('', tk.END, values=record)
        
        # Stats
        if records:
            total = len(records)
            present = len([r for r in records if r[4] == 'Present'])
            stats_label = ttk.Label(popup, text=f"Total Records: {total} | Present: {present}")
            stats_label.pack(pady=5)


def main():
    """Main function."""
    # Create dataset folder
    os.makedirs(DATASET_PATH, exist_ok=True)
    
    root = tk.Tk()
    app = SimpleAttendanceGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()