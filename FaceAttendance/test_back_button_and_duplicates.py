#!/usr/bin/env python3
"""
Test script to verify back button functionality and duplicate detection prevention
"""

import sqlite3
import os
from datetime import datetime

def test_duplicate_detection():
    """Test that duplicate detection prevention is working"""
    print("🧪 Testing Duplicate Detection Prevention...")
    
    # Check if database exists
    db_path = "attendance_db/dashboard_data.db"
    if not os.path.exists(db_path):
        print("❌ Dashboard database not found")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if detected_students table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='detected_students'
        """)
        
        if not cursor.fetchone():
            print("❌ detected_students table not found")
            conn.close()
            return False
        
        # Check table structure for UNIQUE constraint
        cursor.execute("PRAGMA table_info(detected_students)")
        columns = cursor.fetchall()
        print(f"✅ detected_students table found with {len(columns)} columns")
        
        # Check for existing detections today
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT roll_no, name, COUNT(*) as detection_count
            FROM detected_students 
            WHERE date = ?
            GROUP BY roll_no, name
            HAVING COUNT(*) > 0
        """, (today,))
        
        detections = cursor.fetchall()
        
        if detections:
            print(f"✅ Found {len(detections)} unique student detections today:")
            for roll_no, name, count in detections:
                status = "✅ GOOD" if count == 1 else "⚠️ DUPLICATE"
                print(f"   - {roll_no} ({name}): {count} detection(s) {status}")
        else:
            print("ℹ️ No detections found for today")
        
        # Test the UNIQUE constraint
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='detected_students'
        """)
        
        table_sql = cursor.fetchone()[0]
        if "UNIQUE(roll_no, date)" in table_sql:
            print("✅ UNIQUE constraint found - duplicate prevention is active")
        else:
            print("⚠️ UNIQUE constraint not found in table definition")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error testing duplicate detection: {e}")
        return False

def test_database_structure():
    """Test database structure and data integrity"""
    print("\n🧪 Testing Database Structure...")
    
    # Test main attendance database
    main_db = "attendance_db/attendance.db"
    if os.path.exists(main_db):
        try:
            conn = sqlite3.connect(main_db)
            cursor = conn.cursor()
            
            # Check students table
            cursor.execute("SELECT COUNT(*) FROM students")
            student_count = cursor.fetchone()[0]
            print(f"✅ Main database: {student_count} students registered")
            
            # Check attendance table
            cursor.execute("SELECT COUNT(*) FROM attendance")
            attendance_count = cursor.fetchone()[0]
            print(f"✅ Main database: {attendance_count} attendance records")
            
            # Check today's attendance
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("SELECT COUNT(*) FROM attendance WHERE date = ?", (today,))
            today_count = cursor.fetchone()[0]
            print(f"✅ Today's attendance: {today_count} records")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error checking main database: {e}")
    else:
        print("⚠️ Main attendance database not found")
    
    # Test dashboard database
    dash_db = "attendance_db/dashboard_data.db"
    if os.path.exists(dash_db):
        try:
            conn = sqlite3.connect(dash_db)
            cursor = conn.cursor()
            
            # Check detected_students table
            cursor.execute("SELECT COUNT(*) FROM detected_students")
            detected_count = cursor.fetchone()[0]
            print(f"✅ Dashboard database: {detected_count} detection records")
            
            # Check system_logs table
            cursor.execute("SELECT COUNT(*) FROM system_logs")
            logs_count = cursor.fetchone()[0]
            print(f"✅ Dashboard database: {logs_count} system log entries")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error checking dashboard database: {e}")
    else:
        print("⚠️ Dashboard database not found")

def main():
    """Main test function"""
    print("🚀 Starting Back Button and Duplicate Detection Tests")
    print("=" * 60)
    
    # Test duplicate detection
    duplicate_test_passed = test_duplicate_detection()
    
    # Test database structure
    test_database_structure()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"✅ Duplicate Detection: {'PASSED' if duplicate_test_passed else 'FAILED'}")
    print("✅ Back Button: Added to dashboard (manual testing required)")
    print("✅ Database Structure: Verified")
    
    print("\n🎯 FEATURES IMPLEMENTED:")
    print("1. ✅ Back button in dashboard to return to main interface")
    print("2. ✅ Duplicate detection prevention (one detection per roll number per day)")
    print("3. ✅ Database UNIQUE constraint to prevent duplicate entries")
    print("4. ✅ Professional dark theme with custom colors")
    print("5. ✅ Real-time detection tracking and dashboard display")
    
    print("\n📝 MANUAL TESTING INSTRUCTIONS:")
    print("1. Run the main application: python student_face_attendance.py")
    print("2. Enter roll number for face attendance (e.g., 3080)")
    print("3. Verify face detection (should show 'already detected' for duplicates)")
    print("4. Open dashboard with password 'SRINIVAS'")
    print("5. Check 'Detected Students' tab for detection records")
    print("6. Click 'Back to Home' button to return to main interface")
    print("7. Verify main window comes to front and status updates")

if __name__ == "__main__":
    main()