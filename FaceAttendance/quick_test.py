"""
Quick test of registration functionality
"""

from modern_attendance import DatabaseManager
import os

def quick_test():
    """Quick test registration"""
    print("🧪 Quick Registration Test")
    print("=" * 30)
    
    # Test data
    test_students = [
        ("STU001", "John Doe", "Computer Science"),
        ("STU002", "Jane Smith", "Electronics"),
        ("3080", "Existing Student", "IT")  # This one already has images
    ]
    
    db = DatabaseManager()
    
    for roll_no, name, dept in test_students:
        print(f"\nTesting: {roll_no} - {name}")
        
        # Register
        success, message = db.register_student(roll_no, name, dept)
        print(f"  Registration: {'✅' if success else '❌'} {message}")
        
        if success:
            # Verify
            student_info = db.get_student_info(roll_no)
            if student_info:
                print(f"  Verification: ✅ Found - {student_info[1]} ({student_info[2]})")
                
                # Test attendance
                att_success, att_message = db.mark_attendance(roll_no, name, "Present", 0.90)
                print(f"  Attendance: {'✅' if att_success else '❌'} {att_message}")
            else:
                print(f"  Verification: ❌ Not found in database")
    
    # Show final status
    print(f"\n📊 Final Database Status:")
    try:
        import sqlite3
        conn = sqlite3.connect("attendance_db/attendance.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM students")
        student_count = cursor.fetchone()[0]
        print(f"  Total students: {student_count}")
        
        cursor.execute("SELECT COUNT(*) FROM attendance")
        attendance_count = cursor.fetchone()[0]
        print(f"  Total attendance: {attendance_count}")
        
        cursor.execute("SELECT roll_no, name FROM students ORDER BY id DESC LIMIT 3")
        recent_students = cursor.fetchall()
        print(f"  Recent registrations:")
        for roll_no, name in recent_students:
            print(f"    {roll_no}: {name}")
        
        conn.close()
        
    except Exception as e:
        print(f"  Database error: {e}")

if __name__ == "__main__":
    quick_test()