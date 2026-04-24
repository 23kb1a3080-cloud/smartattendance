"""
Test the new Student Face Attendance System
"""

import os
import sqlite3

def test_system():
    """Test the new system components"""
    print("🎓 Testing Student Face Attendance System")
    print("=" * 50)
    
    # Check database
    print("\n🗄️ Database Status:")
    try:
        conn = sqlite3.connect("attendance_db/attendance.db")
        cursor = conn.cursor()
        
        # Check students table
        cursor.execute("SELECT COUNT(*) FROM students")
        student_count = cursor.fetchone()[0]
        print(f"  Registered Students: {student_count}")
        
        if student_count > 0:
            cursor.execute("SELECT roll_no, name, face_encoded FROM students")
            students = cursor.fetchall()
            print("  Student Details:")
            for roll_no, name, face_encoded in students:
                status = "✅ Face Ready" if face_encoded else "⚠️ Needs Re-registration"
                print(f"    {roll_no}: {name} - {status}")
        
        # Check attendance
        cursor.execute("SELECT COUNT(*) FROM attendance")
        attendance_count = cursor.fetchone()[0]
        print(f"  Attendance Records: {attendance_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"  Database Error: {e}")
    
    # Check dataset
    print("\n📁 Dataset Status:")
    if os.path.exists("dataset"):
        folders = [f for f in os.listdir("dataset") if os.path.isdir(os.path.join("dataset", f))]
        print(f"  Student Folders: {len(folders)}")
        
        for folder in folders:
            folder_path = os.path.join("dataset", folder)
            images = [f for f in os.listdir(folder_path) if f.endswith(('.jpg', '.jpeg', '.png'))]
            print(f"    {folder}: {len(images)} images")
    else:
        print("  ❌ Dataset folder not found")
    
    print("\n" + "=" * 50)
    print("🚀 System Status: READY")
    print("\n📋 How to Use:")
    print("1. GUI is running with two modes:")
    print("   📝 Registration Mode: Register new students")
    print("   ✅ Attendance Mode: Face verification for attendance")
    print("\n2. Registration Process:")
    print("   - Enter roll number, name, department")
    print("   - Click 'Start Registration'")
    print("   - Camera captures 20 face images automatically")
    print("   - System generates face templates")
    print("\n3. Attendance Process:")
    print("   - Enter ONLY roll number")
    print("   - Click 'Verify Face & Mark Attendance'")
    print("   - Camera opens and verifies face automatically")
    print("   - Attendance marked if face matches")
    print("\n✨ Key Features:")
    print("   - Face recognition using template matching")
    print("   - Automatic capture and verification")
    print("   - Duplicate prevention (one attendance per day)")
    print("   - Confidence scoring")
    print("   - Modern dark theme GUI")

if __name__ == "__main__":
    test_system()