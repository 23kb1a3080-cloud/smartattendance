"""
Test Dashboard System with SRINIVAS lock
"""

from dashboard_system import dashboard_manager
import json

def test_dashboard_lock():
    """Test the dashboard lock system"""
    print("🔒 Testing Dashboard Lock System")
    print("=" * 40)
    
    # Test wrong password
    print("\n1. Testing wrong password:")
    success, message = dashboard_manager.verify_access("wrong_password")
    print(f"   Result: {'✅' if not success else '❌'} {message}")
    
    # Test correct password
    print("\n2. Testing correct password (SRINIVAS):")
    success, session_token = dashboard_manager.verify_access("SRINIVAS")
    print(f"   Result: {'✅' if success else '❌'} {message if not success else 'Access granted!'}")
    
    if success:
        print(f"   Session Token: {session_token}")
        
        # Test session validation
        print("\n3. Testing session validation:")
        is_valid = dashboard_manager.is_session_valid(session_token)
        print(f"   Session Valid: {'✅' if is_valid else '❌'}")
        
        # Test dashboard data access
        print("\n4. Testing dashboard data access:")
        dashboard_data, message = dashboard_manager.get_dashboard_data(session_token)
        
        if dashboard_data:
            print("   ✅ Dashboard data retrieved successfully")
            print(f"   Current Stats: {dashboard_data['current_stats']}")
            print(f"   Recent Logs: {len(dashboard_data['recent_logs'])} entries")
            print(f"   Today's Attendance: {len(dashboard_data['todays_attendance'])} records")
        else:
            print(f"   ❌ Failed to retrieve data: {message}")
        
        # Test data export
        print("\n5. Testing data export:")
        export_path, export_message = dashboard_manager.export_data(session_token)
        
        if export_path:
            print(f"   ✅ Data exported to: {export_path}")
        else:
            print(f"   ❌ Export failed: {export_message}")
    
    # Test invalid session
    print("\n6. Testing invalid session:")
    fake_token = "invalid_token_123"
    is_valid = dashboard_manager.is_session_valid(fake_token)
    print(f"   Invalid Session Check: {'✅' if not is_valid else '❌'}")
    
    print("\n" + "=" * 40)
    print("🎯 Dashboard Lock System Test Complete")

def test_system_logging():
    """Test system logging functionality"""
    print("\n📋 Testing System Logging")
    print("=" * 30)
    
    # Log some test events
    test_events = [
        ("student_registration", "TEST001", "Test student registered", None, "success"),
        ("face_attendance", "TEST001", "Attendance marked", 0.95, "success"),
        ("system_error", None, "Test error event", None, "error"),
        ("face_attendance", "TEST002", "Face not recognized", 0.2, "failed")
    ]
    
    for event_type, roll_no, description, confidence, status in test_events:
        dashboard_manager.log_system_event(event_type, roll_no, description, confidence, status)
        print(f"   ✅ Logged: {event_type} - {description}")
    
    print(f"\n   📊 {len(test_events)} events logged successfully")

def show_lock_file_status():
    """Show current lock file status"""
    print("\n🔍 Lock File Status")
    print("=" * 20)
    
    try:
        with open("attendance_db/dashboard_lock.json", 'r') as f:
            lock_data = json.load(f)
        
        print(f"   Access Attempts: {lock_data.get('access_attempts', 0)}")
        print(f"   Last Access: {lock_data.get('last_access', 'Never')}")
        print(f"   Locked Until: {lock_data.get('locked_until', 'Not locked')}")
        print(f"   Active Sessions: {len(lock_data.get('authorized_sessions', []))}")
        
    except Exception as e:
        print(f"   Error reading lock file: {e}")

def main():
    """Main test function"""
    print("🎓 Dashboard System Test Suite")
    print("=" * 50)
    
    # Show initial status
    show_lock_file_status()
    
    # Test logging
    test_system_logging()
    
    # Test lock system
    test_dashboard_lock()
    
    # Show final status
    show_lock_file_status()
    
    print("\n" + "=" * 50)
    print("✅ All Dashboard Tests Complete!")
    print("\n📋 How to Use Dashboard:")
    print("1. GUI is running with 3 modes now:")
    print("   📝 Registration Mode")
    print("   ✅ Attendance Mode") 
    print("   📊 Dashboard (Locked) - Requires 'SRINIVAS' password")
    print("\n2. Dashboard Features:")
    print("   - Real-time statistics and analytics")
    print("   - Today's attendance records")
    print("   - System logs and events")
    print("   - Weekly/Monthly reports")
    print("   - Data export functionality")
    print("   - Session-based security")
    print("\n🔒 Security Features:")
    print("   - Password protection with 'SRINIVAS'")
    print("   - Session tokens with 2-hour expiry")
    print("   - Failed attempt lockout (5 minutes after 3 failures)")
    print("   - Encrypted password storage")

if __name__ == "__main__":
    main()