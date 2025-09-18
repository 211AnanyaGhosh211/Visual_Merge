# PPE Detection & Face Recognition System - Complete Documentation

A comprehensive Personal Protective Equipment (PPE) detection and face recognition system built with Flask, YOLO, and FaceNet. This system monitors workplace safety by detecting PPE violations and identifying employees through face recognition.

## 📁 Project Structure

```
backend/
├── app.py                          # Main Flask application (renamed from newapp3.py)
├── requirements.txt                # Python dependencies
├── requirements2.txt              # Additional dependencies
├── test_image.jpg                 # Test image for development
├── test2.py                       # PPE violation logging script
│
├── services/                      # Service modules (organized)
│   ├── ppe_kit_detector.py        # Main PPE + Face detection service
│   ├── ppe_violation_detector.py  # Alternative PPE detection service
│   ├── model_visualizer.py        # YOLO detection visualization utilities
│   ├── analytics_api.py           # Analytics dashboard API endpoints
│   ├── live_cctv_processor.py     # Live CCTV/NVR feed processing
│   ├── ppe_server_launcher.py     # Main server launcher script
│   ├── auth.py                    # Authentication service
│   └── camera_config.py           # Camera configuration
│
├── db/                           # Database modules
│   ├── db.py                     # Centralized database configuration
│   └── Database.py               # Database API endpoints
│
├── data/                         # Data files
│   ├── users.csv                 # Registered employees data
│   ├── users_backup.csv          # Backup of users data
│   └── ppe_violations.csv        # PPE violations log
│
├── log/                          # Log files
│   ├── notifications.txt         # System notifications
│   ├── ppe_violations_log.txt    # PPE violations log
│   └── violation_report_*.txt    # Violation reports
│
├── media/                        # Media files
│   ├── faces/                    # Employee face images
│   │   ├── 007_Arghya/
│   │   ├── 10101_sumansamui/
│   │   └── ... (employee folders)
│   ├── face_detect/              # Face detection outputs
│   ├── uploads/                  # Uploaded videos/images
│   └── detections/               # Detection outputs
│
└── models/                       # AI model files
    ├── best700.pt               # Main YOLO model
    ├── best (3).pt              # Alternative YOLO model
    ├── current_400.pt           # Training checkpoint
    ├── epochs_500.pt            # Training checkpoint
    ├── Indorama_pvc_suit_best.pt # Specialized model
    ├── PPE_detection1.pt        # PPE detection model
    └── ppe.pt                   # General PPE model
```

## 🔄 Recent Changes & Refactoring

### File Organization & Renaming

#### 1. **Main Application**
- **`newapp3.py`** → **`app.py`** (cleaner, more standard naming)

#### 2. **Service Modules** (moved to `services/` directory)
- **`detect.py`** → **`ppe_kit_detector.py`** (main PPE + face detection)
- **`detect2.py`** → **`ppe_violation_detector.py`** (alternative PPE detection)
- **`img.py`** → **`model_visualizer.py`** (YOLO visualization utilities)
- **`dashdash.py`** → **`analytics_api.py`** (analytics dashboard API)
- **`cctvconn.py`** → **`live_cctv_processor.py`** (live CCTV processing)
- **`start_server.py`** → **`ppe_server_launcher.py`** (server launcher)

#### 3. **Database Modules** (moved to `db/` directory)
- **`db.py`** → **`db/db.py`** (centralized database config)
- **`Database.py`** → **`db/Database.py`** (database API endpoints)

#### 4. **Data Files** (moved to `data/` directory)
- **`users.csv`** → **`data/users.csv`** (employee data)
- **`ppe_violations.csv`** → **`data/ppe_violations.csv`** (violations data)

#### 5. **Media Files** (moved to `media/` directory)
- **`static/faces/`** → **`media/faces/`** (employee face images)
- **`static/uploads/`** → **`media/uploads/`** (uploaded files)
- **`face_detect/`** → **`media/face_detect/`** (face detection outputs)

#### 6. **Model Files** (moved to `models/` directory)
- All `.pt` model files moved to `models/` directory

#### 7. **Log Files** (moved to `log/` directory)
- **`log.txt`** → **`log/notifications.txt`** (system notifications)
- **`ppe_violations_log.txt`** → **`log/ppe_violations_log.txt`** (violations log)
- **`violation_report_*.txt`** → **`log/violation_report_*.txt`** (reports)

### Path Updates

