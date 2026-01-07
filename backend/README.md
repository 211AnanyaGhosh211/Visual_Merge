# PPE Detection & Face Recognition System - Complete Documentation

A comprehensive Personal Protective Equipment (PPE) detection and face recognition system built with Flask, YOLO, and FaceNet. This system monitors workplace safety by detecting PPE violations and identifying employees through face recognition.

## 📁 Project Structure

```
backend/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── README.md                      # Project documentation
│
├── services/                      # Service modules (organized)
│   ├── camera_config.py           # Camera configuration
│   ├── live_cctv_processor.py     # Live CCTV/NVR feed processing
│   ├── model_visualizer.py        # YOLO detection visualization utilities
│   ├── ppe_kit_detector.py        # Main PPE + Face detection service
│   ├── ppe_server_launcher.py     # Main server launcher script
│   ├── ppe_violation_detector.py  # Alternative PPE detection service
│   └── violation_count.py        # Violation counting utilities
│
├── routes/                        # API route modules (organized)
│   ├── auth.py                   # Authentication API routes
│   ├── camera_dashboard.py       # Camera dashboard API routes
│   ├── camera_management.py      # Camera management API routes
│   ├── employee_configuration.py # Employee management API routes
│   ├── main_dashboard.py         # Main dashboard API routes
│   ├── model_management.py       # Model management API routes
│   ├── model_mapping.py          # Model mapping API routes
│   └── notification_management.py # Notification API routes
│
├── db/                           # Database modules
│   └── db.py                     # Centralized database configuration and utilities
│
├── data/                         # Data files
│   ├── ppe_violations.csv        # PPE violations log
│   ├── users_backup.csv          # Backup of users data
│   └── users.csv                 # Registered employees data
│
├── log/                          # Log files
│   ├── notifications.txt         # System notifications
│   ├── ppe_violations_log.txt    # PPE violations log
│   ├── time_based_detection_log.json # Time-based detection logs
│   ├── time_based_summary.txt    # Time-based detection summary
│   └── violation_report_2025-06-11.txt # Violation reports
│
├── media/                        # Media files
│   ├── face_detect/              # Face detection outputs
│   ├── faces/                    # Employee face images
│   │   ├── 10101_sumansamui/
│   │   ├── 234_xxyx/
│   │   ├── 7_Avijit/
│   │   ├── E156_James Rodrigues/
│   │   ├── E189_john cena/
│   │   └── E234_john cena/
│   └── uploads/                  # Uploaded videos/images
│       ├── cropped.mp4
│       ├── forklift_speed_output.mp4
│       ├── Mill_A_Unit_1_Boiler_NVR_*.mp4
│       ├── Mill_A_Unit_2_Boiler_NVR_*.mp4
│       ├── Mill_B_Unit_1_Boiler_NVR_*.mp4
│       ├── speed_estimation.avi
│       ├── TATA.mp4
│       └── vecteezy_car-and-truck-traffic_*.mp4
│
├── models/                       # AI model files
│   ├── aparava_300_epoch.pt      # Training checkpoint
│   ├── apraava(100epochs).pt     # Training checkpoint
│   ├── best (3).pt               # Alternative YOLO model
│   ├── best700.pt                # Main YOLO model
│   ├── current_400.pt            # Training checkpoint
│   ├── epochs_500.pt             # Training checkpoint
│   ├── Indorama_pvc_suit_best.pt # Specialized model
│   ├── PPE_detection1.pt         # PPE detection model
│   └── ppe.pt                    # General PPE model
│
├── test_purposes/                # Testing and development files
│   ├── cctvconn2.py             # CCTV connection testing
│   ├── cpu_or_gpu_testing.py    # Hardware testing utilities
│   ├── test_imports.py          # Import testing
│   ├── test.py                  # General testing
│   └── test2.py                 # Additional testing
│
└── venv/                        # Python virtual environment
    ├── Include/
    ├── Lib/
    ├── Scripts/
    └── share/
```

## 🔄 Recent Changes & Refactoring

### File Organization & Renaming

#### 1. **Main Application**
- **`newapp3.py`** → **`app.py`** (cleaner, more standard naming)

#### 2. **Service Modules** (organized in `services/` directory)
- **`camera_config.py`** - Camera configuration management
- **`live_cctv_processor.py`** - Live CCTV/NVR feed processing
- **`model_visualizer.py`** - YOLO detection visualization utilities
- **`ppe_kit_detector.py`** - Main PPE + face detection service
- **`ppe_server_launcher.py`** - Main server launcher script
- **`ppe_violation_detector.py`** - Alternative PPE detection service
- **`violation_count.py`** - Violation counting utilities

#### 3. **Database Modules** (consolidated in `db/` directory)
- **`db.py`** → **`db/db.py`** (centralized database config and utilities)
- **`Database.py`** → **MERGED into `db/db.py`** (database utilities consolidated)

#### 4. **Data Files** (organized in `data/` directory)
- **`ppe_violations.csv`** - PPE violations log
- **`users_backup.csv`** - Backup of users data
- **`users.csv`** - Registered employees data

