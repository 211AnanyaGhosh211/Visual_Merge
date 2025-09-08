import os
from turtle import color
from ultralytics import YOLO
import cv2
import cvzone
import math
import pandas as pd
import torch
from facenet_pytorch import InceptionResnetV1, MTCNN
from PIL import Image
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, jsonify,send_file,Response, jsonify, request
from flask_cors import CORS
import detect
from detect import detectFace
import Database
from Database import database_bp
from Database import db_util
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

# Import dashdash.py functionality
import dashdash
from dashdash import api as dashboard_api

# Initialize logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)  # Initialize the Flask app
CORS(app)  # Enable CORS for all routes
app.register_blueprint(database_bp, url_prefix='/api')
app.register_blueprint(dashboard_api, url_prefix='/api')  # Register dashboard API blueprint


# MySQL Connection Configuration (as a dictionary)
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "12345",
    "database": "EmployeeInfo"
}

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
#yolo_model = YOLO("ppe.pt") 
yolo_model = YOLO("best700.pt") 


# Ensure static directory exists
os.makedirs('static/faces', exist_ok=True)

# CSV file to store registered users
users_file = 'users.csv'
if not os.path.exists(users_file):
    pd.DataFrame(columns=['Name', 'Roll No', 'Image Path']).to_csv(users_file, index=False)

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
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
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
                            face_path = os.path.join(face_capture_user_dir, f"face_{face_capture_count}.jpg")
                        cv2.imwrite(face_path, face)
                        face_capture_count += 1
                        
                        # Show capture feedback
                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 255), 3)
                        cv2.putText(display_frame, f"Captured! ({face_capture_count}/{face_capture_target})", 
                                  (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                        break
            
            # Resize for better performance
            display_frame = cv2.resize(display_frame, (640, 480))
            
            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', display_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
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
    face_capture_user_dir = f'static/faces/{employee_id}_{employee_name.strip()}'
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
        return f'static/faces/{employee_id}_{employee_name.strip()}'
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

def generate_detection_frames():
    """Generator function that yields YOLO-processed frames from camera"""
    global detection_running
    
    # Open the default camera
    cam = cv2.VideoCapture(rtsp_url)
    if not cam.isOpened():
        # Return empty generator instead of yielding error string
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
                        if currentClass in ['NO_helmet', 'NO_Vest', 'NO_goggles','NO_safetyshoes']:
                            myColor = (0, 0, 255)  # Red
                            cv2.imwrite(f"captures/output{curr_datetime}.jpg", img)
                            cv2.imwrite("output.jpg",img)
                        elif currentClass in ['Helmet', 'Safety_Vest', 'Safety_goggles','Safety_shoes']:
                            myColor = (0, 255, 0)  # Green
                        else:
                            myColor = (255, 0, 0)  # Blue

                        # Display the class name and confidence
                        cvzone.putTextRect(img, f'{classNames[cls]} {conf}',
                                           (max(0, x1), max(35, y1)), scale=1, thickness=1, 
                                           colorB=myColor, colorT=(255, 255, 255), 
                                           colorR=myColor, offset=5)

                        # Draw bounding box
                        cv2.rectangle(img, (x1, y1), (x2, y2), myColor, 3)

                        # Detect faces
                        detectFace(currentClass)

            # Resize for better performance
            img = cv2.resize(img, (640, 480))
            
            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
    finally:
        cam.release()

def run_detection():
    global detection_running
    detection_running = True
    
    # This function now just sets the flag - streaming is handled by the route below

@app.route('/detection_feed')
def detection_feed():
    """Route for streaming processed camera feed"""
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
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/safetydetection')
def safety():
    global detection_thread, detection_running
    if not detection_running:
        detection_thread = threading.Thread(target=run_detection)
        detection_thread.start()
        return jsonify({
            "message": "Detection started",
            "stream_url": url_for('detection_feed')
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
        df = pd.concat([df, pd.DataFrame({'Name': [name], 'Roll No': [roll_no], 'Image Path': [user_dir]})], ignore_index=True)
        df.to_csv(users_file, index=False)

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                query = "INSERT INTO registered_employees (EmployeeName, EmployeeID, Images) VALUES (%s, %s, %s)"
                cursor.execute(query, (name, roll_no, user_dir))
                conn.commit()
                logging.info(f"Inserted {cursor.rowcount} record(s) successfully.")
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

def is_streamlit_running():
    """Check if the Streamlit app is already running."""
    for process in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if process.info['cmdline'] and any('dashmain.py' in cmd for cmd in process.info['cmdline']):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False


def start_streamlit():
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
        cursor.execute("SELECT EmployeeName, EmployeeID, Images FROM Registered_Employees")
        Employee = namedtuple('Employee', ['EmployeeName', 'EmployeeID', 'Images'])
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
                    time_occurred = datetime.strptime(time_occurred, '%Y-%m-%d %H:%M:%S')
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
        print(f"Error stopping detection: {e}")  # Logs the error to the console
        return jsonify({"message": "Failed to stop detection", "error": str(e)}), 500

@app.route('/report')
def get_report():
    today_date = datetime.now().strftime("%Y-%m-%d")
    report_filename = f"violation_report_{today_date}.txt"

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
        violations_per_employee = df.groupby("Username")["Exception_Type"].count().reset_index()
        violations_per_employee.columns = ["Username", "Total_Violations"]

        # Find who made the most errors (if applicable)
        most_errors = violations_per_employee.sort_values(by="Total_Violations", ascending=False).iloc[0]

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

from werkzeug.utils import secure_filename
import os
from threading import Thread

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'jpg', 'jpeg', 'png'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def display_video(video_path):
    """Function to run in separate process for displaying video"""
    cap = cv2.VideoCapture(video_path)


yolo_model2=YOLO("best700.pt")
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
                                   [int(cv2.IMWRITE_JPEG_QUALITY), 80])  # 80% quality
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
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
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
    """Route for streaming processed video"""
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

# ======================== MAIN ========================

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