All file paths in the codebase have been updated to reflect the new directory structure:

```python
# Before
users_file = 'users.csv'
model_path = 'best700.pt'
face_dir = 'static/faces/'

# After
users_file = 'data/users.csv'
model_path = 'models/best700.pt'
face_dir = 'media/faces/'
```

### Import Updates

All import statements have been updated to use the new module structure:

```python
# Before
import detect
from detect import detectFace
import dashdash
from dashdash import api as dashboard_api

# After
import services.ppe_kit_detector
from services.ppe_kit_detector import detectFace
import services.analytics_api
from services.analytics_api import api as dashboard_api
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- MySQL Database
- CUDA-compatible GPU (optional, for faster processing)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Visual_Merge/backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up database**
   - Create a MySQL database
   - Update database configuration in `db/db.py`
   - Run the database setup scripts

4. **Configure environment variables** (optional)
   Create a `.env` file in the backend directory:
   ```env
   DB_HOST=localhost
   DB_USER=root
   DB_PASS=your_password
   DB_NAME=EmployeeInfo
   ```

### Running the Application

1. **Start the main server**
   ```bash
   python app.py
   ```

2. **Or use the launcher script**
   ```bash
   python services/ppe_server_launcher.py
   ```

3. **For development with frontend**
   ```bash
   # From the eframe-app directory
   npm run start:all
   ```

## 🔧 Configuration

### Database Configuration

The database configuration is centralized in `db/db.py`:

```python
db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", "12345"),
    "database": os.getenv("DB_NAME", "EmployeeInfo")
}
```

### Model Configuration

- **Main YOLO Model**: `models/best700.pt`
- **Face Recognition**: FaceNet + MTCNN
- **Device**: Automatically detects CUDA availability

### File Paths

- **Employee Data**: `data/users.csv`
- **Face Images**: `media/faces/`
- **Uploads**: `media/uploads/`
- **Logs**: `log/`
- **Models**: `models/`

## 📊 API Endpoints

### Main Application (`app.py`)
- `GET /` - Dashboard
- `POST /capture_faces` - Face registration
- `GET /video_feed` - Live video feed
- `POST /detect` - PPE detection

### Analytics API (`services/analytics_api.py`)
- `GET /api/analytics/dashboard` - Dashboard data
- `GET /api/analytics/violations` - Violations data
- `GET /api/analytics/employees` - Employee data

### Database API (`db/Database.py`)
- `GET /api/db/employees` - Employee management
- `POST /api/db/employees` - Add employee
- `PUT /api/db/employees/<id>` - Update employee
- `DELETE /api/db/employees/<id>` - Delete employee

### Authentication (`services/auth.py`)
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `POST /auth/logout` - User logout

## 🎥 Camera Management

### Simple Camera Setup

The system supports multiple cameras with a simple configuration:

1. **Edit Camera Config**: `backend/services/camera_config.py`
2. **Add Your Cameras**: Define camera details in `CAMERA_CONFIG`
3. **Frontend Selection**: Users select from dropdown (0-10)
4. **Automatic Handling**: Backend uses the right camera automatically

### Camera Types Supported

#### **Laptop Camera (type: "laptop")**
```python
"0": {
    "name": "Laptop Camera", 
    "type": "laptop", 
    "url": None,
    "description": "Built-in laptop webcam"
}
```

#### **RTSP Camera (type: "rtsp")**
```python
"1": {
    "name": "Network Camera", 
    "type": "rtsp", 
    "url": "rtsp://username:password@ip:port/path",
    "description": "Network camera description"
}
```

#### **USB Camera (type: "usb")**
```python
"2": {
    "name": "USB Camera", 
    "type": "usb", 
    "url": None,
    "description": "USB connected camera"
}
```

### Camera API Usage

#### **Frontend sends:**
```javascript
{
    "camera_id": "5"  // Just the camera number
}
```

#### **Backend responds:**
```javascript
{
    "message": "Detection started using Storage Area",
    "stream_url": "/detection_feed",
    "camera_id": "5",
    "camera_name": "Storage Area",
    "camera_type": "rtsp"
}
```

## 🔐 Authentication System

### API Endpoints

#### **Login**
- **Endpoint**: `POST /api/login`
- **Description**: Authenticates users against MySQL database
- **Request**: `{"employeeId": "7", "password": "plaintext_password"}`
- **Response**: User details and login status

#### **Logout**
- **Endpoint**: `POST /api/logout`
- **Description**: Handles user logout
- **Response**: Logout confirmation

#### **Token Verification**
- **Endpoint**: `POST /api/verify-token`
- **Description**: Token verification for future JWT/session validation

### Security Features

1. **SHA2 Password Hashing**: All passwords hashed using SHA-256
2. **Input Validation**: Client-side and server-side validation
3. **SQL Injection Protection**: Parameterized queries
4. **Error Handling**: Comprehensive error responses

### Database Requirements

```sql
CREATE TABLE Registered_Employees (
    EmployeeName VARCHAR(255),
    EmployeeID VARCHAR(50) PRIMARY KEY,
    Images VARCHAR(255),
    Password VARCHAR(255)  -- SHA2 hashed passwords
);
```

## 📁 Media Paths Verification

### ✅ All Media Paths Correctly Configured

#### **1. Face Images (`media/faces/`)**
- ✅ **Code References**: All updated to `media/faces/`
- ✅ **Database**: Updated to use `media/faces/` paths
- ✅ **CSV Files**: Updated to use `media/faces/` paths
- ✅ **Directory Creation**: `os.makedirs('media/faces', exist_ok=True)`

#### **2. Face Detection Images (`media/face_detect/`)**
- ✅ **Output Images**: `media/face_detect/output.jpg`
- ✅ **Timestamped Images**: `media/face_detect/output{datetime}.jpg`
- ✅ **Face Detection Images**: `media/face_detect/face_detect_{datetime}.jpg`
- ✅ **Directory Creation**: `os.makedirs('media/face_detect', exist_ok=True)`

#### **3. Upload Files (`media/uploads/`)**
- ✅ **Upload Directory**: `UPLOAD_FOLDER = 'media/uploads'`
- ✅ **Directory Structure**: Properly configured

#### **4. Model Files (`models/`)**
- ✅ **YOLO Models**: `models/best700.pt`
- ✅ **Model References**: All updated to use `models/` directory

#### **5. Data Files (`data/`)**
- ✅ **CSV Files**: `data/users.csv`
- ✅ **Data References**: All updated to use `data/` directory

#### **6. Log Files (`log/`)**
- ✅ **Notification Logs**: `log/notifications.txt`
- ✅ **Violation Logs**: `log/ppe_violations_log.txt`
- ✅ **Report Files**: `log/violation_report_{date}.txt`

## 🛠️ Development

### Adding New Services

1. Create new service file in `services/` directory
2. Follow naming convention: `service_name.py`
3. Update imports in `app.py` if needed
4. Add to `services/` directory structure

### Adding New Models

1. Place model files in `models/` directory
2. Update model paths in service files
3. Update configuration if needed

### Database Changes

1. Update `db/db.py` for connection changes
2. Update `db/Database.py` for API changes
3. Update database schema as needed

## 📝 Logging

- **System Logs**: `log/notifications.txt`
- **Violations**: `log/ppe_violations_log.txt`
- **Reports**: `log/violation_report_*.txt`

## 🔒 Security

- Database credentials can be configured via environment variables
- Authentication system implemented in `services/auth.py`
- CORS enabled for frontend integration

## 🐛 Troubleshooting

### Common Issues

1. **Model not found**: Check if model files are in `models/` directory
2. **Database connection**: Verify database configuration in `db/db.py`
3. **Import errors**: Ensure all service modules are in `services/` directory
4. **File not found**: Check if file paths match new directory structure

### Camera API Troubleshooting

#### **"Error loading camera list" in Frontend**
- Check if backend is running on port 5000
- Test API directly: `curl http://127.0.0.1:5000/api/cameras`
- Check browser console for CORS errors
- Verify camera config syntax

