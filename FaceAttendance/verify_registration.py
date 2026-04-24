"""
Verify registration functionality
"""

import os
import sqlite3
from modern_attendance import DatabaseManager

def check_dataset_folder():
    """Check if dataset folder and student folders exist"""
    print("📁 Checking Dataset Structure...")
    
    if not os.path.exists("dataset"):
        print("  ❌ Dataset folder missing")
        return False
    
    student_folders = [f for f in os.listdir("dataset") if os.path.isdir(os.path.join("dataset", f))]
    print(f"  ✅ Found {len(student_folders)} student folders")
    
    for folder in student_folders:
        folder_path = os.path.join("dataset", folder)
        images = [f for f in os.listdir(folder_path) if f.endswith(('.jpg', '.jpeg', '.png'))]
        print(f"    {folder}: {len(images)} images")
    
    return len(student_folders) > 0

def check_database():
    """Check database contents"""
    print("\n🗄️ Checking Database...")
    
    try:
        conn = sqlite3.connect("attendance_db/attendance.db")
        cursor = conn.cursor()
        
        # Check students
        cursor.execute("SELECT COUNT(*) FROM students")
        student_count = cursor.fetchone()[0]
        print(f"  ✅ Students in database: {student_count}")
        
        if student_count > 0:
            cursor.execute("SELECT roll_no, name, department FROM students")
            students = cursor.fetchall()
            for roll_no, name, dept in students:
                print(f"    {roll_no}: {name} ({dept})")
        
        # Check attendance
        cursor.execute("SELECT COUNT(*) FROM attendance")
        attendance_count = cursor.fetchone()[0]
        print(f"  ✅ Attendance records: {attendance_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def test_manual_registration():
    """Test manual registration"""
    print("\n🧪 Testing Manual Registration...")
    
    db = DatabaseManager()
    
    # Test registration
    test_roll = "TEST123"
    test_name = "Test Student"
    test_dept = "Test Department"
    
    success, message = db.register_student(test_roll, test_name, test_dept)
    print(f"  Registration: {'✅' if success else '❌'} {message}")
    
    if success:
        # Create test folder and images
        test_folder = os.path.join("dataset", test_roll)
        os.makedirs(test_folder, exist_ok=True)
        
        # Create dummy image files
        for i in range(5):
            dummy_file = os.path.join(test_folder, f"{test_roll}_{i+1:03d}.jpg")
            with open(dummy_file, 'w') as f:
                f.write("dummy")
        
        print(f"  ✅ Created test folder with 5 dummy images")
    
    return success

def main():
    """Main verification function"""
    print("🔍 Registration Verification")
    print("=" * 40)
    
    # Check components
    dataset_ok = check_dataset_folder()
    database_ok = check_database()
    manual_ok = test_manual_registration()
    
    print("\n" + "=" * 40)
    print("📊 Verification Results:")
    print(f"  Dataset Structure: {'✅' if dataset_ok else '❌'}")
    print(f"  Database Access: {'✅' if database_ok else '❌'}")
    print(f"  Manual Registration: {'✅' if manual_ok else '❌'}")
    
    if all([dataset_ok or manual_ok, database_ok, manual_ok]):
        print("\n✅ Registration system is working!")
        print("\nTo test GUI registration:")
        print("1. Run: python modern_attendance.py")
        print("2. Enter roll number and name")
        print("3. Click 'Register Student'")
        print("4. Position face in camera view")
        print("5. Wait for auto-capture to complete")
    else:
        print("\n❌ Some issues found. Check the errors above.")

if __name__ == "__main__":
    main()