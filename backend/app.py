from threading import Thread
import os
from turtle import color
from ultralytics import YOLO
import cv2
import cvzone
import math
import pandas as pd
import torch
# from deep_sort_realtime.deepsort_tracker import DeepSort
import json
from facenet_pytorch import InceptionResnetV1, MTCNN
from PIL import Image
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, jsonify, send_file, Response, jsonify, request
from flask_cors import CORS
import services.ppe_kit_detector
from services.ppe_kit_detector import detectFace
import db.Database
from db.Database import database_bp
from db.Database import db_util
import services.auth
from services.auth import auth_bp
import sys
import threading
import cv2
import torch
import logging
import mysql.connector
import pandas as pd
import subprocess
import psutil
from werkzeug.utils import secure_filename
import time
import multiprocessing as mp
from datetime import timedelta
import base64
from collections import namedtuple

# Import analytics_api.py functionality
import services.analytics_api
from services.analytics_api import api as dashboard_api

# Initialize logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)  # Initialize the Flask app

# Configure CORS with specific settings
CORS(app,
     # Allow frontend origins
     origins=["http://localhost:5173", "http://127.0.0.1:5173"],
     # Allow all necessary methods
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     # Allow necessary headers
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)  # Allow credentials
app.register_blueprint(database_bp, url_prefix='/api')
# Register dashboard API blueprint
app.register_blueprint(dashboard_api, url_prefix='/api')
# Register authentication API blueprint
app.register_blueprint(auth_bp, url_prefix='/api')


# MySQL Connection Configuration (as a dictionary)
# Import database configuration from db.py
from db.db import db_config

def get_db_connection():
    """Function to get a database connection."""
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as err:
        logging.error(f"Database connection error: {err}")
        return None


device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = InceptionResnetV1(pretrained='vggface2').eval().to(device)
mtcnn = MTCNN(keep_all=False, device=device)
# yolo_model = YOLO("model/ppe.pt")
yolo_model = YOLO("models/best700.pt")


# Ensure media/faces directory exists
os.makedirs('media/faces', exist_ok=True)

# CSV file to store registered users
users_file = 'data/users.csv'
if not os.path.exists(users_file):
    pd.DataFrame(columns=['Name', 'Roll No', 'Image Path']
                 ).to_csv(users_file, index=False)

# Global variables for face capture streaming
face_capture_running = False
face_capture_count = 0
face_capture_target = 20
face_capture_user_dir = None
face_capture_cap = None