#### 5. **Media Files** (moved to `media/` directory)
- **`static/faces/`** → **`media/faces/`** (employee face images)
- **`static/uploads/`** → **`media/uploads/`** (uploaded files)
- **`face_detect/`** → **`media/face_detect/`** (face detection outputs)

#### 6. **Model Files** (organized in `models/` directory)
- **`aparava_300_epoch.pt`** - Training checkpoint
- **`apraava(100epochs).pt`** - Training checkpoint
- **`best (3).pt`** - Alternative YOLO model
- **`best700.pt`** - Main YOLO model
- **`current_400.pt`** - Training checkpoint
- **`epochs_500.pt`** - Training checkpoint
- **`Indorama_pvc_suit_best.pt`** - Specialized model
- **`PPE_detection1.pt`** - PPE detection model
- **`ppe.pt`** - General PPE model

#### 7. **Log Files** (organized in `log/` directory)
- **`notifications.txt`** - System notifications
- **`ppe_violations_log.txt`** - PPE violations log
- **`time_based_detection_log.json`** - Time-based detection logs
- **`time_based_summary.txt`** - Time-based detection summary
- **`violation_report_2025-06-11.txt`** - Violation reports

#### 8. **Testing Files** (organized in `test_purposes/` directory)
- **`cctvconn2.py`** - CCTV connection testing
- **`cpu_or_gpu_testing.py`** - Hardware testing utilities
- **`test_imports.py`** - Import testing
- **`test.py`** - General testing
- **`test2.py`** - Additional testing

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
# Current import structure in app.py
from db.db import db_util
from routes.auth import auth_bp
from routes.camera_dashboard import camera_dashboard_bp
from routes.camera_management import camera_management_bp
from routes.employee_configuration import employee_configuration_bp
from routes.main_dashboard import main_dashboard_bp
from routes.model_management import model_management_bp
from routes.model_mapping import model_mapping_bp
from routes.notification_management import notification_management_bp

# Service imports
from services.ppe_kit_detector import detectFace
from services.live_cctv_processor import process_cctv_feed
from services.model_visualizer import visualize_detections
from services.violation_count import count_violations
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
# Database configuration with environment variable support
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "database": os.getenv("DB_NAME")
}

# Database utility class for connection management
class DBUtil:
    def __init__(self):
        self.conn = mysql.connector.connect(**db_config)
        self.cursor = self.conn.cursor()

# Global database utility instance
db_util = DBUtil()
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

### Main Dashboard API (`routes/main_dashboard.py`)
- `GET /api/dashboard` - Main dashboard data
- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/dashboard/violations` - Recent violations

### Route APIs (organized by functionality)

#### **Camera Dashboard** (`routes/camera_dashboard.py`)
- `GET /api/camera_dashboard` - Camera dashboard data
- `GET /api/camera_dashboard/feed` - Live camera feed
- `POST /api/camera_dashboard/start_detection` - Start detection

#### **Camera Management** (`routes/camera_management.py`)
- `GET /api/camera_management/cameras` - Get all cameras
- `GET /api/camera_management/get_camera` - Get single camera by ID
- `POST /api/camera_management/set_camera` - Create new camera
- `DELETE /api/camera_management/del_camera` - Delete camera

#### **Employee Configuration** (`routes/employee_configuration.py`)
- `GET /api/employee_configuration/employees` - Get all employees
- `POST /api/employee_configuration/employees` - Add employee
- `PUT /api/employee_configuration/employees/<id>` - Update employee
- `DELETE /api/employee_configuration/employees/<id>` - Delete employee

#### **Model Management** (`routes/model_management.py`)
- `GET /api/model_management/models` - Get all models
- `POST /api/model_management/models` - Create new model
- `DELETE /api/model_management/models/<id>` - Delete model

#### **Model Mapping** (`routes/model_mapping.py`)
- `GET /api/model_mapping/get_camera` - Get camera for mapping
- `GET /api/model_mapping/get_model` - Get model for mapping
- `POST /api/model_mapping/set_model` - Create model
- `DELETE /api/model_mapping/del_model` - Delete model
- `POST /api/model_mapping/link_camera_model` - Link camera with model

#### **Notification Management** (`routes/notification_management.py`)
- `GET /api/notifications` - Get all notifications
- `POST /api/notifications` - Create notification
- `PUT /api/notifications/<id>` - Update notification
- `DELETE /api/notifications/<id>` - Delete notification

#### **Authentication** (`routes/auth.py`)
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/verify-token` - Token verification


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

### Current File Structure

| File | Location | Purpose |
|------|----------|---------|
| `app.py` | Root | Main Flask application |
| `camera_config.py` | `services/` | Camera configuration management |
| `live_cctv_processor.py` | `services/` | Live CCTV/NVR feed processing |
| `model_visualizer.py` | `services/` | YOLO visualization utilities |
| `ppe_kit_detector.py` | `services/` | Main PPE + face detection |
| `ppe_server_launcher.py` | `services/` | Server launcher |
| `ppe_violation_detector.py` | `services/` | Alternative PPE detection |
| `violation_count.py` | `services/` | Violation counting utilities |
| `auth.py` | `routes/` | Authentication API routes |
| `camera_dashboard.py` | `routes/` | Camera dashboard API routes |
| `camera_management.py` | `routes/` | Camera management API routes |
| `employee_configuration.py` | `routes/` | Employee management API routes |
| `main_dashboard.py` | `routes/` | Main dashboard API routes |
| `model_management.py` | `routes/` | Model management API routes |
| `model_mapping.py` | `routes/` | Model mapping API routes |
| `notification_management.py` | `routes/` | Notification API routes |
| `db.py` | `db/` | Database configuration and utilities |
| `users.csv` | `data/` | Employee data |
| `ppe_violations.csv` | `data/` | Violations data |

