from flask import Blueprint, jsonify, request, Response, url_for, render_template
import mysql.connector
import logging
import base64
import os
import time
import cv2
import torch
import pandas as pd
from PIL import Image
from collections import namedtuple
from db.db import get_db_connection
from facenet_pytorch import InceptionResnetV1, MTCNN



employee_configuration_bp = Blueprint('employee_configuration', __name__, url_prefix='/api/employee_configuration')

# Global variables for face capture streaming
face_capture_running = False
face_capture_count = 0
face_capture_target = 20
face_capture_user_dir = None
face_capture_cap = None

# Device and model initialization
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = InceptionResnetV1(pretrained='vggface2').eval().to(device)
mtcnn = MTCNN(keep_all=False, device=device)

# CSV file to store registered users
users_file = 'data/users.csv'
if not os.path.exists(users_file):
    pd.DataFrame(columns=['Name', 'Roll No', 'Image Path']
                 ).to_csv(users_file, index=False)

# Global variable for known embeddings
known_embeddings = []

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

            # Validate frame before encoding
            if display_frame is None or display_frame.size == 0:
                print("Warning: Display frame is empty, skipping...")
                continue

            # Encode frame as JPEG with error checking
            success, buffer = cv2.imencode('.jpg', display_frame, [
                                     int(cv2.IMWRITE_JPEG_QUALITY), 80])
            
            if not success or buffer is None or buffer.size == 0:
                print("Warning: Failed to encode display frame, skipping...")
                continue
                
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



@employee_configuration_bp.route('/employees', methods=['GET'])
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


@employee_configuration_bp.route('/capture_faces', methods=['POST'])
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


@employee_configuration_bp.route('/start_face_capture', methods=['POST'])
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
            "stream_url": url_for('employee_configuration.face_capture_feed'),
            "progress_url": url_for('employee_configuration.face_capture_progress')
        })
    except Exception as e:
        logging.error(f"Error starting face capture: {e}")
        return jsonify({"status": "error", "message": "Internal server error."}), 500


@employee_configuration_bp.route('/face_capture_feed')
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


@employee_configuration_bp.route('/face_capture_progress')
def face_capture_progress():
    """Get current face capture progress"""
    try:
        progress = get_face_capture_progress()
        return jsonify(progress)
    except Exception as e:
        logging.error(f"Error getting face capture progress: {e}")
        return jsonify({"error": "Internal server error"}), 500


@employee_configuration_bp.route('/stop_face_capture', methods=['POST'])
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


@employee_configuration_bp.route('/del_employee', methods=['DELETE'])
def delete_employee():
    """Delete an employee by ID"""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        
        if not employee_id:
            return jsonify({"status": "error", "message": "Employee ID is required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"status": "error", "message": "Database connection failed"}), 500
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Registered_Employees WHERE EmployeeID = %s", (employee_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"status": "error", "message": "Employee not found"}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"status": "success", "message": "Employee deleted successfully"})
        
    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return jsonify({"status": "error", "message": "Database error"}), 500
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@employee_configuration_bp.route('/employee_config.html', methods=['GET'])
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

