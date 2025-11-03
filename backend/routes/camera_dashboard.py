from flask import Blueprint, jsonify, request, Response, url_for, render_template
from werkzeug.utils import secure_filename
import os, json, math
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



camera_dashboard_bp = Blueprint('camera_dashboard', __name__, url_prefix='/api/camera_dashboard')

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


def generate_detection_frames():
    """Generator function that yields YOLO-processed frames from camera"""
    global detection_running, current_camera_id, current_camera_name

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
        while detection_running:
            success, img = cam.read()
            if not success:
                break

            # Use YOLO's default detection with built-in visualization
            results = yolo_model(img, stream=True)
            
            # Process results and use YOLO's default plotting
            for r in results:
                # Use YOLO's built-in plot method for default visualization
                annotated_img = r.plot()
                
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
    global detection_thread, detection_running, current_camera_id, current_camera_name, current_camera_source

    if request.method == 'POST':
        data = request.get_json()
        camera_id = data.get('camera_id', '0')

        # Get camera info from config
        camera_config = CAMERA_CONFIG.get(camera_id, CAMERA_CONFIG["0"])
        camera_name = camera_config["name"]
        camera_type = camera_config["type"]

        print(
            f"Starting detection with Camera ID: {camera_id}, Name: {camera_name}, Type: {camera_type}")

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
            "stream_url": url_for('camera_dashboard.detection_feed'),
            "camera_id": camera_id,
            "camera_name": camera_name,
            "camera_type": camera_type
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
        sample_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

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
    
    print(f"Processing video file: {video_path}")

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
                    print(f"End of video or failed to read frame at frame {frame_counter}")
                    break

                frame_counter += 1
                
                # Validate frame data
                if img is None or img.size == 0:
                    print(f"Warning: Empty or invalid frame detected at frame {frame_counter}, skipping...")
                    continue

                # curr_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
                # Perform object detection with error handling
                try:
                    results = yolo_model(img, stream=True)
                except Exception as yolo_error:
                    print(f"YOLO processing error at frame {frame_counter}: {yolo_error}")
                    # Skip this frame and continue
                    continue

                try:
                    for r in results:
                        if r is None:
                            continue
                            
                        # Use YOLO's built-in plot method for default visualization
                        annotated_img = r.plot()
                        
                        # CLASS DETECTION ONLY - Comment out other functionalities
                        # boxes = r.boxes
                        # if boxes is not None:
                        #     for box in boxes:
                        #         # Calculate confidence and class index
                        #         conf = math.ceil((box.conf[0] * 100)) / 100
                        #         cls = int(box.cls[0])
                        #         currentClass = yolo_model.names[cls]

                        #         # Save violation images for specific classes - COMMENTED OUT
                        #         if conf > 0.5 and currentClass in ['No_helmet', 'No_Vest', 'No_goggles', 'No_SafetyShoes', 'No_Gloves']:
                        #             try:
                        #                 cv2.imwrite(f"media/face_detect/output{curr_datetime}.jpg", annotated_img)
                        #                 cv2.imwrite("media/face_detect/output.jpg", annotated_img)
                        #             except Exception as write_error:
                        #                 print(f"Warning: Failed to write output image at frame {frame_counter}: {write_error}")

                        #         # Count violation for specific classes - COMMENTED OUT
                        #         count_violation(currentClass)

                        #         # Detect faces for violations - COMMENTED OUT
                        #         try:
                        #             detectFace(currentClass)
                        #         except Exception as face_error:
                        #             print(f"Warning: Face detection error at frame {frame_counter}: {face_error}")

                        # Use the annotated image from YOLO's default plotting
                        img = annotated_img
                                
                except Exception as results_error:
                    print(f"Warning: Results processing error at frame {frame_counter}: {results_error}")
                    continue

                # Resize for better performance
                img = cv2.resize(img, (640, 480))

                # Validate frame before encoding
                if img is None or img.size == 0:
                    print(f"Warning: Frame is empty after processing at frame {frame_counter}, skipping...")
                    continue

                # Encode frame as JPEG with error checking
                success, buffer = cv2.imencode(
                    '.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                
                if not success or buffer is None or buffer.size == 0:
                    print(f"Warning: Failed to encode frame {frame_counter}, skipping...")
                    continue
                    
                frame_bytes = buffer.tobytes()
                
                # Debug output every 30 frames
                if frame_counter % 30 == 0:
                    pass

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                       
            except Exception as frame_error:
                print(f"Frame processing error at frame {frame_counter}: {frame_error}")
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
        sample_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

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

        def draw_label(img, text, x, y, color=(255, 255, 255), bg=(0, 0, 0)):
            (tw, th), base = cv2.getTextSize(
                text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(img, (x, y - th - 6), (x + tw + 6, y + 2), bg, -1)
            cv2.putText(img, text, (x + 3, y - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

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

    # Get classes from request
    classes_json = request.form.get(
        'classes', '["helmet", "shoes", "pvc_suit"]')
    try:
        selected_classes = json.loads(classes_json)
    except json.JSONDecodeError as e:
        selected_classes = ["helmet", "shoes", "pvc_suit"]

    try:
        # Secure filename and create upload directory
        if file.filename is None:
            return jsonify({"status": "error", "error": "No filename provided"}), 400
        filename = secure_filename(file.filename)
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        sample_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

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

        video_feed_url = url_for('camera_dashboard.video_feed4', video_path=sample_path)

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
    """Generator function for class-based PPE detection"""
    global video_processing_stop_requested
    
    cap = None
    try:
        # Get the selected classes from app context
        selected_classes = getattr(camera_dashboard_bp, 'class_based_classes', [
                                   "helmet", "shoes", "pvc_suit"])

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

        def canonicalize(name: str) -> str:
            """Converts a class name to its canonical form using the ALIASES map."""
            n = name.lower().replace(" ", "_")
            for canon, synonyms in ALIASES.items():
                if n == canon or n in synonyms:
                    return canon
            return n

        # Determine required classes for detection
        detect_classes_names = set()
        required_ppe = set()

        if selected_classes:
            user_ppe_types = set()
            for cls_name in selected_classes:
                canon_name = canonicalize(cls_name)
                if canon_name.startswith("no_"):
                    user_ppe_types.add(canon_name[3:])
                else:
                    user_ppe_types.add(canon_name)

            required_ppe = user_ppe_types

            for ppe_type in required_ppe:
                detect_classes_names.add(ppe_type)
                detect_classes_names.add(f"no_{ppe_type}")
        else:
            required_ppe = {"helmet", "shoes",
                            "goggles", "safety_vest", "pvc_suit"}
            for ppe_type in required_ppe:
                detect_classes_names.add(ppe_type)
                detect_classes_names.add(f"no_{ppe_type}")

        detect_classes_names.add("person")

        # Get class indices for YOLO
        detect_class_indices = []
        model_class_map = {canonicalize(
            name): idx for idx, name in yolo_model.names.items()}
        for name in detect_classes_names:
            if name in model_class_map:
                detect_class_indices.append(model_class_map[name])

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Could not open video file")

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

                consecutive_errors = 0  # Reset error counter on successful frame

                # Process frame with YOLO using selected classes and default visualization
                results = yolo_model.predict(
                    frame, conf=0.3, iou=0.5, classes=detect_class_indices, verbose=False)

                # Use YOLO's default plotting for detection visualization
                annotated_frame = results[0].plot()
                
                # CLASS DETECTION ONLY - Comment out other functionalities
                # Add class-based analysis overlay - COMMENTED OUT
                # dets = results[0].boxes
                # if dets is not None and len(dets) > 0:
                #     print(f"DEBUG: Found {len(dets)} detections in frame")
                    
                #     # Add information about selected classes
                #     info_text = f"Selected Classes: {', '.join(selected_classes)}"
                #     cv2.putText(annotated_frame, info_text, (10, 30),
                #                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
                #     for i in range(len(dets)):
                #         xyxy = dets.xyxy[i].cpu().tolist()
                #         cls_id = int(dets.cls[i].cpu().item())
                #         conf = float(dets.conf[i].cpu().item())
                #         class_name = yolo_model.names.get(cls_id, "")
                        
                #         print(f"DEBUG: Found {class_name} with confidence {conf}")

                # Resize for better performance
                annotated_frame = cv2.resize(annotated_frame, (640, 480))

                # Encode frame as JPEG
                _, buffer = cv2.imencode(
                    '.jpg', annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                frame_bytes = buffer.tobytes()

                if frame_count % 30 == 0:  # Print every 30 frames
                    pass

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

                # Adjust sleep based on actual processing speed
                time.sleep(0.033)  # ~30fps

            except Exception as frame_error:
                consecutive_errors += 1
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