#### **CORS Issues**
- Backend CORS configured for `http://127.0.0.1:5173`
- Ensure frontend runs on port 5173
- Check backend runs on port 5000

#### **Camera Config Issues**
- Test config: `python -c "from camera_config import CAMERA_CONFIG; print('Cameras:', len(CAMERA_CONFIG))"`
- Should show: `Cameras: 12`

### Debug Mode

Enable debug mode in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

## 📈 Performance

- **GPU Acceleration**: Automatically detects and uses CUDA if available
- **Threading**: Uses threading for concurrent processing
- **Caching**: Face embeddings are cached for faster recognition
- **Optimized Models**: Uses optimized YOLO models for detection

## 📋 Migration Guide

### File Mapping

| Old File | New File | New Location | Purpose |
|----------|----------|--------------|---------|
| `newapp3.py` | `app.py` | Root | Main application |
| `detect.py` | `ppe_kit_detector.py` | `services/` | Main PPE + face detection |
| `detect2.py` | `ppe_violation_detector.py` | `services/` | Alternative PPE detection |
| `img.py` | `model_visualizer.py` | `services/` | YOLO visualization utilities |
| `dashdash.py` | `analytics_api.py` | `services/` | Analytics dashboard API |
| `cctvconn.py` | `live_cctv_processor.py` | `services/` | Live CCTV processing |
| `start_server.py` | `ppe_server_launcher.py` | `services/` | Server launcher |
| `db.py` | `db.py` | `db/` | Database configuration |
| `Database.py` | `Database.py` | `db/` | Database API endpoints |
| `users.csv` | `users.csv` | `data/` | Employee data |
| `ppe_violations.csv` | `ppe_violations.csv` | `data/` | Violations data |

