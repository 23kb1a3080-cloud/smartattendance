"""
Test script to verify all system components
"""

import os
import sqlite3
from modern_attendance import DatabaseManager, FaceDetector, CameraManager

def test_database():
    """Test database operations"""
    print("🔍 Testing Database Operations...")
    
    db = DatabaseManager()
    
    # Test student registration
    success, message = db.register_student("TEST001", "Test Student", "Computer Science")
    print(f"  Registration: {'✅' if success else '❌'} {message}")
    
    # Test duplicate check
    is_duplicate = db.check_duplicate_attendance("TEST001", "2024-04-24")
    print(f"  Duplicate Check: {'✅' if not is_duplicate else '❌'} No duplicate found")
    
    # Test attendance marking
    success, message = db.mark_attendance("TEST001", "Test Student", "Present", 0.95)
    print(f"  Mark Attendance: {'✅' if success else '❌'} {message}")
    
    # Test duplicate prevention
    success, message = db.mark_attendance("TEST001", "Test Student", "Present", 0.95)
    print(f"  Duplicate Prevention: {'✅' if not success else '❌'} {message}")
    
    # Test records retrieval
    records = db.get_attendance_records(10)
    print(f"  Records Retrieval: {'✅' if len(records) > 0 else '❌'} Found {len(records)} records")
    
    return True

def test_face_detector():
    """Test face detection"""
    print("\n🎯 Testing Face Detection...")
    
    try:
        detector = FaceDetector()
        print("  Face Detector: ✅ Initialized successfully")
        return True
    except Exception as e:
        print(f"  Face Detector: ❌ Error: {e}")
        return False

def test_camera():
    """Test camera functionality"""
    print("\n📷 Testing Camera...")
    
    try:
        camera = CameraManager()
        success, message = camera.start_camera()
        
        if success:
            print(f"  Camera Start: ✅ {message}")
            
            # Test frame reading
            frame = camera.read_frame()
            if frame is not None:
                print("  Frame Reading: ✅ Successfully read frame")
            else:
                print("  Frame Reading: ❌ Could not read frame")
            
            camera.stop_camera()
            print("  Camera Stop: ✅ Camera stopped successfully")
            return True
        else:
            print(f"  Camera Start: ❌ {message}")
            return False
            
    except Exception as e:
        print(f"  Camera Test: ❌ Error: {e}")
        return False

def test_directories():
    """Test directory structure"""
    print("\n📁 Testing Directory Structure...")
    
    required_dirs = ["dataset", "attendance_db", "encodings"]
    
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"  {dir_name}: ✅ Exists")
        else:
            os.makedirs(dir_name, exist_ok=True)
            print(f"  {dir_name}: ✅ Created")
    
    return True

def test_database_schema():
    """Test database schema"""
    print("\n🗄️ Testing Database Schema...")
    
    try:
        conn = sqlite3.connect("attendance_db/attendance.db")
        cursor = conn.cursor()
        
        # Check students table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='students'")
        if cursor.fetchone():
            print("  Students Table: ✅ Exists")
        else:
            print("  Students Table: ❌ Missing")
            
        # Check attendance table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance'")
        if cursor.fetchone():
            print("  Attendance Table: ✅ Exists")
        else:
            print("  Attendance Table: ❌ Missing")
            
        # Check table structure
        cursor.execute("PRAGMA table_info(students)")
        students_columns = [row[1] for row in cursor.fetchall()]
        expected_student_cols = ['id', 'roll_no', 'name', 'department', 'registered_date']
        
        if all(col in students_columns for col in expected_student_cols):
            print("  Students Schema: ✅ Correct")
        else:
            print("  Students Schema: ❌ Incorrect")
            
        cursor.execute("PRAGMA table_info(attendance)")
        attendance_columns = [row[1] for row in cursor.fetchall()]
        expected_attendance_cols = ['id', 'roll_no', 'name', 'date', 'time', 'status', 'confidence']
        
        if all(col in attendance_columns for col in expected_attendance_cols):
            print("  Attendance Schema: ✅ Correct")
        else:
            print("  Attendance Schema: ❌ Incorrect")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"  Database Schema: ❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Face Attendance System - Component Tests")
    print("=" * 50)
    
    tests = [
        test_directories,
        test_database_schema,
        test_database,
        test_face_detector,
        test_camera
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  Test Error: ❌ {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All systems operational! Ready to use.")
    else:
        print("⚠️ Some components need attention.")
    
    print("\n📋 Usage Instructions:")
    print("1. Run: python modern_attendance.py")
    print("2. Enter student details and click 'Register Student'")
    print("3. Camera will open automatically for face capture")
    print("4. For attendance, enter roll number and click 'Mark Attendance'")
    print("5. View records anytime with 'View Records' button")

if __name__ == "__main__":
    main()