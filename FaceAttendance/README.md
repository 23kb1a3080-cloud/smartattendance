# Face Recognition Attendance System

A comprehensive face recognition attendance system for student management with liveness detection to prevent photo spoofing.

## Features

- ✅ Student registration with multi-angle face capture
- ✅ Face encoding and model training
- ✅ Real-time attendance verification
- ✅ Liveness detection (blink verification)
- ✅ SQLite database for attendance records
- ✅ GUI interface for easy operation
- ✅ Duplicate prevention (one attendance per student per day)

## Requirements

- Python 3.8+
- OpenCV
- face_recognition
- dlib
- numpy

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure you have a working webcam

## Usage

### Option 1: Using GUI (Recommended)
```bash
python gui.py
```

### Option 2: Command Line

#### Step 1: Register Student
```bash
python registration.py
```
- Enter roll number
- Capture 30 face images from different angles
- Images stored in `dataset/roll_number/`

#### Step 2: Train Model
```bash
python train_model.py
```
- Generates face encodings
- Saves to `encodings/encodings.pkl`

#### Step 3: Mark Attendance
```bash
python attendance.py
```
- Enter roll number
- Webcam opens
- Face verification with liveness detection
- Attendance marked if verified

## Project Structure

```
FaceAttendance/
├── dataset/              # Student face images
│   └── 22001/           # Roll number folder
│       ├── img1.jpg
│       └── ...
├── encodings/           # Face encodings
│   └── encodings.pkl
├── attendance_db/       # Attendance database
│   └── attendance.db
├── registration.py      # Student registration module
├── train_model.py       # Face encoding module
├── attendance.py        # Real-time recognition module
├── gui.py              # GUI interface
└── README.md
```

## Technical Details

### Face Recognition
- Uses `face_recognition` library (dlib-based)
- 128-dimensional face embeddings
- Distance-based matching (threshold: 0.45)

### Liveness Detection
- Eye blink detection
- Head movement verification
- Prevents photo/video spoofing

### Database
- SQLite for lightweight storage
- Prevents duplicate attendance
- Stores: roll_no, name, date, time, status, confidence

## Configuration

Edit the configuration at the top of each Python file:
- `MATCH_THRESHOLD`: Face matching threshold (lower = stricter)
- `NUM_IMAGES`: Number of images to capture per student
- `CAMERA_INDEX`: Webcam index (default: 0)

## Troubleshooting

### "No face detected"
- Ensure good lighting
- Position face in center of frame
- Remove glasses/hats

### "Not verified"
- Increase `MATCH_THRESHOLD` slightly
- Re-register with better quality images
- Ensure consistent lighting conditions

### Webcam not opening
- Check camera permissions
- Close other applications using the camera
- Try different `CAMERA_INDEX`

## License

MIT License - Feel free to modify and use for educational purposes.
