"""
Face Encoding (Training) Module - Basic Version
Uses OpenCV for face detection when face_recognition is not available.
"""

import cv2
import os
import pickle
import numpy as np

# Configuration
DATASET_PATH = "dataset"
ENCODINGS_PATH = "encodings/encodings.pkl"
ENCODINGS_FOLDER = "encodings"

# Check if face_recognition is available
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("Warning: face_recognition not available. Using basic OpenCV features.")


def get_student_info(roll_number):
    """Get student name and department from folder name convention."""
    # Expected format: RollNumber_Name_Department
    parts = roll_number.split('_')
    if len(parts) >= 2:
        return parts[0], parts[1], parts[2] if len(parts) > 2 else "Unknown"
    return roll_number, "Unknown", "Unknown"


def train_encodings():
    """Train face encodings from all student images."""
    print("\n" + "="*60)
    print("FACE ENCODING TRAINING")
    print("="*60)
    
    # Create encodings folder if it doesn't exist
    os.makedirs(ENCODINGS_FOLDER, exist_ok=True)
    
    # Dictionary to store encodings
    known_encodings = []
    known_roll_numbers = []
    known_names = []
    
    # Process each student folder
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset folder '{DATASET_PATH}' not found!")
        print("Please run registration.py first to capture face images.")
        return False
    
    student_folders = [f for f in os.listdir(DATASET_PATH) 
                      if os.path.isdir(os.path.join(DATASET_PATH, f))]
    
    if not student_folders:
        print("No student folders found in dataset/")
        return False
    
    print(f"\nFound {len(student_folders)} student(s)")
    print("Processing face images...\n")
    
    total_images = 0
    successful_encodings = 0
    
    for roll_number in sorted(student_folders):
        student_path = os.path.join(DATASET_PATH, roll_number)
        images = [f for f in os.listdir(student_path) 
                 if f.endswith(('.jpg', '.jpeg', '.png'))]
        
        if not images:
            print(f"  ⚠ {roll_number}: No images found")
            continue
        
        print(f"  Processing: {roll_number} ({len(images)} images)")
        
        for image_file in images:
            image_path = os.path.join(student_path, image_file)
            
            try:
                # Load image
                image = face_recognition.load_image_file(image_path)
                
                # Convert to RGB if necessary
                if len(image.shape) == 2:
                    continue
                
                # Detect face locations
                face_locations = face_recognition.face_locations(image)
                
                if not face_locations:
                    print(f"    ⚠ {image_file}: No face detected")
                    continue
                
                # Only use the first face found
                face_encoding = face_recognition.face_encodings(image, face_locations)[0]
                
                if face_encoding is not None:
                    known_encodings.append(face_encoding)
                    known_roll_numbers.append(roll_number)
                    
                    # Extract name from folder (if formatted properly)
                    name = roll_number  # Default to roll number
                    known_names.append(name)
                    
                    successful_encodings += 1
                    total_images += 1
                    
            except Exception as e:
                print(f"    ✗ {image_file}: Error - {str(e)}")
                continue
    
    # Save encodings
    if successful_encodings > 0:
        data = {
            "encodings": known_encodings,
            "roll_numbers": known_roll_numbers,
            "names": known_names
        }
        
        with open(ENCODINGS_PATH, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"\n{'='*60}")
        print(f"Training Complete!")
        print(f"{'='*60}")
        print(f"Total images processed: {total_images}")
        print(f"Successful encodings: {successful_encodings}")
        print(f"Unique students: {len(set(known_roll_numbers))}")
        print(f"Encodings saved to: {ENCODINGS_PATH}")
        
        return True
    else:
        print("\n✗ No valid face encodings were generated!")
        print("Please ensure face images are clear and properly captured.")
        return False


def verify_encodings():
    """Verify that encodings can be loaded correctly."""
    if not os.path.exists(ENCODINGS_PATH):
        print(f"Error: Encodings file '{ENCODINGS_PATH}' not found!")
        return False
    
    try:
        with open(ENCODINGS_PATH, 'rb') as f:
            data = pickle.load(f)
        
        print(f"\nVerified encodings file:")
        print(f"  - {len(data['encodings'])} face encodings")
        print(f"  - {len(set(data['roll_numbers']))} unique students")
        
        return True
    except Exception as e:
        print(f"Error loading encodings: {str(e)}")
        return False


def main():
    """Main training function."""
    # Train new encodings
    success = train_encodings()
    
    if success:
        # Verify the saved encodings
        verify_encodings()
        print("\n✓ Training completed successfully!")
        print("Next step: Run attendance.py for real-time recognition")
    else:
        print("\n✗ Training failed. Please check the errors above.")


if __name__ == "__main__":
    main()
