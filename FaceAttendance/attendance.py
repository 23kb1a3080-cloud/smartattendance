"""
Real-Time Attendance Recognition Module
Verifies face against stored encoding and marks attendance with liveness detection.
"""

import cv2
import face_recognition
import pickle
import os
import sqlite3
from datetime import datetime
import numpy as np
from collections import deque

# Configuration
ENCODINGS_PATH = "encodings/encodings.pkl"
ATTENDANCE_DB = "attendance_db/attendance.db"
DATABASE_FOLDER = "attendance_db"
MATCH_THRESHOLD = 0.45  # Lower = stricter security
LIVENESS_FRAME_COUNT = 15


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
            confidence REAL,
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


def mark_attendance(roll_no, name, status, confidence=None):
    """Mark attendance in database."""
    if check_duplicate(roll_no, datetime.now().strftime('%Y-%m-%d')):
        return False, "Attendance already marked today"
    
    conn = sqlite3.connect(ATTENDANCE_DB)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO attendance (roll_no, name, date, time, status, confidence)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        roll_no,
        name,
        datetime.now().strftime('%Y-%m-%d'),
        datetime.now().strftime('%H:%M:%S'),
        status,
        confidence
    ))
    
    conn.commit()
    conn.close()
    
    return True, "Attendance marked successfully"


def get_known_encodings():
    """Load known face encodings from pickle file."""
    if not os.path.exists(ENCODINGS_PATH):
        print(f"Error: Encodings file '{ENCODINGS_PATH}' not found!")
        print("Please run train_model.py first.")
        return None, None, None
    
    with open(ENCODINGS_PATH, 'rb') as f:
        data = pickle.load(f)
    
    return data['encodings'], data['roll_numbers'], data['names']


def calculate_eye_aspect_ratio(eye):
    """Calculate Eye Aspect Ratio for blink detection."""
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])
    
    ear = (A + B) / (2.0 * C)
    return ear


def detect_liveness(frame, face_landmarks):
    """Detect liveness using blink detection and head movement."""
    # Get eye landmarks
    left_eye = face_landmarks['left_eye']
    right_eye = face_landmarks['right_eye']
    
    # Calculate EAR
    left_ear = calculate_eye_aspect_ratio(np.array(left_eye))
    right_ear = calculate_eye_aspect_ratio(np.array(right_eye))
    ear = (left_ear + right_ear) / 2.0
    
    return ear


def create_attendance_ticket(roll_no, name, status, confidence=None):
    """Create attendance confirmation ticket."""
    time_str = datetime.now().strftime('%H:%M %p')
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    if status == 'Present':
        color = (0, 255, 0)  # Green
        status_text = "Attended ✅"
    else:
        color = (0, 0, 255)  # Red
        status_text = "Not Verified ❌"
    
    # Create ticket image
    ticket = np.ones((400, 500, 3), dtype=np.uint8) * 255
    
    # Draw border
    cv2.rectangle(ticket, (10, 10), (490, 390), color, 8)
    
    # Title
    cv2.putText(ticket, "ATTENDANCE TICKET", (100, 50), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    
    # Roll Number
    cv2.putText(ticket, f"Roll No: {roll_no}", (50, 100), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    # Name
    cv2.putText(ticket, f"Name: {name}", (50, 140), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    # Date
    cv2.putText(ticket, f"Date: {date_str}", (50, 180), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 2)
    
    # Time
    cv2.putText(ticket, f"Time: {time_str}", (50, 220), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 2)
    
    # Status
    cv2.putText(ticket, status_text, (150, 280), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
    
    # Confidence
    if confidence is not None:
        cv2.putText(ticket, f"Confidence: {confidence:.2%}", (50, 330), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 2)
    
    return ticket


def recognize_face(roll_number_input):
    """Main recognition function with liveness detection."""
    print("\n" + "="*60)
    print("REAL-TIME ATTENDANCE RECOGNITION")
    print("="*60)
    
    # Initialize database
    init_database()
    
    # Load known encodings
    known_encodings, known_roll_numbers, known_names = get_known_encodings()
    
    if known_encodings is None:
        return
    
    # Check if input roll number exists in database
    if roll_number_input not in known_roll_numbers:
        print(f"Warning: Roll number {roll_number_input} not found in database!")
        print("Please register this student first.")
        return
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    # Face detection variables
    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True
    
    # Liveness detection variables
    blink_count = 0
    prev_ear = 0
    blink_threshold = 0.2
    liveness_frames = deque(maxlen=LIVENESS_FRAME_COUNT)
    
    print(f"\nLooking for student with Roll No: {roll_number_input}")
    print("Instructions:")
    print("1. Look straight at the camera")
    print("2. Blink your eyes to verify liveness")
    print("3. Hold for 2-3 seconds until ticket appears")
    print("\nPress 'q' to quit\n")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Only process every other frame
        if process_this_frame:
            # Find all faces and encodings
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            face_names = []
            match_found = False
            best_distance = 1.0
            
            for face_encoding in face_encodings:
                # Compare with known faces
                distances = face_recognition.face_distance(known_encodings, face_encoding)
                
                if len(distances) > 0:
                    min_distance = min(distances)
                    best_distance = min_distance
                    
                    if min_distance < MATCH_THRESHOLD:
                        match_index = np.argmin(distances)
                        name = known_roll_numbers[match_index]
                        match_found = True
                    else:
                        name = "Unknown"
                else:
                    name = "Unknown"
                
                face_names.append(name)
        
        process_this_frame = not process_this_frame
        
        # Display results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            
            # Draw box
            color = (0, 255, 0) if match_found and name == roll_number_input else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            
            # Draw label
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)
            
            # Display distance
            cv2.putText(frame, f"Distance: {best_distance:.2f}", (left, top - 10), 
                       font, 0.5, (255, 255, 255), 1)
        
        # Show frame
        cv2.imshow('Attendance System - Press q to quit', frame)
        
        # Process liveness if face found
        if match_found and len(face_locations) > 0:
            # Get face landmarks for liveness
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_landmarks_list = face_recognition.face_landmarks(rgb_frame)
            
            if len(face_landmarks_list) > 0:
                ear = detect_liveness(frame, face_landmarks_list[0])
                liveness_frames.append(ear)
                
                # Detect blink
                if prev_ear > 0 and ear < prev_ear * 0.8:
                    blink_count += 1
                
                prev_ear = ear
                
                # Show liveness status
                cv2.putText(frame, f"Blinks: {blink_count}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Check if liveness verified
                if blink_count >= 2 and len(liveness_frames) >= LIVENESS_FRAME_COUNT:
                    # Mark attendance
                    success, message = mark_attendance(
                        roll_number_input, 
                        roll_number_input,  # Using roll number as name
                        'Present',
                        1 - best_distance
                    )
                    
                    # Create and show ticket
                    ticket = create_attendance_ticket(
                        roll_number_input,
                        roll_number_input,
                        'Present',
                        1 - best_distance
                    )
                    
                    cv2.imshow('Attendance Ticket', ticket)
                    print(f"\n✓ Attendance marked for {roll_number_input}")
                    print(f"  Time: {datetime.now().strftime('%H:%M:%S')}")
                    print(f"  Confidence: {(1 - best_distance):.2%}")
                    
                    # Wait for ticket view
                    cv2.waitKey(3000)
                    break
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()


def main():
    """Main attendance function."""
    roll_number = input("\nEnter Roll Number: ").strip()
    
    if not roll_number:
        print("Error: Roll number cannot be empty")
        return
    
    recognize_face(roll_number)


if __name__ == "__main__":
    main()
