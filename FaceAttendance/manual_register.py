"""
Manual registration script to test database functionality
"""

from modern_attendance import DatabaseManager
import os

def manual_register():
    """Manually register a student"""
    print("🎯 Manual Student Registration")
    print("=" * 40)
    
    # Get input
    roll_no = input("Enter Roll Number: ").strip()
    name = input("Enter Student Name: ").strip()
    dept = input("Enter Department (optional): ").strip() or "Unknown"
    
    if not roll_no or not name:
        print("❌ Roll number and name are required!")
        return
    
    # Initialize database
    db = DatabaseManager()
    
    # Register student
    print(f"\nRegistering: {roll_no} - {name} ({dept})")
    success, message = db.register_student(roll_no, name, dept)
    
    if success:
        print(f"✅ {message}")
        
        # Create image folder
        student_dir = os.path.join("dataset", roll_no)
        os.makedirs(student_dir, exist_ok=True)
        
        # Create dummy images
        for i in range(5):
            dummy_file = os.path.join(student_dir, f"{roll_no}_{i+1:03d}.jpg")
            with open(dummy_file, 'w') as f:
                f.write("dummy image data")
        
        print(f"✅ Created folder with 5 dummy images")
        
        # Verify registration
        student_info = db.get_student_info(roll_no)
        if student_info:
            print(f"✅ Verification: Found in database - {student_info}")
        else:
            print(f"❌ Verification: NOT found in database")
            
        # Test attendance
        print(f"\nTesting attendance for {roll_no}...")
        att_success, att_message = db.mark_attendance(roll_no, name, "Present", 0.95)
        print(f"Attendance: {'✅' if att_success else '❌'} {att_message}")
        
    else:
        print(f"❌ {message}")

if __name__ == "__main__":
    manual_register()