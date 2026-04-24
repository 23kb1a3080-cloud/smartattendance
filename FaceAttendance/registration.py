"""
Student Registration Module
Captures 30 face images per student from webcam and stores them in roll-number folders.
"""

import cv2
import os
import sys

# Configuration
DATASET_PATH = "dataset"
NUM_IMAGES = 30
CAMERA_INDEX = 0

# Check if face_recognition is available
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("Warning: face_recognition not available. Using basic OpenCV detection.")


def create_folder_structure(roll_number):
    """Create folder for student's face images."""
    student_path = os.path.join(DATASET_PATH, roll_number)
    os.makedirs(student_path, exist_ok=True)
    return student_path


def capture_faces(roll_number):
    """Capture 30 face images from webcam with multiple angles."""
    student_path = create_folder_structure(roll_number)
    
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return False
    
    # Load face detector
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    image_count = 0
    angles_captured = {'front': 0, 'left': 0, 'right': 0, 'up': 0, 'down': 0}
    
    print(f"\n{'='*60}")
    print(f"Student Registration - Roll No: {roll_number}")
    print(f"{'='*60}")
    print("\nInstructions:")
    print("1. Position your face in the center of the frame")
    print("2. Capture will start automatically")
    print("3. Follow on-screen prompts for different angles:")
    print("   - Front (10 images)")
    print("   - Left Profile (6 images)")
    print("   - Right Profile (6 images)")
    print("   - Up (4 images)")
    print("   - Down (4 images)")
    print("\nPress 'q' to quit early\n")
    
    while image_count < NUM_IMAGES:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame")
            break
        
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            # Draw rectangle around face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Calculate face position relative to frame center
            face_center_x = x + w // 2
            face_center_y = y + h // 2
            frame_center_x = frame.shape[1] // 2
            frame_center_y = frame.shape[0] // 2
            
            dx = face_center_x - frame_center_x
            dy = face_center_y - frame_center_y
            
            # Determine angle based on face position
            angle = 'front'
            if abs(dx) > 50:
                angle = 'left' if dx < 0 else 'right'
            elif dy < -30:
                angle = 'up'
            elif dy > 30:
                angle = 'down'
            
            # Capture if we haven't reached the limit for this angle
            if angles_captured[angle] < 10 and image_count < NUM_IMAGES:
                # Only capture every few frames to avoid duplicates
                if image_count % 3 == 0:
                    face_img = frame[y-20:y+h+20, x-20:x+w+20]
                    if face_img.size > 0:
                        filename = f"{roll_number}_{angle}_{image_count+1}.jpg"
                        filepath = os.path.join(student_path, filename)
                        cv2.imwrite(filepath, face_img)
                        image_count += 1
                        angles_captured[angle] += 1
                        
                        print(f"Captured [{image_count}/{NUM_IMAGES}] - {angle} angle")
        
        # Display instructions on frame
        cv2.putText(frame, f"Roll: {roll_number}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Images: {image_count}/{NUM_IMAGES}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Show angle progress
        y_pos = 90
        for angle, count in angles_captured.items():
            cv2.putText(frame, f"{angle.capitalize()}: {count}/10", (10, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            y_pos += 25
        
        cv2.imshow('Student Registration - Press q to quit', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\n{'='*60}")
    print(f"Registration Complete!")
    print(f"{'='*60}")
    print(f"Total images captured: {image_count}/{NUM_IMAGES}")
    print(f"Folder: {student_path}")
    
    if image_count < 10:
        print("\nWarning: Very few images captured. Consider re-registering.")
        return False
    
    return True


def main():
    """Main registration function."""
    print("\n" + "="*60)
    print("STUDENT FACE REGISTRATION SYSTEM")
    print("="*60)
    
    # Get roll number
    roll_number = input("\nEnter Roll Number: ").strip()
    
    if not roll_number:
        print("Error: Roll number cannot be empty")
        return
    
    # Check if student already exists
    student_path = os.path.join(DATASET_PATH, roll_number)
    if os.path.exists(student_path) and os.listdir(student_path):
        print(f"\nWarning: Student with roll number {roll_number} already exists!")
        choice = input("Overwrite existing data? (y/n): ").strip().lower()
        if choice != 'y':
            print("Registration cancelled.")
            return
        # Clear existing data
        import shutil
        shutil.rmtree(student_path)
    
    # Create dataset folder if it doesn't exist
    os.makedirs(DATASET_PATH, exist_ok=True)
    
    # Capture faces
    success = capture_faces(roll_number)
    
    if success:
        print(f"\n✓ Student {roll_number} registered successfully!")
        print("Next step: Run train_model.py to generate face encodings")
    else:
        print(f"\n✗ Registration incomplete. Please try again.")


if __name__ == "__main__":
    main()
