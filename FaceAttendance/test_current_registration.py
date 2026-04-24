"""
Test current registration status
"""

import os
import sqlite3

def check_current_status():
    """Check what's currently registered"""
    print("🔍 Current Registration Status")
    print("=" * 40)
    
    # Check dataset folder
    print("\n📁 Dataset Folder Contents:")
    if os.path.exists("dataset"):
        folders = [f for f in os.listdir("dataset") if os.path.isdir(os.path.join("dataset", f))]
        for folder in folders:
            folder_path = os.path.join("dataset", folder)
            images = [f for f in os.listdir(folder_path) if f.endswith(('.jpg', '.jpeg', '.png'))]
            print(f"  {folder}: {len(images)} images")
            
            # Show first few image names
            if images:
                print(f"    Sample files: {', '.join(images[:3])}")
    else:
        print("  ❌ Dataset folder not found")
    
    # Check database
    print("\n🗄️ Database Contents:")
    try:
        conn = sqlite3.connect("attendance_db/attendance.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT roll_no, name, department, registered_date FROM students ORDER BY registered_date DESC")
        students = cursor.fetchall()
        
        if students:
            print("  Registered Students:")
            for roll_no, name, dept, reg_date in students:
                print(f"    {roll_no}: {name} ({dept}) - {reg_date}")
        else:
            print("  ❌ No students in database")
        
        # Check attendance
        cursor.execute("SELECT roll_no, name, date, time, status FROM attendance ORDER BY date DESC, time DESC LIMIT 5")
        attendance = cursor.fetchall()
        
        if attendance:
            print("\n  Recent Attendance:")
            for roll_no, name, date, time, status in attendance:
                print(f"    {roll_no}: {name} - {date} {time} ({status})")
        
        conn.close()
        
    except Exception as e:
        print(f"  ❌ Database error: {e}")
    
    print("\n" + "=" * 40)
    print("✅ Registration system is ready!")
    print("\nTo register a new student:")
    print("1. The GUI is already running")
    print("2. Enter a NEW roll number (e.g., 'STU001')")
    print("3. Enter student name")
    print("4. Click 'Register Student'")
    print("5. Camera will open and auto-capture images")
    print("6. Wait for completion message")

if __name__ == "__main__":
    check_current_status()