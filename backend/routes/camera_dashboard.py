from flask import Blueprint, jsonify, request, Response, url_for, render_template
from werkzeug.utils import secure_filename
import os
import json
import math
import cv2
import time
import threading
from datetime import datetime
import torch
from facenet_pytorch import InceptionResnetV1, MTCNN
from services.ppe_kit_detector import detectFace
from ultralytics import YOLO
from flask import current_app
from services.camera_config import CAMERA_CONFIG


camera_dashboard_bp = Blueprint(
    'camera_dashboard', __name__, url_prefix='/api/camera_dashboard')

# Global variables for video processing
video_processing_active = False
current_processing_type = None
current_processing_video_path = None
video_processing_stop_requested = False

# Global variables for live detection
detection_running = False
detection_thread = None
current_camera_id = "0"
current_camera_name = "Laptop Camera"
current_camera_source = "laptop"

# Global variables for class-based live detection (with cv2.imshow)
class_based_live_detection_running = False
class_based_detection_thread = None
class_based_selected_classes = []
class_based_camera_id = "0"

# Default email interval in minutes (1 minute)
DEFAULT_EMAIL_INTERVAL_MINUTES = 1.0
email_interval_minutes = DEFAULT_EMAIL_INTERVAL_MINUTES

device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = InceptionResnetV1(pretrained='vggface2').eval().to(device)
mtcnn = MTCNN(keep_all=False, device=device)
yolo_model = YOLO("models/aparava_300_epoch.pt")


# Configure upload folder
UPLOAD_FOLDER = 'media/uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'jpg', 'jpeg', 'png'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ----------------------------
# Shared Bounding Box Drawing Functions
# ----------------------------

def draw_bounding_box_with_label(img, bbox, label, color=(0, 0, 255), thickness=2, 
                                 font_scale=0.6, font_thickness=2, label_bg_color=(0, 0, 0), 
                                 label_alpha=0.6, label_offset_y=-10):
    """
    Draw a bounding box with a label on an image.
    
    Args:
        img: Image to draw on
        bbox: Bounding box coordinates [x1, y1, x2, y2]
        label: Text label to display
        color: Bounding box color (B, G, R)
        thickness: Bounding box line thickness
        font_scale: Font scale for label text
        font_thickness: Font thickness for label text
        label_bg_color: Background color for label (B, G, R)
        label_alpha: Transparency of label background (0.0 to 1.0)
        label_offset_y: Y offset for label position relative to top of bbox
    
    Returns:
        Modified image with bounding box and label drawn
    """
    x1, y1, x2, y2 = [int(coord) for coord in bbox]
    
    # Draw bounding box
    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
    
    # Draw label with background
    if label:
        label_x = x1
        label_y = y1 + label_offset_y
        
        # Get text size
        font = cv2.FONT_HERSHEY_SIMPLEX
        (text_width, text_height), baseline = cv2.getTextSize(
            label, font, font_scale, font_thickness
        )
        
        # Create overlay for semi-transparent background
        overlay = img.copy()
        cv2.rectangle(
            overlay, 
            (label_x - 2, label_y - text_height - 6), 
            (label_x + text_width + 4, label_y + 6), 
            label_bg_color, 
            -1
        )
        img = cv2.addWeighted(overlay, label_alpha, img, 1 - label_alpha, 0)
        
        # Draw text
        cv2.putText(
            img, label, (label_x, label_y), 
            font, font_scale, color, font_thickness, cv2.LINE_AA
        )
    
    return img