### Path Mapping

| Old Path | New Path | Purpose |
|----------|----------|---------|
| `static/faces/` | `media/faces/` | Employee face images |
| `static/uploads/` | `media/uploads/` | Uploaded files |
| `face_detect/` | `media/face_detect/` | Face detection outputs |
| `best700.pt` | `models/best700.pt` | Main YOLO model |
| `log.txt` | `log/notifications.txt` | System notifications |

### Code Changes Required

#### Current Import Structure
```python
# Main application imports (app.py)
from db.db import db_util
from routes.auth import auth_bp
from routes.camera_dashboard import camera_dashboard_bp
from routes.camera_management import camera_management_bp
from routes.employee_configuration import employee_configuration_bp
from routes.main_dashboard import main_dashboard_bp
from routes.model_management import model_management_bp
from routes.model_mapping import model_mapping_bp
from routes.notification_management import notification_management_bp

# Service imports
from services.ppe_kit_detector import detectFace
from services.live_cctv_processor import process_cctv_feed
from services.model_visualizer import visualize_detections
from services.violation_count import count_violations
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

### Test Purposes Directory

The `test_purposes/` directory contains various testing and development utilities:

- **`cctvconn2.py`** - CCTV connection testing and validation
- **`cpu_or_gpu_testing.py`** - Hardware capability testing (CPU vs GPU)
- **`test_imports.py`** - Import testing for all modules
- **`test.py`** - General testing utilities
- **`test2.py`** - Additional testing scripts

### Verification Commands

```bash
# Test main app
python app.py

# Test imports
python -c "import services.ppe_kit_detector; import services.live_cctv_processor; print('All imports working')"

# Test database
python -c "from db.db import db_util; print('DB OK')"

# Test file access
python -c "import pandas as pd; df = pd.read_csv('data/users.csv'); print('CSV OK')"

# Test camera config
python -c "from services.camera_config import CAMERA_CONFIG; print('Cameras:', len(CAMERA_CONFIG))"

# Test route imports
python -c "from routes.auth import auth_bp; from routes.camera_management import camera_management_bp; print('Routes OK')"

# Test hardware capabilities
python test_purposes/cpu_or_gpu_testing.py

# Test imports
python test_purposes/test_imports.py
```

## 📊 Changelog

### [2.2.0] - 2025-01-18

#### 📚 Documentation Update

**Updated:**
- Project structure section to reflect actual directory layout
- Service modules documentation with current files
- Route modules documentation with current API endpoints
- Model files documentation with actual model files
- Import examples to match current structure
- Testing section with test_purposes directory
- Key files section with current important files
- Verification commands to match current structure

**Added:**
- Test purposes directory documentation
- Current file structure mapping
- Updated import structure examples
- Enhanced testing verification commands

### [2.1.0] - 2025-01-18

#### 🏗️ Database Consolidation & Route Organization

**Added:**
- Organized route modules in `routes/` directory
- Centralized database utilities in `db/db.py`
- Camera management API endpoints
- Model mapping API endpoints
- Employee configuration API endpoints
- Notification management API endpoints

**Changed:**
- Database.py merged into db/db.py for better organization
- API routes organized by functionality
- Import paths updated to use absolute imports
- Database connection management centralized

**Fixed:**
- Relative import issues in route files
- Database connection management
- API endpoint organization
- Import path consistency across modules

**Removed:**
- Duplicate Database.py file
- Relative imports causing runtime errors
- Scattered database configuration

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
- **Database Config**: `db/db.py`
- **Camera Management**: `routes/camera_management.py`
- **Camera Dashboard**: `routes/camera_dashboard.py`
- **Model Mapping**: `routes/model_mapping.py`
- **Employee Config**: `routes/employee_configuration.py`
- **Authentication**: `routes/auth.py`
- **PPE Detection**: `services/ppe_kit_detector.py`
- **Live CCTV Processing**: `services/live_cctv_processor.py`
- **Violation Counting**: `services/violation_count.py`
- **Camera Configuration**: `services/camera_config.py`

### Important URLs
- **Backend**: `http://127.0.0.1:5000`
- **Frontend**: `http://127.0.0.1:5173`
- **Camera Management API**: `http://127.0.0.1:5000/api/camera_management/cameras`
- **Model Mapping API**: `http://127.0.0.1:5000/api/model_mapping/`
- **Employee Config API**: `http://127.0.0.1:5000/api/employee_configuration/`
- **Authentication API**: `http://127.0.0.1:5000/api/auth/login`
