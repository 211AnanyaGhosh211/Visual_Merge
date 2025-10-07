# ----------------------
# Standard Library Imports
# ----------------------
import os
import logging

# ----------------------
# Third-Party Imports
# ----------------------
import torch
from flask import Flask
from flask_cors import CORS
from facenet_pytorch import InceptionResnetV1, MTCNN
from ultralytics import YOLO

# ----------------------
# Database Imports
# ----------------------
from db.db import db_util

# ----------------------
# Blueprint Imports
# ----------------------
from routes.main_dashboard import main_dashboard_bp
from routes.camera_dashboard import camera_dashboard_bp
from routes.auth import auth_bp
from routes.employee_configuration import employee_configuration_bp
from routes.model_management import model_management_bp
from routes.notification_management import notification_management_bp
from routes.camera_management import camera_management_bp

# Initialize logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)  # Initialize the Flask app

# Configure upload folder
UPLOAD_FOLDER = 'media/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure CORS with specific settings
CORS(app,
     # Allow frontend origins
     origins=["http://localhost:5173", "http://127.0.0.1:5173"],
     # Allow all necessary methods
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     # Allow necessary headers
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"], supports_credentials=True)  # Allow credentials


# Register dashboard API blueprint
app.register_blueprint(main_dashboard_bp)
# Register authentication API blueprint
app.register_blueprint(auth_bp)
# Register camera dashboard API blueprint
app.register_blueprint(camera_dashboard_bp)
# Register employee configuration API blueprint
app.register_blueprint(employee_configuration_bp)
# Register model management API blueprint
app.register_blueprint(model_management_bp)
# Register notification management API blueprint
app.register_blueprint(notification_management_bp)
# Register camera management API blueprint
app.register_blueprint(camera_management_bp)


# Ensure media/faces directory exists
os.makedirs('media/faces', exist_ok=True)


# ======================== MAIN ========================


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