def draw_label(img, text, x, y, color=(255, 255, 255), bg=(0, 0, 0), font_scale=0.5, thickness=1):
    """
    Draw a simple label with background on an image (for zone-based detection).
    
    Args:
        img: Image to draw on
        text: Text to display
        x, y: Position coordinates
        color: Text color (B, G, R)
        bg: Background color (B, G, R)
        font_scale: Font scale
        thickness: Font thickness
    
    Returns:
        Modified image with label drawn
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), base = cv2.getTextSize(text, font, font_scale, thickness)
    cv2.rectangle(img, (x, y - th - 6), (x + tw + 6, y + 2), bg, -1)
    cv2.putText(img, text, (x + 3, y - 6), font, font_scale, color, thickness, cv2.LINE_AA)
    return img


def draw_violation_box(img, bbox, violations, person_idx=None, color=(0, 0, 255)):
    """
    Draw a bounding box for a person with violations.
    
    Args:
        img: Image to draw on
        bbox: Bounding box coordinates [x1, y1, x2, y2]
        violations: List of violation names
        person_idx: Optional person index for label
        color: Bounding box color (B, G, R) - default red for violations
    
    Returns:
        Modified image with violation box and label drawn
    """
    # Build violation text
    violation_list = sorted(list(violations))
    if person_idx is not None:
        violation_text = f"Person {person_idx + 1} - Violations: {', '.join(violation_list)}"
    else:
        violation_text = f"Violations: {', '.join(violation_list)}"
    
    # Use shared function to draw
    return draw_bounding_box_with_label(
        img, bbox, violation_text, 
        color=color, 
        thickness=2,
        font_scale=0.6,
        font_thickness=2,
        label_bg_color=(0, 0, 0),
        label_alpha=0.6,
        label_offset_y=-10
    )


def generate_detection_frames():
    """Generator function that yields YOLO-processed frames from camera"""
    global detection_running, current_camera_id, current_camera_name, email_interval_minutes

    # Get camera configuration
    camera_config = CAMERA_CONFIG.get(current_camera_id, CAMERA_CONFIG["0"])
    camera_name = camera_config["name"]
    camera_type = camera_config["type"]
    camera_url = camera_config["url"]

    print(
        f"Using camera: {camera_name} (ID: {current_camera_id}, Type: {camera_type})")

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
        print(
            f"Error: Could not open camera {camera_name}. Type: {camera_type}, URL: {camera_url}")
        return

    try:
        frame_counter = 0
        while detection_running:
            success, img = cam.read()
            if not success:
                break

            frame_counter += 1
            curr_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            # Use YOLO's default detection with built-in visualization
            results = yolo_model(img, stream=True)

            # Process results and use YOLO's default plotting
            for r in results:
                # Use YOLO's built-in plot method for default visualization
                annotated_img = r.plot()

                # VIOLATION PROCESSING - Process violations for live detection
                boxes = r.boxes
                if boxes is not None:
                    for box in boxes:
                        # Calculate confidence and class index
                        conf = math.ceil((box.conf[0] * 100)) / 100
                        cls = int(box.cls[0])
                        currentClass = yolo_model.names[cls]
                        
                        # Check if this is a violation
                        violation_classes = [
                            'NO_helmet', 'NO_Vest', 'NO_goggles', 'NO_SafetyShoes', 'NO_Gloves']
                        is_violation = currentClass in violation_classes

                        # Process violations only
                        if conf > 0.5 and is_violation:
                            # Save violation images first
                            try:
                                # Ensure directory exists
                                os.makedirs("media/face_detect", exist_ok=True)

                                cv2.imwrite(
                                    f"media/face_detect/output{curr_datetime}.jpg", annotated_img)
                                cv2.imwrite(
                                    "media/face_detect/output.jpg", annotated_img)
                                print(f"✅ Saved violation image for {currentClass} in live detection")
                            except Exception as write_error:
                                print(f"Warning: Failed to write output image at frame {frame_counter}: {write_error}")

                            # Detect faces for violations
                            try:
                                detectFace(currentClass, email_interval_minutes)
                            except Exception as face_error:
                                print(f"Warning: Face detection error at frame {frame_counter}: {face_error}")

                # Use the annotated image from YOLO's default plotting
                img = annotated_img

            # Resize for better performance
            img = cv2.resize(img, (640, 480))

            # Validate frame before encoding
            if img is None or img.size == 0:
                print("Warning: Frame is empty after processing, skipping...")
                continue

            # Encode frame as JPEG with error checking
            success, buffer = cv2.imencode(
                '.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])

            if not success or buffer is None or buffer.size == 0:
                print("Warning: Failed to encode frame, skipping...")
                continue

            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    finally:
        cam.release()


def run_detection():
    global detection_running
    detection_running = True
    print("Detection thread started - detection_running set to True")


@camera_dashboard_bp.route('/detection_feed')
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


@camera_dashboard_bp.route('/cameras', methods=['GET'])
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


@camera_dashboard_bp.route('/safetydetection', methods=['GET', 'POST'])
def safety():
    global detection_thread, detection_running, current_camera_id, current_camera_name, current_camera_source, email_interval_minutes

    if request.method == 'POST':
        data = request.get_json()
        camera_id = data.get('camera_id', '0')
        email_interval = data.get('email_interval_minutes', DEFAULT_EMAIL_INTERVAL_MINUTES)

        # Get camera info from config
        camera_config = CAMERA_CONFIG.get(camera_id, CAMERA_CONFIG["0"])
        camera_name = camera_config["name"]
        camera_type = camera_config["type"]

        print(
            f"Starting detection with Camera ID: {camera_id}, Name: {camera_name}, Type: {camera_type}, Email Interval: {email_interval} minutes")

        # Update global variables
        current_camera_id = camera_id
        current_camera_name = camera_name
        current_camera_source = camera_type
        email_interval_minutes = email_interval
    else:
        camera_id = current_camera_id
        camera_name = current_camera_name
        camera_type = current_camera_source

    if not detection_running:
        detection_thread = threading.Thread(target=run_detection)
        detection_thread.start()
        return jsonify({
            "message": f"Detection started using {camera_name}",
            "stream_url": url_for('camera_dashboard.detection_feed'),
            "camera_id": camera_id,
            "camera_name": camera_name,
            "camera_type": camera_type,
            "email_interval_minutes": email_interval_minutes
        })
    else:
        return jsonify({"message": "Detection already running"})


@camera_dashboard_bp.route('/stopdetection', methods=['POST'])
def stop_detection():
    global detection_running
    try:
        detection_running = False
        return jsonify({"message": "Detection stopped"})
    except Exception as e:
        # Logs the error to the console
        print(f"Error stopping detection: {e}")
        return jsonify({"message": "Failed to stop detection", "error": str(e)}), 500


@camera_dashboard_bp.route('/set_email_interval', methods=['POST'])
def set_email_interval():
    """Set email notification interval in minutes"""
    global email_interval_minutes
    try:
        data = request.get_json()
        interval = data.get('email_interval_minutes', DEFAULT_EMAIL_INTERVAL_MINUTES)
        
        if interval < DEFAULT_EMAIL_INTERVAL_MINUTES:
            return jsonify({"status": "error", "message": f"Interval must be at least {DEFAULT_EMAIL_INTERVAL_MINUTES} minutes (1 minute)"}), 400
        
        email_interval_minutes = interval
        return jsonify({
            "status": "success", 
            "message": f"Email interval set to {interval} minutes",
            "email_interval_minutes": email_interval_minutes
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to set email interval: {str(e)}"}), 500


@camera_dashboard_bp.route('/get_email_interval', methods=['GET'])
def get_email_interval():
    """Get current email notification interval"""
    global email_interval_minutes
    return jsonify({
        "email_interval_minutes": email_interval_minutes
    })


@camera_dashboard_bp.route('/demo2', methods=['POST'])
def demo2():
    global video_processing_active, current_processing_type, current_processing_video_path

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
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        sample_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], filename)

        # Save original file
        file.save(sample_path)

        # Set global processing state
        video_processing_active = True
        current_processing_type = "general"
        current_processing_video_path = sample_path
        video_processing_stop_requested = False  # Reset stop flag

        # Create output path (consider adding timestamp for uniqueness)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"output_{timestamp}_{filename}"
        output_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], output_filename)

        return jsonify({
            "status": "success",
            "video_feed_url": url_for('camera_dashboard.video_feed2', video_path=sample_path),
            "download_url": url_for('static', filename=f'uploads/{output_filename}'),
            "message": "File uploaded successfully"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Processing failed: {str(e)}"
        }), 500


@camera_dashboard_bp.route('/video_feed2')
def video_feed2():
    """Route for streaming PPE detection processed video with zone-based analysis"""
    video_path = request.args.get('video_path')
    print(f"🎥 Video feed requested for: {video_path}")
    if not video_path or not os.path.exists(video_path):
        print(f"❌ Invalid video path: {video_path}")
        return jsonify({"status": "error", "error": "Invalid video path"}), 404
    try:
        print(f"✅ Starting video stream for: {video_path}")
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
        print(f"❌ Video streaming error: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


# def generate_processed_frames2(video_path):
#     """Generator function that yields YOLO-processed frames"""
#     try:
#         cap = cv2.VideoCapture(video_path)
#         if not cap.isOpened():
#             raise ValueError("Could not open video file")
#         while True:
#             success, frame = cap.read()
#             if not success:
#                 break

#             # Process frame with YOLO (auto-draws boxes)
#             results = yolo_model(frame)
#             annotated_frame = results[0].plot()

#             # Resize for better performance
#             annotated_frame = cv2.resize(annotated_frame, (640, 480))

#             # Encode frame as JPEG
#             _, buffer = cv2.imencode('.jpg', annotated_frame,
#                                      # 80% quality
#                                      [int(cv2.IMWRITE_JPEG_QUALITY), 80])
#             frame_bytes = buffer.tobytes()

#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

#             # Adjust sleep based on actual processing speed
#             time.sleep(0.033)  # ~30fps

#     except Exception as e:
#         print(f"Streaming error: {str(e)}")
#     finally:
#         cap.release()
# line based detection

def generate_processed_frames2(video_path):
    """Generator function that yields YOLO-processed frames from a video file"""
    global video_processing_stop_requested

    print(f"🎬 Starting video processing for: {video_path}")
    print(f"📁 Video file exists: {os.path.exists(video_path)}")

    # Import violation counting functions - COMMENTED OUT
    # from services.violation_count import count_violation, reset_violation_counts

    # Reset violation counts at start - COMMENTED OUT
    # reset_violation_counts()

    # Open video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file: {video_path}")
        return

    # Get video properties for debugging
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Class names for different objects detected by the model
    '''classNames = ['Hardhat', 'Mask', 'NO-Hardhat', 'NO-Mask', 'NO-Safety Vest', 'Person', 'Safety Cone', 'Safety Vest', 'machinery', 'vehicle']'''
    classNames = [
        'Helmet',
        'Safety_Vest',
        'Safety_goggles',
        'Safety_shoes',
        'No_helmet',
        'No_Vest',
        'No_goggles',
        'No_SafetyShoes',
        'Person',
        'Safety_Gloves',
        'No_Gloves'
    ]

    try:
        frame_counter = 0
        while True:
            # Check if stop was requested
            if video_processing_stop_requested:
                print("Video processing stop requested, breaking loop")
                break

            try:
                success, img = cap.read()
                if not success:
                    print(
                        f"End of video or failed to read frame at frame {frame_counter}")
                    break

                frame_counter += 1

                # Validate frame data
                if img is None or img.size == 0:
                    print(
                        f"Warning: Empty or invalid frame detected at frame {frame_counter}, skipping...")
                    continue

                curr_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

                # Perform object detection with error handling
                # Explicitly pass ALL class indices to ensure ALL classes are detected
                # This overrides any previous class filtering from class-based detection
                try:
                    # Get all available class indices from the model to explicitly enable all classes
                    all_class_indices = list(yolo_model.names.keys())
                    # Use direct model call with explicit class list to ensure no filtering
                    results = yolo_model(img, conf=0.25, iou=0.45, classes=all_class_indices, verbose=False)
                except Exception as yolo_error:
                    print(
                        f"YOLO processing error at frame {frame_counter}: {yolo_error}")
                    # Skip this frame and continue
                    continue

                try:
                    # Process results - results is a list when using direct model call
                    # Iterate through results (usually just one result for a single image)
                    annotated_img = img
                    for r in results:
                        if r is not None:
                            # Use YOLO's built-in plot method for default visualization
                            annotated_img = r.plot()
                            break  # Use first result

                    # CLASS DETECTION ONLY - Process violations
                    # Process results to extract violation information
                    for r in results:
                        if r is None:
                            continue
                        boxes = r.boxes
                        if boxes is not None:
                            for box in boxes:
                                # Calculate confidence and class index
                                conf = math.ceil((box.conf[0] * 100)) / 100
                                cls = int(box.cls[0])
                                currentClass = yolo_model.names[cls]
                                # Check if this is a violation
                                violation_classes = [
                                    'NO_helmet', 'NO_Vest', 'NO_goggles', 'NO_SafetyShoes', 'NO_Gloves']
                                is_violation = currentClass in violation_classes

                                # Process violations only
                                if conf > 0.5 and is_violation:
                                    # Save violation images first
                                    try:
                                        # Ensure directory exists
                                        os.makedirs(
                                            "media/face_detect", exist_ok=True)

                                        cv2.imwrite(
                                            f"media/face_detect/output{curr_datetime}.jpg", annotated_img)
                                        cv2.imwrite(
                                            "media/face_detect/output.jpg", annotated_img)
                                        print(
                                            f"✅ Saved violation image for {currentClass}")
                                    except Exception as write_error:
                                        print(
                                            f"Warning: Failed to write output image at frame {frame_counter}: {write_error}")

                                    # Count violation for specific classes
                                    # count_violation(currentClass)

                                    # Detect faces for violations
                                    try:
                                        detectFace(currentClass, email_interval_minutes)
                                    except Exception as face_error:
                                        print(
                                            f"Warning: Face detection error at frame {frame_counter}: {face_error}")
                        break  # Process first result only

                    # Use the annotated image from YOLO's default plotting
                    img = annotated_img

                except Exception as results_error:
                    print(
                        f"Warning: Results processing error at frame {frame_counter}: {results_error}")
                    continue

                # Resize for better performance
                img = cv2.resize(img, (640, 480))

                # Validate frame before encoding
                if img is None or img.size == 0:
                    print(
                        f"Warning: Frame is empty after processing at frame {frame_counter}, skipping...")
                    continue

                # Encode frame as JPEG with error checking
                success, buffer = cv2.imencode(
                    '.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])

                if not success or buffer is None or buffer.size == 0:
                    print(
                        f"Warning: Failed to encode frame {frame_counter}, skipping...")
                    continue

                frame_bytes = buffer.tobytes()

                # Debug output every 30 frames
                if frame_counter % 30 == 0:
                    print(
                        f"📹 Streaming frame {frame_counter} - Size: {len(frame_bytes)} bytes")

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            except Exception as frame_error:
                print(
                    f"Frame processing error at frame {frame_counter}: {frame_error}")
                continue

    except Exception as e:
        print(f"Streaming error: {str(e)}")
    finally:
        cap.release()
        # Reset stop flag when processing completes
        video_processing_stop_requested = False


@camera_dashboard_bp.route('/demo3', methods=['POST'])
def demo3():
    global video_processing_active, current_processing_type, current_processing_video_path

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
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        sample_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], filename)

        # Save original file
        file.save(sample_path)

        # Set global processing state
        video_processing_active = True
        current_processing_type = "zone"
        current_processing_video_path = sample_path
        video_processing_stop_requested = False  # Reset stop flag

        # Create output path (consider adding timestamp for uniqueness)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"output_{timestamp}_{filename}"
        output_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], output_filename)

        return jsonify({
            "status": "success",
            "video_feed_url": url_for('camera_dashboard.video_feed3', video_path=sample_path),
            "download_url": url_for('static', filename=f'uploads/{output_filename}'),
            "message": "File uploaded successfully"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Processing failed: {str(e)}"
        }), 500


@camera_dashboard_bp.route('/video_feed3')
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


def generate_processed_frames3(video_path):
    """Generator function that yields PPE detection processed frames with zone-based analysis"""
    global video_processing_stop_requested

    try:
        # PPE Detection Configuration
        CONF_THRES = 0.25
        IOU_THRES = 0.45

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

        # Colors for zone visualization
        CLR_LINE = (255, 255, 255)

        def point_side_of_line(px, py, x1, y1, x2, y2):
            """Returns sign of cross product for vertical line: >0 = left side, <0 = right side, =0 = on the line"""
            return (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)

        # Use shared draw_label function (already defined at module level)

        while True:
            # Check if stop was requested
            if video_processing_stop_requested:
                print("Video processing stop requested, breaking loop")
                break

            success, frame = cap.read()
            if not success:
                break

            # Run YOLO detection
            results = yolo_model.predict(
                frame, conf=CONF_THRES, iou=IOU_THRES, verbose=False)
            
            # Get detection boxes for zone-based analysis
            annotated = frame.copy()
            dets = results[0].boxes
            if dets is not None and dets.shape[0] > 0:
                for i in range(len(dets)):
                    xyxy = dets.xyxy[i].cpu().tolist()
                    cls = int(dets.cls[i].cpu().item())
                    conf = float(dets.conf[i].cpu().item())
                    class_name = yolo_model.names.get(cls, str(cls))
                    
                    px1, py1, px2, py2 = [int(coord) for coord in xyxy]
                    
                    # Zone-based analysis for person detections
                    if class_name.lower() == "person":
                        # Calculate person center
                        pcx, pcy = (px1 + px2) / 2, (py1 + py2) / 2
                        
                        # Determine which zone the person is in
                        sign = point_side_of_line(pcx, pcy, x1, y1, x2, y2)
                        zone = zone_names[0] if sign > 0 else zone_names[1] if sign < 0 else "ON_LINE"
                        
                        # If person is on RIGHT zone, just show OK - no detection needed
                        if zone == zone_names[1]:  # RIGHT zone
                            cv2.rectangle(annotated, (px1, py1), (px2, py2), (0, 255, 0), 2)
                            draw_label(annotated, "OK", px1, py1 - 10,
                                       color=(255, 255, 255), bg=(0, 255, 0))
                        else:
                            # Person is on LEFT zone - do normal detection
                            cv2.rectangle(annotated, (px1, py1), (px2, py2), (0, 255, 0), 2)
                            cv2.putText(annotated, f"{class_name} {conf:.2f}", (px1, py1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                            # Add zone information overlay
                            label = f"Zone: {zone}"
                            draw_label(annotated, label, px1, py1 - 30,
                                       color=(255, 255, 255), bg=(0, 0, 255))
                    else:
                        # For non-person detections, only process if in LEFT zone
                        # Calculate detection center for zone check
                        dcx, dcy = (px1 + px2) / 2, (py1 + py2) / 2
                        sign = point_side_of_line(dcx, dcy, x1, y1, x2, y2)
                        zone = zone_names[0] if sign > 0 else zone_names[1] if sign < 0 else "ON_LINE"
                        
                        # Only show detections and check violations in LEFT zone
                        if zone == zone_names[0] or sign == 0:  # LEFT zone or on line
                            cv2.rectangle(annotated, (px1, py1), (px2, py2), (0, 255, 0), 2)
                            cv2.putText(annotated, f"{class_name} {conf:.2f}", (px1, py1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                            
                            # Save violation images for specific classes (only in LEFT zone)
                            if conf > 0.5 and class_name in ['NO_helmet', 'NO_Vest', 'NO_goggles', 'NO_safetyshoes']:
                                curr_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                                cv2.imwrite(f"media/zone_based/output_{curr_datetime}.jpg", annotated)
                                cv2.imwrite("media/zone_based/output.jpg", annotated)

            # Draw divider line
            cv2.line(annotated, (int(x1), int(y1)),
                     (int(x2), int(y2)), CLR_LINE, 2)
            draw_label(annotated, f"AUTO DIVIDER (VERTICAL)", int((x1 + x2) / 2), int((y1 + y2) / 2) - 6,
                       color=(0, 0, 0), bg=(255, 255, 255))

            # HUD info
            cv2.putText(annotated, f"Zone Analysis: {zone_names[0]} / {zone_names[1]}", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

            # Resize only if frame is very large (to maintain quality while ensuring performance)
            # If original is larger than 1920x1080, resize to 1920x1080 maintaining aspect ratio
            if annotated.shape[1] > 1920 or annotated.shape[0] > 1080:
                scale = min(1920 / annotated.shape[1], 1080 / annotated.shape[0])
                new_width = int(annotated.shape[1] * scale)
                new_height = int(annotated.shape[0] * scale)
                annotated = cv2.resize(annotated, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

            # Encode frame as JPEG with high quality
            _, buffer = cv2.imencode('.jpg', annotated,
                                     [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            # Adjust sleep based on actual processing speed
            time.sleep(0.033)  # ~30fps

    except Exception as e:
        print(f"Streaming error: {str(e)}")
    finally:
        cap.release()
        # Reset stop flag when processing completes
        video_processing_stop_requested = False

# def generate_processed_framesX(video_path):
#     """Generator function that yields PPE detection processed frames with zone-based analysis"""
#     global video_processing_stop_requested
    
#     try:
#         # PPE Detection Configuration
#         CONF_THRES = 0.25
#         IOU_THRES = 0.45

#         cap = cv2.VideoCapture(video_path)
#         if not cap.isOpened():
#             raise ValueError("Could not open video file")

#         # Calculate the video width and height
#         W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#         H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

#         # Set vertical divider
#         x_mid = W // 2
#         divider = [x_mid, 0, x_mid, H - 1]
#         zone_names = ("LEFT", "RIGHT")
#         x1, y1, x2, y2 = divider

#         # Colors for zone visualization
#         CLR_LINE = (255, 255, 255)

#         def point_side_of_line(px, py, x1, y1, x2, y2):
#             """Returns sign of cross product for vertical line: >0 = left side, <0 = right side, =0 = on the line"""
#             return (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)

#         def draw_label(img, text, x, y, color=(255, 255, 255), bg=(0, 0, 0)):
#             (tw, th), base = cv2.getTextSize(
#                 text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
#             cv2.rectangle(img, (x, y - th - 6), (x + tw + 6, y + 2), bg, -1)
#             cv2.putText(img, text, (x + 3, y - 6),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

#         while True:
#             # Check if stop was requested
#             if video_processing_stop_requested:
#                 print("Video processing stop requested, breaking loop")
#                 break
                
#             success, frame = cap.read()
#             if not success:
#                 break

#             # Run YOLO detection with default visualization
#             results = yolo_model.predict(
#                 frame, conf=CONF_THRES, iou=IOU_THRES, verbose=False)
            
#             # Use YOLO's default plotting for detection visualization
#             annotated = results[0].plot()
            
#             # CLASS DETECTION ONLY - Comment out other functionalities
#             # Add zone-based analysis overlay - COMMENTED OUT
#             # dets = results[0].boxes
#             # if dets is not None and dets.shape[0] > 0:
#             #     for i in range(len(dets)):
#             #         xyxy = dets.xyxy[i].cpu().tolist()
#             #         cls = int(dets.cls[i].cpu().item())
#             #         conf = float(dets.conf[i].cpu().item())
#             #         class_name = yolo_model.names.get(cls, str(cls))
                    
#             #         # Check if it's a person for zone analysis - COMMENTED OUT
#             #         if class_name.lower() == "person":
#             #             # Calculate person center
#             #             px1, py1, px2, py2 = xyxy
#             #             pcx, pcy = (px1 + px2) / 2, (py1 + py2) / 2
                        
#             #             # Determine which zone the person is in
#             #             sign = point_side_of_line(pcx, pcy, x1, y1, x2, y2)
#             #             zone = zone_names[0] if sign > 0 else zone_names[1] if sign < 0 else "ON_LINE"
                        
#             #             # Add zone information overlay
#             #             label = f"Zone: {zone}"
#             #             draw_label(annotated, label, int(px1), int(py1) - 20,
#             #                        color=(255, 255, 255), bg=(0, 0, 0))
                    
#             #         # Detect faces for violations - COMMENTED OUT
#             #         detectFace(class_name)
                    
#             #         # Save violation images for specific classes - COMMENTED OUT
#             #         if conf > 0.5 and class_name in ['NO_helmet', 'NO_Vest', 'NO_goggles', 'NO_safetyshoes']:
#             #             curr_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#             #             cv2.imwrite(f"media/zone_based/output_{curr_datetime}.jpg", annotated)
#             #             cv2.imwrite("media/zone_based/output.jpg", annotated)

#             # Draw divider line
#             cv2.line(annotated, (int(x1), int(y1)),
#                      (int(x2), int(y2)), CLR_LINE, 2)
#             draw_label(annotated, f"AUTO DIVIDER (VERTICAL)", int((x1 + x2) / 2), int((y1 + y2) / 2) - 6,
#                        color=(0, 0, 0), bg=(255, 255, 255))

#             # HUD info
#             cv2.putText(annotated, f"Zone Analysis: {zone_names[0]} / {zone_names[1]}", (10, 20),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

#             # Resize only if frame is very large (to maintain quality while ensuring performance)
#             # If original is larger than 1920x1080, resize to 1920x1080 maintaining aspect ratio
#             if annotated.shape[1] > 1920 or annotated.shape[0] > 1080:
#                 scale = min(1920 / annotated.shape[1], 1080 / annotated.shape[0])
#                 new_width = int(annotated.shape[1] * scale)
#                 new_height = int(annotated.shape[0] * scale)
#                 annotated = cv2.resize(annotated, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

#             # Encode frame as JPEG with high quality
#             _, buffer = cv2.imencode('.jpg', annotated,
#                                      [int(cv2.IMWRITE_JPEG_QUALITY), 95])
#             frame_bytes = buffer.tobytes()

#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

#             # Adjust sleep based on actual processing speed
#             time.sleep(0.033)  # ~30fps

#     except Exception as e:
#         print(f"Streaming error: {str(e)}")
#     finally:
#         cap.release()
#         # Reset stop flag when processing completes
#         video_processing_stop_requested = False
        
@camera_dashboard_bp.route('/demo4', methods=['POST'])
def demo4():
    """Class-based PPE detection route"""
    global video_processing_active, current_processing_type, current_processing_video_path

    if 'file' not in request.files:
        return jsonify({"status": "error", "error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "error": "No selected file"}), 400

    if not (file and allowed_file(file.filename)):
        return jsonify({"status": "error", "error": "Invalid file type"}), 400

    # Get classes from request - STRICT: no default classes
    classes_json = request.form.get('classes', '[]')
    try:
        selected_classes = json.loads(classes_json)
        # Ensure it's a list and filter out empty strings
        if not isinstance(selected_classes, list):
            selected_classes = []
        selected_classes = [cls for cls in selected_classes if cls and cls.strip()]
    except json.JSONDecodeError as e:
        # STRICT: If JSON parsing fails, use empty list (zero default behavior)
        selected_classes = []

    try:
        # Secure filename and create upload directory
        if file.filename is None:
            return jsonify({"status": "error", "error": "No filename provided"}), 400
        filename = secure_filename(file.filename)
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        sample_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], filename)

        # Save original file
        file.save(sample_path)

        # Set global processing state
        video_processing_active = True
        current_processing_type = "class"
        current_processing_video_path = sample_path
        video_processing_stop_requested = False  # Reset stop flag

        # Create output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"output_{timestamp}_{filename}"
        output_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], output_filename)

        # Store the selected classes in the app context
        camera_dashboard_bp.class_based_classes = selected_classes

        video_feed_url = url_for(
            'camera_dashboard.video_feed4', video_path=sample_path)

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


@camera_dashboard_bp.route('/video_feed4')
def video_feed4():
    """Route for streaming class-based PPE detection processed video"""
    video_path = request.args.get('video_path')

    if not video_path or not os.path.exists(video_path):
        return jsonify({"status": "error", "error": "Invalid video path"}), 404

    try:
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
        return jsonify({"status": "error", "error": str(e)}), 500


def generate_processed_frames4(video_path):
    """Generator function for class-based PPE detection - strict selection-based filtering"""
    global video_processing_stop_requested

    cap = None
    try:
        # Get the selected classes from app context
        selected_classes = getattr(camera_dashboard_bp, 'class_based_classes', [])

        # Class name aliases from reference.py - source of truth
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
            "no_safety_shoes": {"no_shoes", "NO_safetyshoes", "no_boots", "no_safety_shoes", "No_SafetyShoes"},
            "no_goggles": {"no_goggles", "NO_goggles", "no_eye_protection", "no_safety_goggles"},
            "Safety_Gloves": {"Safety_Gloves", "Gloves"},
            "No_Gloves": {"No_Gloves", "NO_Gloves", "No_Safety_Gloves"},
        }

        def canonicalize(name: str) -> str:
            """Converts a class name to its canonical form using the ALIASES map - from reference.py"""
            n = name.lower().replace(" ", "_")
            for canon, synonyms in ALIASES.items():
                canon_lower = canon.lower()
                synonyms_lower = {s.lower() for s in synonyms}
                if n == canon_lower or n in synonyms_lower:
                    return canon
            return n

        def center_of_box(xyxy):
            """Calculate center point of bounding box - from reference.py"""
            x1, y1, x2, y2 = xyxy
            return (int((x1 + x2) / 2), int((y1 + y2) / 2))

        def inside_bbox(point, bbox):
            """Check if point is inside bounding box - from reference.py"""
            px, py = point
            x1, y1, x2, y2 = bbox
            return x1 <= px <= x2 and y1 <= py <= y2

        def violation_indicates_missing_ppe(violation_name, required_item):
            """Check if a violation class name indicates missing required PPE"""
            violation_lower = violation_name.lower()
            required_lower = required_item.lower()
            
            # Standard "no_X" format check
            if violation_name.startswith("no_") or violation_name.startswith("No_") or violation_name.startswith("NO_"):
                # Extract base name after "no_" prefix
                if violation_name.startswith("no_"):
                    base = violation_name[3:]
                elif violation_name.startswith("No_"):
                    base = violation_name[3:]
                elif violation_name.startswith("NO_"):
                    base = violation_name[3:]
                else:
                    base = violation_name
                
                # Check if base matches required item (case-insensitive)
                if base.lower() == required_lower:
                    return True
                
                # Handle special mappings
                if violation_name == "No_Gloves" and required_item == "Safety_Gloves":
                    return True
                if violation_name == "no_gloves" and required_item == "Safety_Gloves":
                    return True
            
            # Check if violation name contains required item name (for edge cases)
            if required_lower in violation_lower and ("no" in violation_lower or violation_name.startswith("No") or violation_name.startswith("NO")):
                return True
            
            return False

        # Determine required PPE types from selected classes
        # If no classes selected: show ALL violations
        # If classes selected: show only violations for those classes
        required_ppe = set()
        detect_classes_names = set()
        violation_classes_to_show = set()  # Track which violation classes to display

        if not selected_classes or len(selected_classes) == 0:
            # No classes selected: Show ALL violations
            print("No classes selected - showing ALL violations")
            # Detect all classes (we'll filter to show only violations)
            # Add person for tracking
            detect_classes_names.add("person")
            # Detect all violation classes from the model
            for idx, name in yolo_model.names.items():
                canon_name = canonicalize(name)
                # Include all "no_" violation classes
                if (canon_name.startswith("no_") or canon_name.startswith("No_") or 
                    canon_name.startswith("NO_")):
                    detect_classes_names.add(canon_name)
                    violation_classes_to_show.add(canon_name)
                # Also include positive PPE classes to properly associate violations with persons
                elif canon_name in ["helmet", "safety_vest", "pvc_suit", "shoes", "goggles", "Safety_Gloves"]:
                    detect_classes_names.add(canon_name)
        else:
            # Classes selected: Show only violations for selected classes
            print(f"Classes selected: {selected_classes} - showing only violations for these classes")
            # Process selected classes to determine required PPE
            user_ppe_types = set()
            for cls_name in selected_classes:
                canon_name = canonicalize(cls_name)
                if canon_name.startswith("no_"):
                    user_ppe_types.add(canon_name[3:])
                else:
                    user_ppe_types.add(canon_name)

            required_ppe = user_ppe_types

            # Build detection class names: include PPE types, their "no_" versions, and person
            for ppe_type in required_ppe:
                detect_classes_names.add(ppe_type)
                violation_class = f"no_{ppe_type}"
                detect_classes_names.add(violation_class)
                violation_classes_to_show.add(violation_class)
                # Handle special case for gloves
                if ppe_type == "Safety_Gloves":
                    violation_classes_to_show.add("No_Gloves")
                    detect_classes_names.add("No_Gloves")
            detect_classes_names.add("person")

        # Map class names to model indices
        detect_class_indices = []
        model_class_map = {canonicalize(name): idx for idx, name in yolo_model.names.items()}
        for name in detect_classes_names:
            if name in model_class_map:
                detect_class_indices.append(model_class_map[name])

        if not selected_classes or len(selected_classes) == 0:
            print(f"No classes selected - will show ALL violations")
        else:
            print(f"Selected classes: {selected_classes}")
            print(f"Required PPE: {required_ppe}")
        print(f"Detection classes: {detect_classes_names}")
        print(f"Violation classes to show: {violation_classes_to_show}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Could not open video file")

        # Colors from reference.py
        CLR_OK = (0, 200, 0)
        CLR_MISS = (0, 0, 255)

        frame_count = 0
        consecutive_errors = 0
        max_consecutive_errors = 5

        while True:
            try:
                # Check if stop was requested
                if video_processing_stop_requested:
                    break

                success, frame = cap.read()
                if not success:
                    break

                frame_count += 1
                consecutive_errors = 0

                # Run YOLO detection with selected classes only
                results = yolo_model.predict(
                    frame,
                    conf=0.3,
                    iou=0.5,
                    classes=detect_class_indices,
                    verbose=False
                )

                dets = results[0].boxes
                persons = []
                ppe_items = []

                # Separate persons and PPE items (following reference.py logic)
                if dets is not None and len(dets) > 0:
                    for i in range(len(dets)):
                        xyxy = dets.xyxy[i].cpu().tolist()
                        cls_id = int(dets.cls[i].cpu().item())
                        conf = float(dets.conf[i].cpu().item())
                        class_name = canonicalize(yolo_model.names.get(cls_id, ""))

                        if class_name == "person":
                            persons.append({"bbox": xyxy, "conf": conf})
                        else:
                            # Include all PPE items and violations (we'll filter during display)
                            if conf >= 0.3:  # Confidence threshold from reference
                                ppe_items.append({"center": center_of_box(xyxy), "name": class_name, "bbox": xyxy})

                # Create annotated frame - start with original
                annotated_frame = frame.copy()

                # Process each person and check for violations
                for person_idx, person in enumerate(persons):
                    px1, py1, px2, py2 = [int(coord) for coord in person["bbox"]]
                    person_bbox = [px1, py1, px2, py2]

                    # Find PPE items and violations associated with this person
                    owned_items = {item["name"] for item in ppe_items if inside_bbox(item["center"], person_bbox)}
                    
                    # Check which violations this person has
                    person_violations = set()
                    
                    if not selected_classes or len(selected_classes) == 0:
                        # No classes selected: Show ALL violations found (negative classes only)
                        for item_name in owned_items:
                            # Check if it's a violation class (negative class - starts with "no_", "No_", or "NO_")
                            canon_item = canonicalize(item_name)
                            if (canon_item.startswith("no_") or canon_item.startswith("No_") or 
                                canon_item.startswith("NO_")):
                                # Add the violation name
                                person_violations.add(canon_item)
                    else:
                        # Classes selected: Only show violations for selected classes
                        for required_item in required_ppe:
                            # Check for violation indicators
                            violation_found = False
                            
                            # Check standard "no_X" format
                            violation_class = f"no_{required_item}"
                            if violation_class in owned_items:
                                person_violations.add(required_item)
                                violation_found = True
                            else:
                                # Check all violation classes in owned_items for matches
                                for violation_name in owned_items:
                                    if violation_indicates_missing_ppe(violation_name, required_item):
                                        person_violations.add(required_item)
                                        violation_found = True
                                        break
                            
                            # Also check if we explicitly detected a "no_X" violation
                            if not violation_found:
                                # Check if any violation class matches
                                for item_name in owned_items:
                                    if violation_indicates_missing_ppe(item_name, required_item):
                                        person_violations.add(required_item)
                                        break

                    # Only show persons with violations (negative classes only)
                    if person_violations:
                        # This person has violations - draw them using shared function
                        annotated_frame = draw_violation_box(
                            annotated_frame, 
                            person["bbox"], 
                            person_violations, 
                            person_idx=person_idx + 1,
                            color=CLR_MISS
                        )

                # Resize for better performance
                annotated_frame = cv2.resize(annotated_frame, (640, 480))

                # Encode frame as JPEG
                _, buffer = cv2.imencode(
                    '.jpg', annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                frame_bytes = buffer.tobytes()

                if frame_count % 30 == 0:
                    print(f"Frame {frame_count}: Processed {len(persons)} persons, {len(ppe_items)} PPE items")

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

                # Adjust sleep based on actual processing speed
                time.sleep(0.033)  # ~30fps

            except Exception as frame_error:
                consecutive_errors += 1
                print(f"Frame processing error: {frame_error}")
                if consecutive_errors >= max_consecutive_errors:
                    break
                continue

    except Exception as e:
        print(f"Class-based detection streaming error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if cap is not None:
            cap.release()
        # Reset stop flag when processing completes
        video_processing_stop_requested = False


@camera_dashboard_bp.route('/stop_video_processing', methods=['POST'])
def stop_video_processing():
    """Stop video processing and reset global state"""
    global video_processing_active, current_processing_type, current_processing_video_path, video_processing_stop_requested

    try:
        # Set stop flag to signal processing functions to stop
        video_processing_stop_requested = True

        # Reset global processing state
        video_processing_active = False
        current_processing_type = None
        current_processing_video_path = None

        return jsonify({
            "status": "success",
            "message": "Video processing stopped successfully"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Failed to stop video processing",
            "error": str(e)
        }), 500


@camera_dashboard_bp.route('/video_processing_status', methods=['GET'])
def get_video_processing_status():
    """Get current video processing status"""
    global video_processing_active, current_processing_type, current_processing_video_path, video_processing_stop_requested

    return jsonify({
        "processing_active": video_processing_active,
        "processing_type": current_processing_type,
        "video_path": current_processing_video_path,
        "stop_requested": video_processing_stop_requested
    })


def generate_class_based_detection_frames():
    """Generator function that yields class-based YOLO-processed frames from camera for HTTP streaming"""
    global class_based_live_detection_running, class_based_selected_classes, class_based_camera_id, email_interval_minutes
    
    # Class name aliases from reference.py - source of truth
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
        "no_safety_shoes": {"no_shoes", "NO_safetyshoes", "no_boots", "no_safety_shoes", "No_SafetyShoes"},
        "no_goggles": {"no_goggles", "NO_goggles", "no_eye_protection", "no_safety_goggles"},
        "Safety_Gloves": {"Safety_Gloves", "Gloves"},
        "No_Gloves": {"No_Gloves", "NO_Gloves", "No_Safety_Gloves"},
    }

    def canonicalize(name: str) -> str:
        """Converts a class name to its canonical form using the ALIASES map"""
        n = name.lower().replace(" ", "_")
        for canon, synonyms in ALIASES.items():
            canon_lower = canon.lower()
            synonyms_lower = {s.lower() for s in synonyms}
            if n == canon_lower or n in synonyms_lower:
                return canon
        return n

    def center_of_box(xyxy):
        """Calculate center point of bounding box"""
        x1, y1, x2, y2 = xyxy
        return (int((x1 + x2) / 2), int((y1 + y2) / 2))

    def inside_bbox(point, bbox):
        """Check if point is inside bounding box"""
        px, py = point
        x1, y1, x2, y2 = bbox
        return x1 <= px <= x2 and y1 <= py <= y2

    def violation_indicates_missing_ppe(violation_name, required_item):
        """Check if a violation class name indicates missing required PPE"""
        violation_lower = violation_name.lower()
        required_lower = required_item.lower()
        
        # Standard "no_X" format check
        if violation_name.startswith("no_") or violation_name.startswith("No_") or violation_name.startswith("NO_"):
            # Extract base name after "no_" prefix
            if violation_name.startswith("no_"):
                base = violation_name[3:]
            elif violation_name.startswith("No_"):
                base = violation_name[3:]
            elif violation_name.startswith("NO_"):
                base = violation_name[3:]
            else:
                base = violation_name
            
            # Check if base matches required item (case-insensitive)
            if base.lower() == required_lower:
                return True
            
            # Handle special mappings
            if violation_name == "No_Gloves" and required_item == "Safety_Gloves":
                return True
            if violation_name == "no_gloves" and required_item == "Safety_Gloves":
                return True
        
        # Check if violation name contains required item name (for edge cases)
        if required_lower in violation_lower and ("no" in violation_lower or violation_name.startswith("No") or violation_name.startswith("NO")):
            return True
        
        return False

    # Get camera configuration
    camera_config = CAMERA_CONFIG.get(class_based_camera_id, CAMERA_CONFIG["0"])
    camera_name = camera_config["name"]
    camera_type = camera_config["type"]
    camera_url = camera_config["url"]

    print(f"🎥 Starting class-based live detection (HTTP streaming)")
    print(f"   Camera: {camera_name} (ID: {class_based_camera_id}, Type: {camera_type})")
    print(f"   Selected classes: {class_based_selected_classes}")

    # Open camera based on type
    if camera_type == 'rtsp' and camera_url:
        print(f"Opening RTSP camera: {camera_url}")
        cam = cv2.VideoCapture(camera_url)
    elif camera_type == 'laptop':
        print(f"Opening laptop camera (index 0)")
        cam = cv2.VideoCapture(0)
    else:
        print(f"Opening camera with index: {class_based_camera_id}")
        cam = cv2.VideoCapture(int(class_based_camera_id))

    if not cam.isOpened():
        print(f"❌ Error: Could not open camera {camera_name}")
        return

    # Determine required PPE types from selected classes
    required_ppe = set()
    detect_classes_names = set()
    violation_classes_to_show = set()

    if not class_based_selected_classes or len(class_based_selected_classes) == 0:
        # No classes selected: Show ALL violations
        print("No classes selected - showing ALL violations")
        detect_classes_names.add("person")
        # Detect all violation classes from the model
        for idx, name in yolo_model.names.items():
            canon_name = canonicalize(name)
            # Include all "no_" violation classes
            if (canon_name.startswith("no_") or canon_name.startswith("No_") or 
                canon_name.startswith("NO_")):
                detect_classes_names.add(canon_name)
                violation_classes_to_show.add(canon_name)
            # Also include positive PPE classes to properly associate violations with persons
            elif canon_name in ["helmet", "safety_vest", "pvc_suit", "shoes", "goggles", "Safety_Gloves"]:
                detect_classes_names.add(canon_name)
    else:
        # Classes selected: Show only violations for selected classes
        print(f"Classes selected: {class_based_selected_classes} - showing only violations for these classes")
        # Process selected classes to determine required PPE
        user_ppe_types = set()
        for cls_name in class_based_selected_classes:
            canon_name = canonicalize(cls_name)
            if canon_name.startswith("no_"):
                user_ppe_types.add(canon_name[3:])
            else:
                user_ppe_types.add(canon_name)

        required_ppe = user_ppe_types

        # Build detection class names: include PPE types, their "no_" versions, and person
        for ppe_type in required_ppe:
            detect_classes_names.add(ppe_type)
            violation_class = f"no_{ppe_type}"
            detect_classes_names.add(violation_class)
            violation_classes_to_show.add(violation_class)
            # Handle special case for gloves
            if ppe_type == "Safety_Gloves":
                violation_classes_to_show.add("No_Gloves")
                detect_classes_names.add("No_Gloves")
        detect_classes_names.add("person")

    # Map class names to model indices
    detect_class_indices = []
    model_class_map = {canonicalize(name): idx for idx, name in yolo_model.names.items()}
    for name in detect_classes_names:
        if name in model_class_map:
            detect_class_indices.append(model_class_map[name])

    print(f"Detection classes: {detect_classes_names}")
    print(f"Violation classes to show: {violation_classes_to_show}")

    # Colors from reference.py
    CLR_OK = (0, 200, 0)
    CLR_MISS = (0, 0, 255)

    frame_count = 0

    try:
        while class_based_live_detection_running:
            success, frame = cam.read()
            if not success:
                print("Failed to read frame from camera")
                break

            frame_count += 1
            curr_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            # Run YOLO detection with selected classes only
            results = yolo_model.predict(
                frame,
                conf=0.3,
                iou=0.5,
                classes=detect_class_indices,
                verbose=False
            )

            dets = results[0].boxes
            persons = []
            ppe_items = []

            # Separate persons and PPE items
            if dets is not None and len(dets) > 0:
                for i in range(len(dets)):
                    xyxy = dets.xyxy[i].cpu().tolist()
                    cls_id = int(dets.cls[i].cpu().item())
                    conf = float(dets.conf[i].cpu().item())
                    class_name = canonicalize(yolo_model.names.get(cls_id, ""))

                    if class_name == "person":
                        persons.append({"bbox": xyxy, "conf": conf})
                    else:
                        # Include all PPE items and violations
                        if conf >= 0.3:
                            ppe_items.append({"center": center_of_box(xyxy), "name": class_name, "bbox": xyxy})

            # Create annotated frame - start with original
            annotated_frame = frame.copy()

            # Process each person and check for violations
            for person_idx, person in enumerate(persons):
                px1, py1, px2, py2 = [int(coord) for coord in person["bbox"]]
                person_bbox = [px1, py1, px2, py2]

                # Find PPE items and violations associated with this person
                owned_items = {item["name"] for item in ppe_items if inside_bbox(item["center"], person_bbox)}
                
                # Check which violations this person has
                person_violations = set()
                
                if not class_based_selected_classes or len(class_based_selected_classes) == 0:
                    # No classes selected: Show ALL violations found (negative classes only)
                    for item_name in owned_items:
                        # Check if it's a violation class (negative class - starts with "no_", "No_", or "NO_")
                        canon_item = canonicalize(item_name)
                        if (canon_item.startswith("no_") or canon_item.startswith("No_") or 
                            canon_item.startswith("NO_")):
                            # Add the violation name
                            person_violations.add(canon_item)
                else:
                    # Classes selected: Only show violations for selected classes
                    for required_item in required_ppe:
                        # Check for violation indicators
                        violation_found = False
                        
                        # Check standard "no_X" format
                        violation_class = f"no_{required_item}"
                        if violation_class in owned_items:
                            person_violations.add(required_item)
                            violation_found = True
                        else:
                            # Check all violation classes in owned_items for matches
                            for violation_name in owned_items:
                                if violation_indicates_missing_ppe(violation_name, required_item):
                                    person_violations.add(required_item)
                                    violation_found = True
                                    break
                        
                        # Also check if we explicitly detected a "no_X" violation
                        if not violation_found:
                            # Check if any violation class matches
                            for item_name in owned_items:
                                if violation_indicates_missing_ppe(item_name, required_item):
                                    person_violations.add(required_item)
                                    break

                # Only show persons with violations (negative classes only)
                if person_violations:
                    # This person has violations - draw them using shared function
                    annotated_frame = draw_violation_box(
                        annotated_frame, 
                        person["bbox"], 
                        person_violations, 
                        person_idx=person_idx + 1,
                        color=CLR_MISS
                    )

                    # Process violations for face detection and saving
                    for violation_name in person_violations:
                        try:
                            # Ensure directory exists
                            os.makedirs("media/face_detect", exist_ok=True)
                            cv2.imwrite(f"media/face_detect/output{curr_datetime}.jpg", annotated_frame)
                            cv2.imwrite("media/face_detect/output.jpg", annotated_frame)
                            print(f"✅ Saved violation image for {violation_name} in class-based live detection")
                            
                            # Detect faces for violations
                            detectFace(violation_name, email_interval_minutes)
                        except Exception as face_error:
                            print(f"Warning: Face detection error at frame {frame_count}: {face_error}")

            # Add camera info overlay
            info_text = f"Camera: {camera_name} | Frame: {frame_count}"
            cv2.putText(annotated_frame, info_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Add classes info
            if class_based_selected_classes:
                classes_text = f"Detecting: {', '.join(class_based_selected_classes)}"
            else:
                classes_text = "Detecting: ALL violations"
            cv2.putText(annotated_frame, classes_text, (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            # Resize for better performance
            annotated_frame = cv2.resize(annotated_frame, (640, 480))

            # Validate frame before encoding
            if annotated_frame is None or annotated_frame.size == 0:
                print("Warning: Frame is empty after processing, skipping...")
                continue

            # Encode frame as JPEG with error checking
            success, buffer = cv2.imencode(
                '.jpg', annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])

            if not success or buffer is None or buffer.size == 0:
                print("Warning: Failed to encode frame, skipping...")
                continue

            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    except Exception as e:
        print(f"❌ Error in class-based live detection streaming: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cam.release()
        print("✅ Class-based live detection streaming stopped")


def run_class_based_live_detection():
    """Run class-based live detection with cv2.imshow display (kept for backward compatibility)"""
    global class_based_live_detection_running, class_based_selected_classes, class_based_camera_id
    
    # Class name aliases from reference.py - source of truth
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
        "no_safety_shoes": {"no_shoes", "NO_safetyshoes", "no_boots", "no_safety_shoes", "No_SafetyShoes"},
        "no_goggles": {"no_goggles", "NO_goggles", "no_eye_protection", "no_safety_goggles"},
        "Safety_Gloves": {"Safety_Gloves", "Gloves"},
        "No_Gloves": {"No_Gloves", "NO_Gloves", "No_Safety_Gloves"},
    }

    def canonicalize(name: str) -> str:
        """Converts a class name to its canonical form using the ALIASES map"""
        n = name.lower().replace(" ", "_")
        for canon, synonyms in ALIASES.items():
            canon_lower = canon.lower()
            synonyms_lower = {s.lower() for s in synonyms}
            if n == canon_lower or n in synonyms_lower:
                return canon
        return n

    def center_of_box(xyxy):
        """Calculate center point of bounding box"""
        x1, y1, x2, y2 = xyxy
        return (int((x1 + x2) / 2), int((y1 + y2) / 2))

    def inside_bbox(point, bbox):
        """Check if point is inside bounding box"""
        px, py = point
        x1, y1, x2, y2 = bbox
        return x1 <= px <= x2 and y1 <= py <= y2

    def violation_indicates_missing_ppe(violation_name, required_item):
        """Check if a violation class name indicates missing required PPE"""
        violation_lower = violation_name.lower()
        required_lower = required_item.lower()
        
        # Standard "no_X" format check
        if violation_name.startswith("no_") or violation_name.startswith("No_") or violation_name.startswith("NO_"):
            # Extract base name after "no_" prefix
            if violation_name.startswith("no_"):
                base = violation_name[3:]
            elif violation_name.startswith("No_"):
                base = violation_name[3:]
            elif violation_name.startswith("NO_"):
                base = violation_name[3:]
            else:
                base = violation_name
            
            # Check if base matches required item (case-insensitive)
            if base.lower() == required_lower:
                return True
            
            # Handle special mappings
            if violation_name == "No_Gloves" and required_item == "Safety_Gloves":
                return True
            if violation_name == "no_gloves" and required_item == "Safety_Gloves":
                return True
        
        # Check if violation name contains required item name (for edge cases)
        if required_lower in violation_lower and ("no" in violation_lower or violation_name.startswith("No") or violation_name.startswith("NO")):
            return True
        
        return False

    # Get camera configuration
    camera_config = CAMERA_CONFIG.get(class_based_camera_id, CAMERA_CONFIG["0"])
    camera_name = camera_config["name"]
    camera_type = camera_config["type"]
    camera_url = camera_config["url"]

    print(f"🎥 Starting class-based live detection")
    print(f"   Camera: {camera_name} (ID: {class_based_camera_id}, Type: {camera_type})")
    print(f"   Selected classes: {class_based_selected_classes}")

    # Open camera based on type
    if camera_type == 'rtsp' and camera_url:
        print(f"Opening RTSP camera: {camera_url}")
        cam = cv2.VideoCapture(camera_url)
    elif camera_type == 'laptop':
        print(f"Opening laptop camera (index 0)")
        cam = cv2.VideoCapture(0)
    else:
        print(f"Opening camera with index: {class_based_camera_id}")
        cam = cv2.VideoCapture(int(class_based_camera_id))

    if not cam.isOpened():
        print(f"❌ Error: Could not open camera {camera_name}")
        class_based_live_detection_running = False
        return

    # Determine required PPE types from selected classes
    required_ppe = set()
    detect_classes_names = set()
    violation_classes_to_show = set()

    if not class_based_selected_classes or len(class_based_selected_classes) == 0:
        # No classes selected: Show ALL violations
        print("No classes selected - showing ALL violations")
        detect_classes_names.add("person")
        # Detect all violation classes from the model
        for idx, name in yolo_model.names.items():
            canon_name = canonicalize(name)
            # Include all "no_" violation classes
            if (canon_name.startswith("no_") or canon_name.startswith("No_") or 
                canon_name.startswith("NO_")):
                detect_classes_names.add(canon_name)
                violation_classes_to_show.add(canon_name)
            # Also include positive PPE classes to properly associate violations with persons
            elif canon_name in ["helmet", "safety_vest", "pvc_suit", "shoes", "goggles", "Safety_Gloves"]:
                detect_classes_names.add(canon_name)
    else:
        # Classes selected: Show only violations for selected classes
        print(f"Classes selected: {class_based_selected_classes} - showing only violations for these classes")
        # Process selected classes to determine required PPE
        user_ppe_types = set()
        for cls_name in class_based_selected_classes:
            canon_name = canonicalize(cls_name)
            if canon_name.startswith("no_"):
                user_ppe_types.add(canon_name[3:])
            else:
                user_ppe_types.add(canon_name)

        required_ppe = user_ppe_types

        # Build detection class names: include PPE types, their "no_" versions, and person
        for ppe_type in required_ppe:
            detect_classes_names.add(ppe_type)
            violation_class = f"no_{ppe_type}"
            detect_classes_names.add(violation_class)
            violation_classes_to_show.add(violation_class)
            # Handle special case for gloves
            if ppe_type == "Safety_Gloves":
                violation_classes_to_show.add("No_Gloves")
                detect_classes_names.add("No_Gloves")
        detect_classes_names.add("person")

    # Map class names to model indices
    detect_class_indices = []
    model_class_map = {canonicalize(name): idx for idx, name in yolo_model.names.items()}
    for name in detect_classes_names:
        if name in model_class_map:
            detect_class_indices.append(model_class_map[name])

    print(f"Detection classes: {detect_classes_names}")
    print(f"Violation classes to show: {violation_classes_to_show}")

    # Colors from reference.py
    CLR_OK = (0, 200, 0)
    CLR_MISS = (0, 0, 255)

    frame_count = 0
    window_name = f"Class-Based Live Detection - {camera_name}"

    try:
        while class_based_live_detection_running:
            success, frame = cam.read()
            if not success:
                print("Failed to read frame from camera")
                break

            frame_count += 1

            # Run YOLO detection with selected classes only
            results = yolo_model.predict(
                frame,
                conf=0.3,
                iou=0.5,
                classes=detect_class_indices,
                verbose=False
            )

            dets = results[0].boxes
            persons = []
            ppe_items = []

            # Separate persons and PPE items
            if dets is not None and len(dets) > 0:
                for i in range(len(dets)):
                    xyxy = dets.xyxy[i].cpu().tolist()
                    cls_id = int(dets.cls[i].cpu().item())
                    conf = float(dets.conf[i].cpu().item())
                    class_name = canonicalize(yolo_model.names.get(cls_id, ""))

                    if class_name == "person":
                        persons.append({"bbox": xyxy, "conf": conf})
                    else:
                        # Include all PPE items and violations
                        if conf >= 0.3:
                            ppe_items.append({"center": center_of_box(xyxy), "name": class_name, "bbox": xyxy})

            # Create annotated frame - start with original
            annotated_frame = frame.copy()

            # Process each person and check for violations
            for person_idx, person in enumerate(persons):
                px1, py1, px2, py2 = [int(coord) for coord in person["bbox"]]
                person_bbox = [px1, py1, px2, py2]

                # Find PPE items and violations associated with this person
                owned_items = {item["name"] for item in ppe_items if inside_bbox(item["center"], person_bbox)}
                
                # Check which violations this person has
                person_violations = set()
                
                if not class_based_selected_classes or len(class_based_selected_classes) == 0:
                    # No classes selected: Show ALL violations found (negative classes only)
                    for item_name in owned_items:
                        # Check if it's a violation class (negative class - starts with "no_", "No_", or "NO_")
                        canon_item = canonicalize(item_name)
                        if (canon_item.startswith("no_") or canon_item.startswith("No_") or 
                            canon_item.startswith("NO_")):
                            # Add the violation name
                            person_violations.add(canon_item)
                else:
                    # Classes selected: Only show violations for selected classes
                    for required_item in required_ppe:
                        # Check for violation indicators
                        violation_found = False
                        
                        # Check standard "no_X" format
                        violation_class = f"no_{required_item}"
                        if violation_class in owned_items:
                            person_violations.add(required_item)
                            violation_found = True
                        else:
                            # Check all violation classes in owned_items for matches
                            for violation_name in owned_items:
                                if violation_indicates_missing_ppe(violation_name, required_item):
                                    person_violations.add(required_item)
                                    violation_found = True
                                    break
                        
                        # Also check if we explicitly detected a "no_X" violation
                        if not violation_found:
                            # Check if any violation class matches
                            for item_name in owned_items:
                                if violation_indicates_missing_ppe(item_name, required_item):
                                    person_violations.add(required_item)
                                    break

                # Only show persons with violations (negative classes only)
                if person_violations:
                    # This person has violations - draw them using shared function
                    annotated_frame = draw_violation_box(
                        annotated_frame, 
                        person["bbox"], 
                        person_violations, 
                        person_idx=person_idx + 1,
                        color=CLR_MISS
                    )

            # Add camera info overlay
            info_text = f"Camera: {camera_name} | Frame: {frame_count}"
            cv2.putText(annotated_frame, info_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Add classes info
            if class_based_selected_classes:
                classes_text = f"Detecting: {', '.join(class_based_selected_classes)}"
            else:
                classes_text = "Detecting: ALL violations"
            cv2.putText(annotated_frame, classes_text, (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            # Display frame using cv2.imshow
            cv2.imshow(window_name, annotated_frame)
            
            # Check for 'q' key press to stop
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("'q' key pressed - stopping detection")
                class_based_live_detection_running = False
                break

            # Small delay to prevent overwhelming the system
            time.sleep(0.033)  # ~30fps

    except Exception as e:
        print(f"❌ Error in class-based live detection: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cam.release()
        cv2.destroyAllWindows()
        class_based_live_detection_running = False
        print("✅ Class-based live detection stopped")


@camera_dashboard_bp.route('/class_based_detection_feed')
def class_based_detection_feed():
    """Route for streaming class-based processed camera feed"""
    print(f"Class-based detection feed requested - class_based_live_detection_running: {class_based_live_detection_running}")
    try:
        return Response(
            generate_class_based_detection_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
    except Exception as e:
        print(f"Error in class_based_detection_feed: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


@camera_dashboard_bp.route('/class_based_live_detection', methods=['POST'])
def start_class_based_live_detection():
    """Start class-based live detection with HTTP streaming"""
    global class_based_live_detection_running, class_based_detection_thread, class_based_selected_classes, class_based_camera_id
    
    if class_based_live_detection_running:
        return jsonify({
            "status": "error",
            "message": "Class-based live detection is already running. Stop it first."
        }), 400

    try:
        data = request.get_json()
        camera_id = data.get('camera_id', '0')
        selected_classes = data.get('classes', [])
        
        # Validate and filter classes
        if not isinstance(selected_classes, list):
            selected_classes = []
        selected_classes = [cls for cls in selected_classes if cls and cls.strip()]

        # Get camera info from config
        camera_config = CAMERA_CONFIG.get(camera_id, CAMERA_CONFIG["0"])
        camera_name = camera_config["name"]
        camera_type = camera_config["type"]

        # Update global variables
        class_based_camera_id = camera_id
        class_based_selected_classes = selected_classes
        class_based_live_detection_running = True

        print(f"Starting class-based detection with Camera ID: {camera_id}, Name: {camera_name}, Type: {camera_type}")
        print(f"Selected classes: {selected_classes}")

        # Start detection thread (the generator will handle the actual processing)
        class_based_detection_thread = threading.Thread(target=lambda: None)  # Dummy thread, generator handles it
        class_based_detection_thread.daemon = True

        return jsonify({
            "status": "success",
            "message": f"Class-based live detection started using {camera_name}",
            "stream_url": url_for('camera_dashboard.class_based_detection_feed'),
            "camera_id": camera_id,
            "camera_name": camera_name,
            "camera_type": camera_type,
            "selected_classes": selected_classes
        })
    except Exception as e:
        class_based_live_detection_running = False
        return jsonify({
            "status": "error",
            "message": f"Failed to start class-based live detection: {str(e)}"
        }), 500


@camera_dashboard_bp.route('/stop_class_based_live_detection', methods=['POST'])
def stop_class_based_live_detection():
    """Stop class-based live detection"""
    global class_based_live_detection_running
    
    try:
        class_based_live_detection_running = False
        return jsonify({
            "status": "success",
            "message": "Class-based live detection stopped"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to stop class-based live detection: {str(e)}"
        }), 500


@camera_dashboard_bp.route('/class_based_live_detection_status', methods=['GET'])
def get_class_based_live_detection_status():
    """Get current class-based live detection status"""
    global class_based_live_detection_running, class_based_selected_classes, class_based_camera_id
    
    camera_config = CAMERA_CONFIG.get(class_based_camera_id, CAMERA_CONFIG["0"])
    camera_name = camera_config["name"]
    
    return jsonify({
        "running": class_based_live_detection_running,
        "camera_id": class_based_camera_id,
        "camera_name": camera_name,
        "selected_classes": class_based_selected_classes
    })