### Path Mapping

| Old Path | New Path | Purpose |
|----------|----------|---------|
| `static/faces/` | `media/faces/` | Employee face images |
| `static/uploads/` | `media/uploads/` | Uploaded files |
| `face_detect/` | `media/face_detect/` | Face detection outputs |
| `best700.pt` | `models/best700.pt` | Main YOLO model |
| `log.txt` | `log/notifications.txt` | System notifications |

### Code Changes Required

#### Import Statements
```python
# Before
import detect
from detect import detectFace
import dashdash
from dashdash import api as dashboard_api

# After
import services.ppe_kit_detector
from services.ppe_kit_detector import detectFace
import services.analytics_api
from services.analytics_api import api as dashboard_api
```

#### File Paths
```python
# Before
users_file = 'users.csv'
model_path = 'best700.pt'
face_dir = 'static/faces/'

# After
users_file = 'data/users.csv'
model_path = 'models/best700.pt'
face_dir = 'media/faces/'
```

## 🧪 Testing

### Verification Commands

```bash
# Test main app
python app.py

# Test imports
python -c "import services.ppe_kit_detector; import services.analytics_api; print('All imports working')"

# Test database
python -c "from db.db import get_db_connection; conn = get_db_connection(); print('DB OK')"

# Test file access
python -c "import pandas as pd; df = pd.read_csv('data/users.csv'); print('CSV OK')"

# Test camera config
python -c "from services.camera_config import CAMERA_CONFIG; print('Cameras:', len(CAMERA_CONFIG))"
```

## 📊 Changelog

### [2.0.0] - 2025-01-18

#### 🏗️ Major Refactoring & Organization

**Added:**
- Organized directory structure with dedicated folders
- Centralized database configuration in `db/db.py`
- Environment variable support for database configuration
- Comprehensive documentation
- Service-oriented architecture with modules in `services/` directory

**Changed:**
- File organization and module renaming for better clarity
- Path updates throughout the codebase
- Centralized database configuration
- Import path consistency

**Fixed:**
- Database configuration duplication
- Import path inconsistencies
- File path references
- Module naming confusion
- Directory structure organization

**Removed:**
- Duplicate files
- Hardcoded configurations
- Scattered file locations

## 🤝 Contributing

1. Follow the established directory structure
2. Use descriptive names for new modules
3. Update this documentation when adding new features
4. Test all changes before committing

## 📄 License

[Add your license information here]

---

**Last Updated**: January 2025  
**Version**: 2.0 (Refactored)  
**Maintainer**: [Your Name]

---

## 🎯 Quick Reference

### Essential Commands
```bash
# Start backend
python app.py

# Test camera API
curl http://127.0.0.1:5000/api/cameras

# Test authentication
python services/test_login_api.py

# Check media paths
python -c "import os; print('Media dirs exist:', all(os.path.exists(d) for d in ['media/faces', 'media/uploads', 'media/face_detect', 'models', 'data', 'log']))"
```

### Key Files
- **Main App**: `app.py`
- **Camera Config**: `services/camera_config.py`
- **Database Config**: `db/db.py`
- **Authentication**: `services/auth.py`
- **PPE Detection**: `services/ppe_kit_detector.py`

### Important URLs
- **Backend**: `http://127.0.0.1:5000`
- **Frontend**: `http://127.0.0.1:5173`
- **Camera API**: `http://127.0.0.1:5000/api/cameras`
- **Login API**: `http://127.0.0.1:5000/api/login`
