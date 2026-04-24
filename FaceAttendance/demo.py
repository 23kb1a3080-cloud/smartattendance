"""
Demo script to showcase the Face Attendance System
"""

import time as time_module
from modern_attendance import DatabaseManager

def demo_database_operations():
    """Demonstrate database operations"""
    print("🎯 Face Attendance System Demo")
    print("=" * 40)
    
    db = DatabaseManager()
    
    # Demo students
    students = [
        ("22001", "Alice Johnson", "Computer Science"),
        ("22002", "Bob Smith", "Electronics"),
        ("22003", "Carol Davis", "Mechanical"),
        ("22004", "David Wilson", "Civil"),
        ("22005", "Eva Brown", "Computer Science")
    ]
    
    print("\n📝 Registering Demo Students...")
    for roll_no, name, dept in students:
        success, message = db.register_student(roll_no, name, dept)
        print(f"  {roll_no} - {name}: {'✅' if success else '❌'}")
        time_module.sleep(0.1)
    
    print("\n✅ Marking Sample Attendance...")
    attendance_data = [
        ("22001", "Alice Johnson", "Present", 0.95),
        ("22002", "Bob Smith", "Present", 0.88),
        ("22003", "Carol Davis", "Present", 0.92),
        ("22005", "Eva Brown", "Present", 0.97)
    ]
    
    for roll_no, name, status, confidence in attendance_data:
        success, message = db.mark_attendance(roll_no, name, status, confidence)
        print(f"  {roll_no} - {name}: {'✅' if success else '❌'}")
        time_module.sleep(0.1)
    
    print("\n📊 Attendance Summary:")
    records = db.get_attendance_records()
    
    print(f"{'Roll No':<8} {'Name':<15} {'Date':<12} {'Time':<10} {'Status':<8} {'Confidence'}")
    print("-" * 70)
    
    for record in records:
        roll_no, name, date, time_str, status, confidence = record
        conf_str = f"{confidence:.1%}" if confidence else "N/A"
        print(f"{roll_no:<8} {name:<15} {date:<12} {time_str:<10} {status:<8} {conf_str}")
    
    print(f"\n📈 Statistics:")
    print(f"  Total Students Registered: {len(students)}")
    print(f"  Total Attendance Records: {len(records)}")
    print(f"  Present Today: {len([r for r in records if r[4] == 'Present'])}")
    print(f"  Attendance Rate: {len(records)/len(students)*100:.1f}%")
    
    print("\n🚀 System Ready!")
    print("Run 'python modern_attendance.py' to start the GUI application")

if __name__ == "__main__":
    demo_database_operations()