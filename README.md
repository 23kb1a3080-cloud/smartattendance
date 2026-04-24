# 🎓 Smart Face Attendance System

A comprehensive face recognition-based attendance system built with Python, OpenCV, and CustomTkinter. This system provides secure student registration, real-time face verification, and a powerful dashboard for attendance management.

## 🌟 Features

### Core Functionality
- **Student Registration**: Capture multiple face images for accurate recognition
- **Face Recognition**: Real-time face verification using advanced algorithms
- **Attendance Tracking**: Automatic attendance marking with timestamp
- **Duplicate Prevention**: One attendance per student per day
- **Dashboard System**: Secure data visualization and management

### Advanced Features
- **Professional Dark Theme**: Modern UI with custom color scheme
- **Password Protection**: Dashboard secured with "SRINIVAS" password
- **Real-time Detection**: Live face detection with confidence scoring
- **Data Export**: Export attendance data to JSON format
- **System Logs**: Comprehensive logging of all system activities
- **Reports Generation**: Weekly and monthly attendance reports

## 🚀 Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### Required Libraries
- OpenCV (`cv2`)
- CustomTkinter (`customtkinter`)
- face_recognition (optional, falls back to OpenCV)
- PIL (Pillow)
- SQLite3 (built-in)
- NumPy

### Installation
1. Clone the repository:
```bash
git clone https://github.com/23kb1a3080-cloud/smartattendance.git
cd smartattendance
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
cd FaceAttendance
python student_face_attendance.py
```

## 📁 Project Structure

```
smartattendance/
├── FaceAttendance/                 # Main application directory
│   ├── student_face_attendance.py # Main application file
│   ├── dashboard_system.py        # Dashboard management system
│   ├── attendance_db/              # Database storage
│   ├── dataset/                    # Student face images
│   └── encodings/                  # Face encoding data
├── dataset/                        # Sample student data
│   ├── 11111/                     # Student roll number folders
│   ├── 3000/
│   ├── 3011/
│   ├── 3080/
│   └── TEST123/
├── attendance_db/                  # Database files
└── requirements.txt               # Python dependencies
```

## 🎯 How to Use

### 1. Student Registration
1. Select "📝 Student Registration" mode
2. Enter student details (Roll Number, Name, Department)
3. Click "📸 Start Registration"
4. Position face in camera frame (20 images will be captured automatically)
5. Wait for registration completion

### 2. Face Attendance
1. Select "✅ Face Attendance" mode
2. Enter your roll number
3. Click "🔍 Verify Face & Mark Attendance"
4. Position face in camera frame for verification
5. Wait for attendance confirmation

### 3. Dashboard Access
1. Click "📊 Dashboard (Locked)" button
2. Enter password: **SRINIVAS**
3. Explore different tabs:
   - **📈 Overview**: System statistics and trends
   - **👥 Detected Students**: Real-time detection records
   - **✅ Today's Attendance**: Current day attendance
   - **📋 System Logs**: System activity logs
   - **📊 Reports**: Generate detailed reports
   - **💾 Export Data**: Export system data
4. Use "🏠 Back to Home" button to return to main interface

## 🔧 Technical Details

### Face Recognition System
- **Primary**: face_recognition library with dlib backend
- **Fallback**: OpenCV Haar Cascades with template matching
- **Accuracy**: Confidence-based matching with adjustable thresholds
- **Performance**: Real-time processing at ~30 FPS

### Database Schema
```sql
-- Students table
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    department TEXT,
    registered_date TEXT NOT NULL,
    face_encoded INTEGER DEFAULT 0
);

-- Attendance table
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no TEXT NOT NULL,
    name TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    status TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    verification_method TEXT DEFAULT 'face_recognition',
    UNIQUE(roll_no, date)
);

-- Detected students table (Dashboard)
CREATE TABLE detected_students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no TEXT NOT NULL,
    name TEXT NOT NULL,
    confidence REAL NOT NULL,
    detection_time TEXT NOT NULL,
    date TEXT NOT NULL,
    status TEXT DEFAULT 'detected',
    UNIQUE(roll_no, date)
);
```

### Security Features
- **Password Protection**: Dashboard access requires "SRINIVAS" password
- **Session Management**: Secure session tokens with expiration
- **Access Logging**: All access attempts are logged
- **Data Integrity**: Database constraints prevent duplicate entries

## 🎨 UI Features

### Color Scheme
- **Background**: Dark theme (#0d1117)
- **Primary**: Professional blue (#1f538d)
- **Success**: Green tones for positive actions
- **Warning**: Orange for attention items
- **Danger**: Red for errors and critical actions
- **Accent**: Bright blue (#58a6ff) for highlights

### User Experience
- **Responsive Design**: Adapts to different screen sizes
- **Real-time Feedback**: Live status updates and progress indicators
- **Professional Icons**: Emoji-based icons for better visual appeal
- **Smooth Animations**: CustomTkinter animations and transitions

## 📊 System Capabilities

### Performance Metrics
- **Registration**: 20 face images captured in ~10 seconds
- **Recognition**: Real-time face verification in <1 second
- **Database**: SQLite for fast, reliable data storage
- **Scalability**: Supports hundreds of students efficiently

### Duplicate Prevention
- **Database Level**: UNIQUE constraints prevent duplicate entries
- **Application Level**: Real-time duplicate detection
- **User Feedback**: Clear messages for duplicate attempts
- **Data Integrity**: Maintains clean, accurate records

## 🔍 Testing

Run the test suite to verify system functionality:
```bash
cd FaceAttendance
python test_back_button_and_duplicates.py
```

### Test Coverage
- ✅ Duplicate detection prevention
- ✅ Database structure integrity
- ✅ Face recognition accuracy
- ✅ UI functionality
- ✅ Data persistence

## 🛠️ Development

### System Requirements
- **Python**: 3.7 or higher
- **Camera**: USB webcam or built-in camera
- **OS**: Windows, macOS, or Linux
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 1GB for application and data

### Development Setup
1. Fork the repository
2. Create a virtual environment
3. Install development dependencies
4. Make your changes
5. Run tests
6. Submit a pull request

## 📝 Configuration

### Camera Settings
- **Resolution**: 640x480 (configurable)
- **FPS**: 30 (configurable)
- **Format**: BGR color space

### Recognition Thresholds
- **face_recognition**: 0.5 (adjustable)
- **OpenCV fallback**: 0.3 (adjustable)
- **Verification frames**: 30 frames (~1 second)

## 🚨 Troubleshooting

### Common Issues
1. **Camera not opening**: Check camera permissions and connections
2. **Face not detected**: Ensure good lighting and clear face visibility
3. **Recognition fails**: Re-register with better quality images
4. **Dashboard access denied**: Use correct password "SRINIVAS"

### Error Handling
- Comprehensive error logging
- User-friendly error messages
- Graceful fallback mechanisms
- Recovery procedures

## 🤝 Contributing

We welcome contributions! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- **Developer**: Smart Attendance System Team
- **Institution**: Educational Technology Project
- **Contact**: [GitHub Repository](https://github.com/23kb1a3080-cloud/smartattendance)

## 🙏 Acknowledgments

- OpenCV community for computer vision tools
- face_recognition library by Adam Geitgey
- CustomTkinter for modern GUI components
- Python community for excellent libraries

## 📈 Future Enhancements

- [ ] Mobile app integration
- [ ] Cloud database support
- [ ] Multi-camera support
- [ ] Advanced analytics
- [ ] API endpoints
- [ ] Web dashboard
- [ ] Biometric integration
- [ ] AI-powered insights

---

**Made with ❤️ for educational institutions worldwide**