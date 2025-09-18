# Migration Guide: Old Structure → New Structure

This guide helps developers understand the changes made during the refactoring process.

## 🔄 File Mapping

### Main Application
| Old File | New File | Reason |
|----------|----------|---------|
| `newapp3.py` | `app.py` | Standard naming convention |

### Service Modules
| Old File | New File | New Location | Purpose |
|----------|----------|--------------|---------|
| `detect.py` | `ppe_kit_detector.py` | `services/` | Main PPE + face detection |
| `detect2.py` | `ppe_violation_detector.py` | `services/` | Alternative PPE detection |
| `img.py` | `model_visualizer.py` | `services/` | YOLO visualization utilities |
| `dashdash.py` | `analytics_api.py` | `services/` | Analytics dashboard API |
| `cctvconn.py` | `live_cctv_processor.py` | `services/` | Live CCTV processing |
| `start_server.py` | `ppe_server_launcher.py` | `services/` | Server launcher |
| `auth.py` | `auth.py` | `services/` | Authentication (moved) |

### Database Modules
| Old File | New File | New Location | Purpose |
|----------|----------|--------------|---------|
| `db.py` | `db.py` | `db/` | Database configuration |
| `Database.py` | `Database.py` | `db/` | Database API endpoints |

### Data Files
| Old File | New File | New Location | Purpose |
|----------|----------|--------------|---------|
| `users.csv` | `users.csv` | `data/` | Employee data |
| `ppe_violations.csv` | `ppe_violations.csv` | `data/` | Violations data |

### Media Files
| Old Path | New Path | Purpose |
|----------|----------|---------|
| `static/faces/` | `media/faces/` | Employee face images |
| `static/uploads/` | `media/uploads/` | Uploaded files |
| `face_detect/` | `media/face_detect/` | Face detection outputs |

### Model Files
| Old Location | New Location | Purpose |
|--------------|--------------|---------|
| Root directory | `models/` | All `.pt` model files |

### Log Files
| Old File | New File | New Location | Purpose |
|----------|----------|--------------|---------|
| `log.txt` | `notifications.txt` | `log/` | System notifications |
| `ppe_violations_log.txt` | `ppe_violations_log.txt` | `log/` | Violations log |
| `violation_report_*.txt` | `violation_report_*.txt` | `log/` | Violation reports |

## 🔧 Code Changes Required

### Import Statements

#### Before (Old Structure)
```python
# Main app imports
import detect
from detect import detectFace
import dashdash
from dashdash import api as dashboard_api
import auth
from auth import auth_bp

# Database imports
from db import db_config
import Database
from Database import database_bp
```

#### After (New Structure)
```python
# Main app imports
import services.ppe_kit_detector
from services.ppe_kit_detector import detectFace
import services.analytics_api
from services.analytics_api import api as dashboard_api
import services.auth
from services.auth import auth_bp

# Database imports
from db.db import db_config
import db.Database
from db.Database import database_bp
```

### File Paths

#### Before (Old Structure)
```python
# File paths
users_file = 'users.csv'
model_path = 'best700.pt'
face_dir = 'static/faces/'
upload_dir = 'static/uploads/'
log_file = 'log.txt'
violations_log = 'ppe_violations_log.txt'
```

#### After (New Structure)
```python
# File paths
users_file = 'data/users.csv'
model_path = 'models/best700.pt'
face_dir = 'media/faces/'
upload_dir = 'media/uploads/'
log_file = 'log/notifications.txt'
violations_log = 'log/ppe_violations_log.txt'
```

### Database Configuration

#### Before (Old Structure)
```python
# Hardcoded in multiple files
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "12345",
    "database": "EmployeeInfo"
}
```

#### After (New Structure)
```python
# Centralized in db/db.py
from db.db import db_config

# Or with environment variables
db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", "12345"),
    "database": os.getenv("DB_NAME", "EmployeeInfo")
}
```

## 🚀 Migration Steps

### 1. Update Import Statements
Search and replace all import statements in your code:

```bash
# Find all files with old imports
grep -r "import detect" .
grep -r "import dashdash" .
grep -r "import auth" .

# Update to new imports
# detect → services.ppe_kit_detector
# dashdash → services.analytics_api
# auth → services.auth
```

### 2. Update File Paths
Search and replace all file paths:

```bash
# Find all files with old paths
grep -r "users.csv" .
grep -r "static/faces" .
grep -r "best700.pt" .

# Update to new paths
# users.csv → data/users.csv
# static/faces → media/faces
# best700.pt → models/best700.pt
```

### 3. Update Database References
Update all database connection references:

```bash
# Find hardcoded database configs
grep -r "mysql.connector.connect" .

# Replace with centralized config
# from db.db import db_config
```

### 4. Test the Application
After making changes, test the application:

```bash
# Test imports
python -c "from app import app; print('Import successful')"

# Test database connection
python -c "from db.db import get_db_connection; conn = get_db_connection(); print('DB connected')"

# Test service modules
python -c "import services.ppe_kit_detector; print('Services working')"
```

## ⚠️ Common Issues & Solutions

### Issue 1: ModuleNotFoundError
**Error**: `ModuleNotFoundError: No module named 'detect'`

**Solution**: Update import statements to use new module names:
```python
# Old
import detect

# New
import services.ppe_kit_detector
```

### Issue 2: FileNotFoundError
**Error**: `FileNotFoundError: [Errno 2] No such file or directory: 'users.csv'`

**Solution**: Update file paths to new directory structure:
```python
# Old
users_file = 'users.csv'

# New
users_file = 'data/users.csv'
```

### Issue 3: Database Connection Error
**Error**: Database connection fails

**Solution**: Use centralized database configuration:
```python
# Old
conn = mysql.connector.connect(host="localhost", user="root", ...)

# New
from db.db import get_db_connection
conn = get_db_connection()
```

### Issue 4: Model Not Found
**Error**: `FileNotFoundError: [Errno 2] No such file or directory: 'best700.pt'`

**Solution**: Update model paths:
```python
# Old
model = YOLO("best700.pt")

# New
model = YOLO("models/best700.pt")
```

## 📋 Checklist

- [ ] Update all import statements
- [ ] Update all file paths
- [ ] Update database configuration references
- [ ] Test all imports work correctly
- [ ] Test database connection
- [ ] Test file access (CSV, models, images)
- [ ] Test service modules
- [ ] Update documentation
- [ ] Test end-to-end functionality

## 🔍 Verification Commands

```bash
# Test main app
python app.py

# Test imports
python -c "import services.ppe_kit_detector; import services.analytics_api; print('All imports working')"

# Test database
python -c "from db.db import get_db_connection; conn = get_db_connection(); print('DB OK')"

# Test file access
python -c "import pandas as pd; df = pd.read_csv('data/users.csv'); print('CSV OK')"
```

---

**Note**: This migration guide assumes you're working with the refactored codebase. If you're starting fresh, refer to the main README.md for setup instructions.