def generate_face_capture_frames():
    """Generator function that yields frames during face capture with face detection overlay"""
    global face_capture_running, face_capture_count, face_capture_target, face_capture_cap

    if not face_capture_cap or not face_capture_cap.isOpened():
        return

    try:
        while face_capture_running and face_capture_count < face_capture_target:
            ret, frame = face_capture_cap.read()
            if not ret:
                break

            # Create a copy for display
            display_frame = frame.copy()

            # Detect faces
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces, *_ = mtcnn.detect(rgb_frame)

            if faces is not None:
                for box in faces:
                    x1, y1, x2, y2 = map(int, box)
                    if x1 < 0 or y1 < 0 or x2 > frame.shape[1] or y2 > frame.shape[0]:
                        continue

                    # Draw face detection box
                    cv2.rectangle(display_frame, (x1, y1),
                                  (x2, y2), (0, 255, 0), 2)

                    # Add text showing capture progress
                    progress_text = f"Captured: {face_capture_count}/{face_capture_target}"
                    cv2.putText(display_frame, progress_text, (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                    # Add instruction text
                    instruction_text = "Position your face in the green box"
                    cv2.putText(display_frame, instruction_text, (10, 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                    # Capture face if conditions are met
                    face = frame[y1:y2, x1:x2]
                    if face.size > 0 and face_capture_count < face_capture_target:
                        # Add a small delay to avoid capturing too quickly
                        time.sleep(0.5)

                        if face_capture_user_dir:
                            face_path = os.path.join(
                                face_capture_user_dir, f"face_{face_capture_count}.jpg")
                        cv2.imwrite(face_path, face)
                        face_capture_count += 1

                        # Show capture feedback
                        cv2.rectangle(display_frame, (x1, y1),
                                      (x2, y2), (0, 255, 255), 3)
                        cv2.putText(display_frame, f"Captured! ({face_capture_count}/{face_capture_target})",
                                    (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                        break

            # Resize for better performance
            display_frame = cv2.resize(display_frame, (640, 480))

            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', display_frame, [
                                     int(cv2.IMWRITE_JPEG_QUALITY), 80])
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    except Exception as e:
        logging.error(f"Face capture streaming error: {e}")
    finally:
        if face_capture_cap:
            face_capture_cap.release()


def start_face_capture(employee_id, employee_name):
    """Start face capture process with streaming"""
    global face_capture_running, face_capture_count, face_capture_target, face_capture_user_dir, face_capture_cap

    # Reset capture state
    face_capture_count = 0
    face_capture_target = 20
    face_capture_user_dir = f'media/faces/{employee_id}_{employee_name.strip()}'
    os.makedirs(face_capture_user_dir, exist_ok=True)
    # Initialize camera
    face_capture_cap = cv2.VideoCapture(0)
    if not face_capture_cap.isOpened():
        return False, "Error: Unable to access the camera."

    face_capture_running = True
    return True, "Face capture started successfully"


def stop_face_capture():
    """Stop face capture process"""
    global face_capture_running, face_capture_cap

    face_capture_running = False
    if face_capture_cap:
        face_capture_cap.release()
        face_capture_cap = None

    return face_capture_count


def get_face_capture_progress():
    """Get current face capture progress"""
    global face_capture_count, face_capture_target
    return {
        "captured": face_capture_count,
        "target": face_capture_target,
        "percentage": (face_capture_count / face_capture_target) * 100 if face_capture_target > 0 else 0
    }

def capture_faces(employee_id, employee_name):
    """Legacy function - kept for backward compatibility"""
    success, message = start_face_capture(employee_id, employee_name)
    if success:
        return f'media/faces/{employee_id}_{employee_name.strip()}'
    else:
        return None


def cache_embeddings():
    """Cache face embeddings for registered users."""
    df = pd.read_csv(users_file)
    embeddings = []
    for _, row in df.iterrows():
        folder_path = row['Image Path']
        if not os.path.exists(folder_path):
            continue
        for file_name in os.listdir(folder_path):
            image_path = os.path.join(folder_path, file_name)
            try:
                img = Image.open(image_path)
                with torch.no_grad():
                    face, _ = mtcnn(img, return_prob=True)
                    if face is not None:
                        face = face.unsqueeze(0).to(device)
                        embedding = model(face)
                        embeddings.append((embedding[0].cpu(), row['Name']))
            except Exception as e:
                logging.error(f"Error processing image {image_path}: {e}")
    return embeddings

known_embeddings = cache_embeddings()

detection_running = False
detection_thread = None
rtsp_url = "rtsp://admin:admin%401966@192.168.100.112:554/cam/realmonitor?channel=4&subtype=0"
current_camera_source = "laptop"  # 'laptop' or 'rtsp'
current_camera_id = "0"
current_camera_name = "Laptop Camera"

# Import camera configuration
from services.camera_config import CAMERA_CONFIG, DEFAULT_CAMERA_ID, DEFAULT_CAMERA_NAME, DEFAULT_CAMERA_TYPE


def generate_detection_frames():
    """Generator function that yields YOLO-processed frames from camera"""
    global detection_running, current_camera_id, current_camera_name

    # Get camera configuration
    camera_config = CAMERA_CONFIG.get(current_camera_id, CAMERA_CONFIG["0"])
    camera_name = camera_config["name"]
    camera_type = camera_config["type"]
    camera_url = camera_config["url"]
    
    print(f"Using camera: {camera_name} (ID: {current_camera_id}, Type: {camera_type})")
    
    # Open camera based on type
    if camera_type == 'rtsp' and camera_url:
        print(f"Opening RTSP camera: {camera_url}")
        cam = cv2.VideoCapture(camera_url)
    elif camera_type == 'laptop':
        print(f"Opening laptop camera (index 0)")
        cam = cv2.VideoCapture(0)
    else:
        # For other types, try to use camera_id as index
        print(f"Opening camera with index: {current_camera_id}")
        cam = cv2.VideoCapture(int(current_camera_id))
    
    if not cam.isOpened():
        print(f"Error: Could not open camera {camera_name}. Type: {camera_type}, URL: {camera_url}")
        return

    # Class names for different objects detected by the model
    '''classNames = ['Hardhat', 'Mask', 'NO-Hardhat', 'NO-Mask', 'NO-Safety Vest', 'Person', 
                 'Safety Cone', 'Safety Vest', 'machinery', 'vehicle']'''

    classNames = ['Helmet', 'Safety_Vest', 'Safety_goggles', 'Safety_shoes', 'NO_helmet', 'NO_Vest',
                  'NO_goggles', 'NO_safetyshoes', 'Person']

    try:
        while detection_running:
            success, img = cam.read()
            if not success:
                break

            curr_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Perform object detection
            results = yolo_model(img, stream=True)

            for r in results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                    # Calculate confidence and class index
                    conf = math.ceil((box.conf[0] * 100)) / 100
                    cls = int(box.cls[0])
                    currentClass = classNames[cls]

                    # Set color based on the class
                    if conf > 0.5:
                        if currentClass in ['NO_helmet', 'NO_Vest', 'NO_goggles', 'NO_safetyshoes']:
                            myColor = (0, 0, 255)  # Red
                            cv2.imwrite(
                                f"media/face_detect/output{curr_datetime}.jpg", img)
                            cv2.imwrite("media/face_detect/output.jpg", img)
                        elif currentClass in ['Helmet', 'Safety_Vest', 'Safety_goggles', 'Safety_shoes']:
                            myColor = (0, 255, 0)  # Green
                        else:
                            myColor = (255, 0, 0)  # Blue

                        # Display the class name and confidence
                        cvzone.putTextRect(img, f'{classNames[cls]} {conf}',
                                           (max(0, x1), max(35, y1)), scale=1, thickness=1,
                                           colorB=myColor, colorT=(
                                               255, 255, 255),
                                           colorR=myColor, offset=5)

                        # Draw bounding box
                        cv2.rectangle(img, (x1, y1), (x2, y2), myColor, 3)

                        # Detect faces
                        detectFace(currentClass)

            # Resize for better performance
            img = cv2.resize(img, (640, 480))

            # Encode frame as JPEG
            _, buffer = cv2.imencode(
                '.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    finally:
        cam.release()


def run_detection():
    global detection_running
    detection_running = True
    print("Detection thread started - detection_running set to True")

    # This function now just sets the flag - streaming is handled by the route below


@app.route('/detection_feed')
def detection_feed():
    """Route for streaming processed camera feed"""
    print(f"Detection feed requested - detection_running: {detection_running}")
    try:
        return Response(
            generate_detection_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
    except Exception as e:
        print(f"Error in detection_feed: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/cameras', methods=['GET'])
def get_cameras():
    """Get list of available cameras"""
    # Reload camera config to get latest changes
    from services.camera_config import CAMERA_CONFIG
    return jsonify({
        "cameras": CAMERA_CONFIG,
        "current_camera_id": current_camera_id,
        "current_camera_name": current_camera_name,
        "total_cameras": len(CAMERA_CONFIG)
    })

@app.route('/safetydetection', methods=['GET', 'POST'])
def safety():
    global detection_thread, detection_running, current_camera_id, current_camera_name, current_camera_source
    
    if request.method == 'POST':
        data = request.get_json()
        camera_id = data.get('camera_id', '0')
        
        # Get camera info from config
        camera_config = CAMERA_CONFIG.get(camera_id, CAMERA_CONFIG["0"])
        camera_name = camera_config["name"]
        camera_type = camera_config["type"]
        
        print(f"Starting detection with Camera ID: {camera_id}, Name: {camera_name}, Type: {camera_type}")
        
        # Update global variables
        current_camera_id = camera_id
        current_camera_name = camera_name
        current_camera_source = camera_type
    else:
        camera_id = current_camera_id
        camera_name = current_camera_name
        camera_type = current_camera_source
    
    if not detection_running:
        detection_thread = threading.Thread(target=run_detection)
        detection_thread.start()
        return jsonify({
            "message": f"Detection started using {camera_name}",
            "stream_url": url_for('detection_feed'),
            "camera_id": camera_id,
            "camera_name": camera_name,
            "camera_type": camera_type
        })
    else:
        return jsonify({"message": "Detection already running"})

@app.route('/capture_faces', methods=['POST'])
def register():
    """Register a new employee and capture their face images."""
    try:
        name = request.form.get('employeeName', '').strip()
        roll_no = request.form.get('employeeId', '').strip()

        if not name or not roll_no:
            return jsonify({"status": "error", "message": "Name and Roll No are required."}), 400

        logging.info(f"Received data - Name: {name}, Roll No: {roll_no}")
        user_dir = capture_faces(roll_no, name)
        if user_dir is None:
            return jsonify({"status": "error", "message": "Error capturing faces."}), 400

        df = pd.read_csv(users_file)
        df = pd.concat([df, pd.DataFrame({'Name': [name], 'Roll No': [
                       roll_no], 'Image Path': [user_dir]})], ignore_index=True)
        df.to_csv(users_file, index=False)

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                query = "INSERT INTO registered_employees (EmployeeName, EmployeeID, Images) VALUES (%s, %s, %s)"
                cursor.execute(query, (name, roll_no, user_dir))
                conn.commit()
                logging.info(
                    f"Inserted {cursor.rowcount} record(s) successfully.")
            except mysql.connector.Error as err:
                conn.rollback()
                logging.error(f"Database error: {err}")
                return jsonify({"status": "error", "message": "Database error."}), 500
            finally:
                cursor.close()
                conn.close()

        global known_embeddings
        known_embeddings = cache_embeddings()

        return jsonify({"status": "success", "message": "Employee registered successfully."})
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({"status": "error", "message": "Internal server error."}), 500

@app.route('/start_face_capture', methods=['POST'])
def start_face_capture_route():
    """Start face capture process with streaming"""
    try:
        # Handle both JSON and form data
        if request.is_json and request.json:
            name = request.json.get('employeeName', '').strip()
            roll_no = request.json.get('employeeId', '').strip()
        else:
            name = request.form.get('employeeName', '').strip()
            roll_no = request.form.get('employeeId', '').strip()

        if not name or not roll_no:
            return jsonify({"status": "error", "message": "Name and Roll No are required."}), 400

        success, message = start_face_capture(roll_no, name)
        if not success:
            return jsonify({"status": "error", "message": message}), 400

        return jsonify({
            "status": "success",
            "message": message,
            "stream_url": url_for('face_capture_feed'),
            "progress_url": url_for('face_capture_progress')
        })
    except Exception as e:
        logging.error(f"Error starting face capture: {e}")
        return jsonify({"status": "error", "message": "Internal server error."}), 500

@app.route('/face_capture_feed')
def face_capture_feed():
    """Route for streaming face capture feed"""
    try:
        return Response(
            generate_face_capture_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/face_capture_progress')
def face_capture_progress():
    """Get current face capture progress"""
    try:
        progress = get_face_capture_progress()
        return jsonify(progress)
    except Exception as e:
        logging.error(f"Error getting face capture progress: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/stop_face_capture', methods=['POST'])
def stop_face_capture_route():
    """Stop face capture process and return final count"""
    try:
        captured_count = stop_face_capture()

        if captured_count >= 20:
            return jsonify({
                "status": "success",
                "message": f"Face capture completed. {captured_count} images captured.",
                "captured_count": captured_count
            })
        else:
            return jsonify({
                "status": "warning",
                "message": f"Face capture stopped. Only {captured_count} images captured.",
                "captured_count": captured_count
            })
    except Exception as e:
        logging.error(f"Error stopping face capture: {e}")
        return jsonify({"status": "error", "message": "Internal server error."}), 500

    """Start the Streamlit app if it's not already running."""
    if not is_streamlit_running():
        subprocess.Popen(["streamlit", "run", "dashmain.py"],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)


@app.route('/')
def home():
    """Render the home dashboard."""
    start_streamlit()
    return render_template('dashboard.html')

@app.route('/login')
def login_page():
    """Render the login page."""
    return render_template('login.html')


# Define other routes
@app.route('/employee_config.html', methods=['GET'])
def employee_config():
    """Display employee configuration."""
    conn = get_db_connection()
    employees = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Registered_Employees")
            employees = cursor.fetchall()
        except mysql.connector.Error as err:
            logging.error(f"Database error: {err}")
        finally:
            cursor.close()
            conn.close()
    return render_template('employee_config.html', employees=employees)

@app.route('/api/employees', methods=['GET'])
def get_employees():
    """Get all registered employees."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()
        cursor.execute(
            "SELECT EmployeeName, EmployeeID, Images FROM Registered_Employees")
        Employee = namedtuple(
            'Employee', ['EmployeeName', 'EmployeeID', 'Images'])
        employees = [Employee(*row) for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        # Convert the data to a list of dictionaries, handling binary data
        serializable_employees = []
        for employee in employees:
            # Create a new dictionary with the values we need
            employee_dict = {
                'EmployeeName': str(employee.EmployeeName) if employee.EmployeeName is not None else '',
                'EmployeeID': str(employee.EmployeeID) if employee.EmployeeID is not None else '',
                'Images': base64.b64encode(employee.Images).decode('utf-8')
                if isinstance(employee.Images, bytes)
                else str(employee.Images) if employee.Images is not None else ''
            }
            serializable_employees.append(employee_dict)

        return jsonify(serializable_employees)
    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return jsonify({"error": str(err)}), 500
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/model_management.html', methods=['GET'])
def model_management():
    """Display model configuration."""
    conn = get_db_connection()
    models = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM EmployeeInfo.Models")
            models = cursor.fetchall()
        except mysql.connector.Error as err:
            logging.error(f"Database error: {err}")
        finally:
            cursor.close()
            conn.close()
    return render_template('model_management.html', models=models)

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get all registered models."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM EmployeeInfo.Models")
        models = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(models)
    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return jsonify({"error": str(err)}), 500
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/model_mapping.html', methods=['GET'])
def model_mapping():
    return render_template('model_mapping.html')

@app.route('/camera_management.html', methods=['GET'])
def camera_management():
    """Display model configuration."""
    conn = get_db_connection()
    cams = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM EmployeeInfo.Camera;")
            cams = cursor.fetchall()
        except mysql.connector.Error as err:
            logging.error(f"Database error: {err}")
        finally:
            cursor.close()
            conn.close()
    return render_template('camera_management2.html', cams=cams)

@app.route('/api/cameras', methods=['GET'])
def cameras():
    """Get all registered cameras."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM EmployeeInfo.Camera")
        cams = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(cams)
    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return jsonify({"error": str(err)}), 500
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500

def get_notifications():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        sql = """
        SELECT Exception_Type, Username, time_occurred
        FROM EmployeeInfo.Exception_Logs
        ORDER BY time_occurred DESC 
        LIMIT 12
        """
        cursor.execute(sql)
        notifications = []

        for row in cursor.fetchall():
            # Type cast to avoid linter issues
            notification: dict = dict(row)  # type: ignore

            # # Convert BLOB to base64 if image exists
            # if 'Incident_image' in notification and notification['Incident_image']:
            #     img_data = notification['Incident_image']
            #     if isinstance(img_data, bytes):
            #         notification['image_base64'] = base64.b64encode(img_data).decode('utf-8')
            # Time formatting remains the same
            if 'time_occurred' in notification:
                time_occurred = notification['time_occurred']
                if isinstance(time_occurred, str):
                    time_occurred = datetime.strptime(
                        time_occurred, '%Y-%m-%d %H:%M:%S')
                elif not isinstance(time_occurred, datetime):
                    time_occurred = datetime.now()

                time_diff = datetime.now() - time_occurred

                if time_diff < timedelta(minutes=1):
                    notification['time_ago'] = "Just now"
                elif time_diff < timedelta(hours=1):
                    minutes = int(time_diff.seconds / 60)
                    notification['time_ago'] = f"{minutes} mins ago"
                elif time_diff < timedelta(days=1):
                    hours = int(time_diff.seconds / 3600)
                    notification['time_ago'] = f"{hours} hours ago"
                else:
                    days = time_diff.days
                    notification['time_ago'] = f"{days} days ago"

            notifications.append(notification)

        return notifications
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/notifications', methods=['GET'])
def get_notifications_api():
    try:
        notifications = get_notifications()
        return jsonify(notifications)
    except Exception as e:
        logging.error(f"Error in notifications route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/camera_dashboard.html', methods=['GET'])
def camera_dashboard():
    return render_template('camera_dashboard.html')

@app.route('/notifications.html', methods=['GET'])
def notifications():
    try:
        notifications = get_notifications()
        return render_template('notifications.html', notifications=notifications)
    except Exception as e:
        logging.error(f"Error in notifications route: {e}")
        return render_template('notifications.html', notifications=[])


@app.route('/settings.html', methods=['GET'])
def settings():
    return render_template('settings.html')

@app.route('/profile.html', methods=['GET'])
def profile():
    return render_template('profile.html')

@app.route('/dashboard.html', methods=['GET'])
def dash():
    start_streamlit()
    return render_template('dashboard.html')

@app.route('/stopdetection', methods=['POST'])
def stop_detection():
    global detection_running
    try:
        detection_running = False
        return jsonify({"message": "Detection stopped"})
    except Exception as e:
        # Logs the error to the console
        print(f"Error stopping detection: {e}")
        return jsonify({"message": "Failed to stop detection", "error": str(e)}), 500


@app.route('/report')
def get_report():
    today_date = datetime.now().strftime("%Y-%m-%d")
    report_filename = f"log/violation_report_{today_date}.txt"

    # Connect to MySQL
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Query to fetch only today's violation data
    query = f"""
    SELECT time_occurred, Username, Employee_id, Exception_Type
    FROM EmployeeInfo.Exception_Logs WHERE DATE(time_occurred) = '{today_date}';
    """
    cursor.execute(query)

    # Load data into a Pandas DataFrame
    if cursor.description is not None:
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(cursor.fetchall(), columns=columns)
    else:
        df = pd.DataFrame()  # Empty DataFrame if no description

    # Close the connection
    cursor.close()
    conn.close()

    # If no violations today, generate an empty report
    if df.empty:
        report = f"""
SAFETY VIOLATION REPORT - {today_date}
--------------------------------------
No safety violations recorded today.
"""
    else:
        # Count total violations
        total_violations = len(df)

        # Count violations per employee
        violations_per_employee = df.groupby(
            "Username")["Exception_Type"].count().reset_index()
        violations_per_employee.columns = ["Username", "Total_Violations"]

        # Find who made the most errors (if applicable)
        most_errors = violations_per_employee.sort_values(
            by="Total_Violations", ascending=False).iloc[0]

        # Count violations per type
        violations_per_type = df["Exception_Type"].value_counts()

        # # Generate name-wise fault report
        # namewise_fault_report = df.groupby("Username").apply(
        #     lambda x: x[["time_occurred", "Exception_Type"]].to_string(index=False)
        # ).to_string()

        # Generate report
        report = f"""
SAFETY VIOLATION REPORT - {today_date}
--------------------------------------
Total Violations: {total_violations}

Violations per Employee:
{violations_per_employee.to_string(index=False)}

Most Errors:
{most_errors["Username"]} with {most_errors["Total_Violations"]} violations

Violations per Type:
{violations_per_type.to_string()}

"""

    with open(report_filename, "w") as file:
        file.write(report)

    # Return file as a download
    return send_file(report_filename, as_attachment=True)


# Configure upload folder
UPLOAD_FOLDER = 'media/uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'jpg', 'jpeg', 'png'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def display_video(video_path):
    """Function to run in separate process for displaying video"""
    cap = cv2.VideoCapture(video_path)


yolo_model2 = YOLO("models/best700.pt")


def generate_processed_frames2(video_path):
    """Generator function that yields YOLO-processed frames"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Could not open video file")
        while True:
            success, frame = cap.read()
            if not success:
                break

            # Process frame with YOLO (auto-draws boxes)
            results = yolo_model(frame)
            annotated_frame = results[0].plot()

            # Resize for better performance
            annotated_frame = cv2.resize(annotated_frame, (640, 480))

            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', annotated_frame,
                                     # 80% quality
                                     [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            # Adjust sleep based on actual processing speed
            time.sleep(0.033)  # ~30fps

    except Exception as e:
        print(f"Streaming error: {str(e)}")
    finally:
        cap.release()
  # line based detection


def generate_processed_frames3(video_path):
    """Generator function that yields PPE detection processed frames with zone-based analysis"""
    try:
        # PPE Detection Configuration
        CONF_THRES = 0.25
        IOU_THRES = 0.45

        # Which PPEs are required by zone:
        REQUIRED_LEFT = {"L"}
        REQUIRED_RIGHT = {"helmet", "shoes", "goggles", "safety_vest", "pvc_suit",
                          "no_helmet", "no_safety_shoes", "no_goggles", "no_pvc_suit", "no_safety_vest"}

        # Class name aliases to normalize to canonical names
        ALIASES = {
            "helmet": {"helmet", "hardhat", "safety_helmet", "Helmet"},
            "shoes": {"shoes", "safety_shoes", "boots", "Safety Shoes"},
            "goggles": {"goggles", "safety_goggles", "glasses", "eye_protection", "Safety Goggles"},
            "pvc_suit": {"pvc_suit", "pvc", "chem_suit", "hazmat_suit", "PVC Suit"},
            "safety_vest": {"vest", "safety_vest", "vest"},
            "no_safety_vest": {"no_vest", "no_safety_vest", "no_vest"},
            "no_pvc_suit": {"no_suit", "no_safety_suit", "no_safety_vest"},
            "no_goggles": {"no_goggles", "no_safety_goggles", "no_eye_protection", "no_safety_goggles"},
            "no_safety_shoes": {"no_shoes", "no_safety_shoes", "no_boots", "no_safety_shoes"},
            "no_helmet": {"no_helmet", "no_safety_helmet", "no_hardhat", "no_safety_helmet"}
        }
        # Colors
        CLR_OK = (0, 200, 0)
        CLR_MISS = (255, 0, 0)  # Blue
        CLR_LINE = (255, 255, 255)
        CLR_MISS_TEXT = (255, 255, 255)  # White text
        CLR_MISS_BG = (255, 0, 0)  # Blue background
        def canonicalize(name: str) -> str:
            n = name.lower().replace(" ", "_")
            for canon, synonyms in ALIASES.items():
                if n == canon or n in synonyms:
                    return canon
            return n  # fallback

        def center_of_box(xyxy):
            x1, y1, x2, y2 = xyxy
            return ((x1 + x2) / 2, (y1 + y2) / 2)

        def point_side_of_line(px, py, x1, y1, x2, y2):
            """Returns sign of cross product for vertical line: >0 = left side, <0 = right side, =0 = on the line"""
            return (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)

        def inside_bbox(px, py, xyxy):
            x1, y1, x2, y2 = xyxy
            return x1 <= px <= x2 and y1 <= py <= y2

        def draw_label(img, text, x, y, color=(255, 255, 255), bg=(0, 0, 0)):
            (tw, th), base = cv2.getTextSize(
                text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(img, (x, y - th - 6), (x + tw + 6, y + 2), bg, -1)
            cv2.putText(img, text, (x + 3, y - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Could not open video file")

        # Calculate the video width and height
        W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Set vertical divider
        x_mid = W // 2
        divider = [x_mid, 0, x_mid, H - 1]
        zone_names = ("LEFT", "RIGHT")

        x1, y1, x2, y2 = divider

        person_class_ids = set()

        # Class name map
        model_names = {i: canonicalize(n) for i, n in yolo_model.names.items()}

        # Detect person class ID(s)
        for idx, name in yolo_model.names.items():
            if name.lower() == "person":
                person_class_ids.add(idx)

        if not person_class_ids:
            print("⚠️ Warning: model has no 'person' class.")

        while True:
            success, frame = cap.read()
            if not success:
                break

            # Run YOLO detection
            results = yolo_model.predict(
                frame, conf=CONF_THRES, iou=IOU_THRES, verbose=False)
            dets = results[0].boxes

            # Prepare detections for tracking
            detections_for_tracker = []
            persons_detections = []
            ppe_items = []
            if dets is not None and dets.shape[0] > 0:
                for i in range(len(dets)):
                    xyxy = dets.xyxy[i].cpu().tolist()
                    cls = int(dets.cls[i].cpu().item())
                    conf = float(dets.conf[i].cpu().item())
                    name = yolo_model.names.get(cls, str(cls))
                    cname = model_names.get(cls, canonicalize(name))
                    if cls in person_class_ids or cname == "person":
                        # Simple tracking format
                        w = xyxy[2] - xyxy[0]
                        h = xyxy[3] - xyxy[1]
                        detections_for_tracker.append(
                            ([xyxy[0], xyxy[1], w, h], conf, cname))
                        persons_detections.append({"bbox": xyxy, "conf": conf})
                    else:
                        cx, cy = center_of_box(xyxy)
                        ppe_items.append({"bbox": xyxy, "center": (
                            cx, cy), "name": cname, "conf": conf})

            # Simple tracking without DeepSort
            tracks = []
            for i, det in enumerate(detections_for_tracker):
                class SimpleTrack:
                    def __init__(self, track_id, bbox):
                        self.track_id = track_id
                        self.bbox = bbox

                    def is_confirmed(self):
                        return True

                    def to_ltrb(self):
                        return self.bbox

                bbox, conf, name = det
                tracks.append(SimpleTrack(
                    i, [bbox[0], bbox[1], bbox[0] + bbox[2], bbox[1] + bbox[3]]))

            annotated = frame.copy()

            # Iterate through tracked persons and process PPE
            for track in tracks:
                if not track.is_confirmed():
                    continue
                track_id = track.track_id
                ltrb = track.to_ltrb()
                px1, py1, px2, py2 = ltrb
                pcx, pcy = center_of_box(ltrb)

                sign = point_side_of_line(pcx, pcy, x1, y1, x2, y2)
                zone = zone_names[0] if sign > 0 else zone_names[1] if sign < 0 else "ON_LINE"

                owned = []
                for it in ppe_items:
                    cx, cy = it["center"]
                    # Check if the PPE item is inside the tracked person's bounding box
                    if inside_bbox(cx, cy, ltrb):
                        owned.append(it["name"])

                owned_set = set(owned)

                # Zone rules
                if zone == "LEFT":
                    required = REQUIRED_LEFT
                elif zone == "RIGHT":
                    required = REQUIRED_RIGHT
                else:
                    # For simplicity, combining requirements on the line
                    required = REQUIRED_LEFT.union(REQUIRED_RIGHT)
                # Identify missing items by checking if any of the "no_" classes are present
                missing_items = []
                for required_item in required:
                    if f"no_{required_item}" in owned_set:
                        missing_items.append(required_item)

                color = CLR_OK if not missing_items else CLR_MISS

                # Draw bbox + label for tracked person
                cv2.rectangle(annotated, (int(px1), int(py1)),
                              (int(px2), int(py2)), color, 2)
                label = f"ID:{track_id} {zone} {'OK' if not missing_items else 'MISSING:' + ','.join(missing_items)}"
                # Use updated colors for missing label
                text_color = CLR_OK if not missing_items else CLR_MISS_TEXT
                bg_color = (40, 40, 40) if not missing_items else CLR_MISS_BG

                # Adjust text position based on zone
                text_x = int(px1)
                text_y = int(py1) - 8
                (tw, th), base = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                if zone == "RIGHT":
                    # Align text to the right of the bounding box
                    text_x = int(px2) - tw - 6

                draw_label(annotated, label, text_x, text_y,
                           color=text_color, bg=bg_color)

            # Draw divider line
            cv2.line(annotated, (int(x1), int(y1)),
                     (int(x2), int(y2)), CLR_LINE, 2)
            draw_label(annotated, f"AUTO DIVIDER (VERTICAL)", int((x1 + x2) / 2), int((y1 + y2) / 2) - 6,
                       color=(0, 0, 0), bg=(255, 255, 255))

            # HUD info
            cv2.putText(annotated, f"Required {zone_names[0]}: {', '.join(sorted(REQUIRED_LEFT))}", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(annotated, f"Required {zone_names[1]}: {', '.join(sorted(REQUIRED_RIGHT))}", (10, 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

            # Resize for better performance
            annotated = cv2.resize(annotated, (640, 480))

            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', annotated,
                                     # 80% quality
                                     [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            # Adjust sleep based on actual processing speed
            time.sleep(0.033)  # ~30fps

    except Exception as e:
        print(f"Streaming error: {str(e)}")
    finally:
        cap.release()


@app.route('/demo2', methods=['POST'])
def demo2():
    if 'file' not in request.files:
        return jsonify({"status": "error", "error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "error": "No selected file"}), 400

    if not (file and allowed_file(file.filename)):
        return jsonify({"status": "error", "error": "Invalid file type"}), 400

    try:
        # Secure filename and create upload directory
        if file.filename is None:
            return jsonify({"status": "error", "error": "No filename provided"}), 400
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        sample_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Save original file
        file.save(sample_path)

        # Create output path (consider adding timestamp for uniqueness)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"output_{timestamp}_{filename}"
        output_path = os.path.join(
            app.config['UPLOAD_FOLDER'], output_filename)

        return jsonify({
            "status": "success",
            "video_feed_url": url_for('video_feed2', video_path=sample_path),
            "download_url": url_for('static', filename=f'uploads/{output_filename}'),
            "message": "File uploaded successfully"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Processing failed: {str(e)}"
        }), 500

@app.route('/video_feed2')
def video_feed2():
    """Route for streaming PPE detection processed video with zone-based analysis"""
    video_path = request.args.get('video_path')
    if not video_path or not os.path.exists(video_path):
        return jsonify({"status": "error", "error": "Invalid video path"}), 404
    try:
        return Response(
            generate_processed_frames2(video_path),
            mimetype='multipart/x-mixed-replace; boundary=frame',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/demo3', methods=['POST'])
def demo3():
    if 'file' not in request.files:
        return jsonify({"status": "error", "error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "error": "No selected file"}), 400

    if not (file and allowed_file(file.filename)):
        return jsonify({"status": "error", "error": "Invalid file type"}), 400

    try:
        # Secure filename and create upload directory
        if file.filename is None:
            return jsonify({"status": "error", "error": "No filename provided"}), 400
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        sample_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Save original file
        file.save(sample_path)

        # Create output path (consider adding timestamp for uniqueness)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"output_{timestamp}_{filename}"
        output_path = os.path.join(
            app.config['UPLOAD_FOLDER'], output_filename)

        return jsonify({
            "status": "success",
            "video_feed_url": url_for('video_feed3', video_path=sample_path),
            "download_url": url_for('static', filename=f'uploads/{output_filename}'),
            "message": "File uploaded successfully"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Processing failed: {str(e)}"
        }), 500

@app.route('/video_feed3')
def video_feed3():
    """Route for streaming PPE detection processed video with zone-based analysis"""
    video_path = request.args.get('video_path')
    if not video_path or not os.path.exists(video_path):
        return jsonify({"status": "error", "error": "Invalid video path"}), 404
    try:
        return Response(
            generate_processed_frames3(video_path),
            mimetype='multipart/x-mixed-replace; boundary=frame',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


# ======================== CLASS-BASED DETECTION ========================

@app.route('/health', methods=['GET'])
def health_check():
    """Basic health check route"""
    return jsonify({
        "status": "success",
        "message": "Backend is running",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/test_class_detection', methods=['GET'])
def test_class_detection():
    """Test route to verify class-based detection is working"""
    return jsonify({
        "status": "success",
        "message": "Class-based detection route is working",
        "available_classes": ["helmet", "safety_vest", "pvc_suit", "shoes", "goggles"]
    })

@app.route('/test_video_stream', methods=['GET'])
def test_video_stream():
    """Simple test video stream to verify streaming works"""
    def generate_test_frames():
        import numpy as np
        frame_count = 0
        try:
            print("DEBUG: Starting test video stream")
            while frame_count < 300:  # 10 seconds at 30fps
                # Create a simple test frame
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                
                # Add animated background
                color_shift = int(50 + 30 * np.sin(frame_count * 0.1))
                frame[:] = (color_shift, color_shift, color_shift)
                
                # Add text
                cv2.putText(frame, "Test Video Stream", (50, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(frame, f"Frame {frame_count}", (50, 150), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                cv2.putText(frame, "If you see this, streaming works!", (50, 200), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Add a moving circle
                center_x = int(320 + 200 * np.sin(frame_count * 0.2))
                center_y = int(240 + 100 * np.cos(frame_count * 0.2))
                cv2.circle(frame, (center_x, center_y), 20, (0, 255, 0), -1)
                
                # Encode frame
                success, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if not success:
                    print(f"DEBUG: Failed to encode test frame {frame_count}")
                    break
                    
                frame_bytes = buffer.tobytes()
                
                if frame_count % 30 == 0:
                    print(f"DEBUG: Yielding test frame {frame_count}, size: {len(frame_bytes)} bytes")
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                frame_count += 1
                time.sleep(0.033)  # 30 FPS
                
            print(f"DEBUG: Finished test stream with {frame_count} frames")
                
        except Exception as e:
            print(f"DEBUG: Error in test video generation: {str(e)}")
            import traceback
            traceback.print_exc()
    
    return Response(
        generate_test_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
            'Transfer-Encoding': 'chunked'
        }
    )

@app.route('/demo4', methods=['POST'])
def demo4():
    """Class-based PPE detection route"""
    print("DEBUG: demo4 route called")
    
    if 'file' not in request.files:
        print("DEBUG: No file part in request")
        return jsonify({"status": "error", "error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        print("DEBUG: No selected file")
        return jsonify({"status": "error", "error": "No selected file"}), 400

    if not (file and allowed_file(file.filename)):
        print(f"DEBUG: Invalid file type: {file.filename}")
        return jsonify({"status": "error", "error": "Invalid file type"}), 400

    # Get classes from request
    classes_json = request.form.get('classes', '["helmet", "shoes", "pvc_suit"]')
    print(f"DEBUG: Received classes JSON: {classes_json}")
    try:
        selected_classes = json.loads(classes_json)
        print(f"DEBUG: Parsed classes: {selected_classes}")
    except json.JSONDecodeError as e:
        print(f"DEBUG: JSON decode error: {e}")
        selected_classes = ["helmet", "shoes", "pvc_suit"]

    try:
        # Secure filename and create upload directory
        if file.filename is None:
            return jsonify({"status": "error", "error": "No filename provided"}), 400
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        sample_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Save original file
        file.save(sample_path)

        # Create output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"output_{timestamp}_{filename}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

        # Store the selected classes in the app context
        app.class_based_classes = selected_classes
        print(f"DEBUG: Stored classes in app context: {selected_classes}")

        video_feed_url = url_for('video_feed4', video_path=sample_path)
        print(f"DEBUG: Generated video feed URL: {video_feed_url}")
        
        return jsonify({
            "status": "success",
            "video_feed_url": video_feed_url,
            "download_url": url_for('static', filename=f'uploads/{output_filename}'),
            "message": f"File uploaded successfully with classes: {selected_classes}"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Processing failed: {str(e)}"
        }), 500


@app.route('/video_feed4')
def video_feed4():
    """Route for streaming class-based PPE detection processed video"""
    video_path = request.args.get('video_path')
    print(f"DEBUG: video_feed4 called with video_path: {video_path}")
    
    if not video_path or not os.path.exists(video_path):
        print(f"DEBUG: Invalid video path: {video_path}")
        return jsonify({"status": "error", "error": "Invalid video path"}), 404

    try:
        print("DEBUG: Starting video feed generation...")
        return Response(
            generate_processed_frames4(video_path),
            mimetype='multipart/x-mixed-replace; boundary=frame',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no',  # Disable nginx buffering
                'Transfer-Encoding': 'chunked'
            }
        )
    except Exception as e:
        print(f"DEBUG: Error in video_feed4: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


def generate_processed_frames4(video_path):
    """Generator function for class-based PPE detection"""
    cap = None
    try:
        # Get the selected classes from app context
        selected_classes = getattr(app, 'class_based_classes', ["helmet", "shoes", "pvc_suit"])
        print(f"DEBUG: Retrieved classes from app context: {selected_classes}")
        
        # Initialize tracker (simplified version without DeepSort for now)
        # tracker = DeepSort(max_age=70, n_init=3)
        tracker = None
        
        # Class name aliases to normalize names from the model to a standard form
        ALIASES = {
            "person": {"person", "Person"},
            "helmet": {"helmet", "hardhat", "safety_helmet", "Helmet"},
            "safety_vest": {"vest", "safety_vest", "Safety_Vestr"},
            "no_helmet": {"no_helmet", "no_safety_helmet", "no_hardhat", "NO_helmet"},
            "no_safety_vest": {"no_vest", "no_safety_vest", "NO_Vestr"},
            "pvc_suit": {"pvc_suit", "suit"},
            "no_pvc_suit": {"no_pvc_suit", "no_suit"},
            "shoes": {"shoes", "safety_shoes", "boots", "Safety Shoes"},
            "goggles": {"goggles", "safety_goggles", "glasses", "eye_protection", "Safety Goggles"},
            "no_safety_shoes": {"no_shoes", "NO_safetyshoes", "no_boots", "no_safety_shoes"},
            "no_goggles": {"no_goggles", "NO_goggles", "no_eye_protection", "no_safety_goggles"},
        }

        # Visual Configuration
        CLR_OK = (0, 200, 0)
        CLR_MISS = (0, 0, 255)

        def canonicalize(name: str) -> str:
            """Converts a class name to its canonical form using the ALIASES map."""
            n = name.lower().replace(" ", "_")
            for canon, synonyms in ALIASES.items():
                if n == canon or n in synonyms:
                    return canon
            return n

        def center_of_box(xyxy):
            """Calculates the center point of a bounding box."""
            x1, y1, x2, y2 = xyxy
            return (int((x1 + x2) / 2), int((y1 + y2) / 2))

        def inside_bbox(point, bbox):
            """Checks if a point is inside a bounding box."""
            px, py = point
            x1, y1, x2, y2 = bbox
            return x1 <= px <= x2 and y1 <= py <= y2


        # Determine required classes for detection
        detect_classes_names = set()
        required_ppe = set()

        if selected_classes:
            print(f"User specified classes: {selected_classes}")
            user_ppe_types = set()
            for cls_name in selected_classes:
                canon_name = canonicalize(cls_name)
                if canon_name.startswith("no_"):
                    user_ppe_types.add(canon_name[3:])
                else:
                    user_ppe_types.add(canon_name)

            required_ppe = user_ppe_types
            print(f"Required PPE for all zones set to: {required_ppe}")

            for ppe_type in required_ppe:
                detect_classes_names.add(ppe_type)
                detect_classes_names.add(f"no_{ppe_type}")
        else:
            print("No specific classes provided. Using fallback full PPE requirements.")
            required_ppe = {"helmet", "shoes", "goggles", "safety_vest", "pvc_suit"}
            for ppe_type in required_ppe:
                detect_classes_names.add(ppe_type)
                detect_classes_names.add(f"no_{ppe_type}")

        detect_classes_names.add("person")

        # Get class indices for YOLO
        detect_class_indices = []
        model_class_map = {canonicalize(name): idx for idx, name in yolo_model.names.items()}
        for name in detect_classes_names:
            if name in model_class_map:
                detect_class_indices.append(model_class_map[name])

        print(f"Model will detect the following classes: {[yolo_model.names[i] for i in detect_class_indices]}")
        print(f"DEBUG: Required PPE set: {required_ppe}")
        print(f"DEBUG: Detect classes names: {detect_classes_names}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Could not open video file")
        
        print("DEBUG: Video opened successfully, starting processing...")
        
        frame_count = 0
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while True:
            try:
                success, frame = cap.read()
                if not success:
                    print(f"DEBUG: End of video reached after {frame_count} frames")
                    break
                
                frame_count += 1
                if frame_count % 30 == 0:  # Print every 30 frames
                    print(f"DEBUG: Processed {frame_count} frames")
                
                consecutive_errors = 0  # Reset error counter on successful frame

                # Process frame with YOLO using selected classes
                results = yolo_model.predict(frame, conf=0.3, iou=0.5, classes=detect_class_indices, verbose=False)

                dets = results[0].boxes
                detections_for_tracker = []
                ppe_items = []
                
                if dets is not None and len(dets) > 0:
                    print(f"DEBUG: Found {len(dets)} detections in frame")
                    for i in range(len(dets)):
                        xyxy = dets.xyxy[i].cpu().tolist()
                        cls_id = int(dets.cls[i].cpu().item())
                        conf = float(dets.conf[i].cpu().item())
                        class_name = canonicalize(yolo_model.names.get(cls_id, ""))

                        if class_name == "person":
                            w, h = xyxy[2] - xyxy[0], xyxy[3] - xyxy[1]
                            detections_for_tracker.append(([xyxy[0], xyxy[1], w, h], conf, class_name))
                            print(f"DEBUG: Found person with confidence {conf}")
                        else:
                            # Only consider PPE detections above the confidence threshold
                            if conf >= 0.3:
                                ppe_items.append({"center": center_of_box(xyxy), "name": class_name})
                                print(f"DEBUG: Found PPE item: {class_name} with confidence {conf}")

                # Simple detection without tracking for now
                for i, detection in enumerate(detections_for_tracker):
                    x1, y1, w, h = detection[0]
                    conf = detection[1]
                    class_name = detection[2]
                    
                    x2, y2 = x1 + w, y1 + h
                    px1, py1, px2, py2 = map(int, [x1, y1, x2, y2])

                    # Check for nearby PPE items
                    owned_ppe = {item["name"] for item in ppe_items if inside_bbox(item["center"], [px1, py1, px2, py2])}
                    missing_items = set()
                    present_items = set()

                    # Improved logic for detecting present vs missing items
                    for required_item in required_ppe:
                        if required_item in owned_ppe:
                            present_items.add(required_item)
                        elif f"no_{required_item}" in owned_ppe:
                            missing_items.add(required_item)
                        else:
                            missing_items.add(required_item)

                    color = CLR_MISS if missing_items else CLR_OK
                    cv2.rectangle(frame, (px1, py1), (px2, py2), color, 2)

                    # Enhanced visual display with better formatting
                    x, y = px1, py1 - 10
                    base_text = f"ID: {i+1} PPE:"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    scale = 0.6        # Increased text size
                    thickness = 2      # Increased thickness

                    # Compute text size for background
                    text_size = cv2.getTextSize(base_text, font, scale, thickness)[0]
                    overlay = frame.copy()
                    cv2.rectangle(overlay, (x-2, y-16), (x + text_size[0] + 4, y+6), (0,0,0), -1)
                    alpha = 0.6
                    frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

                    cv2.putText(frame, base_text, (x, y), font, scale, (255,255,255), thickness)

                    offset_x = x + text_size[0] + 10

                    for item in sorted(list(required_ppe)):
                        if item in present_items:
                            status = "OK"
                            text_color = (0, 200, 0)  # Green
                        else:
                            status = "MISSING"
                            text_color = (0, 0, 255)  # Red

                        text = f" {item}:{status}"
                        tsize = cv2.getTextSize(text, font, scale, thickness)[0]
                        overlay = frame.copy()
                        cv2.rectangle(overlay, (offset_x-2, y-16), (offset_x + tsize[0] + 4, y+6), (0,0,0), -1)
                        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

                        cv2.putText(frame, text, (offset_x, y), font, scale, text_color, thickness)
                        offset_x += tsize[0] + 10

                # Resize for better performance
                frame = cv2.resize(frame, (640, 480))

                # Encode frame as JPEG
                _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                frame_bytes = buffer.tobytes()

                if frame_count % 30 == 0:  # Print every 30 frames
                    print(f"DEBUG: Yielding frame {frame_count}, size: {len(frame_bytes)} bytes")

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

                # Adjust sleep based on actual processing speed
                time.sleep(0.033)  # ~30fps
                
            except Exception as frame_error:
                consecutive_errors += 1
                print(f"DEBUG: Error processing frame {frame_count}: {str(frame_error)}")
                if consecutive_errors >= max_consecutive_errors:
                    print(f"DEBUG: Too many consecutive errors ({consecutive_errors}), stopping stream")
                    break
                continue

    except Exception as e:
        print(f"Class-based detection streaming error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if cap is not None:
            cap.release()
            print("DEBUG: Video capture released")


# ======================== MAIN ========================


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
