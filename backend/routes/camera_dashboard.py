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

# Global variables for multi-camera simultaneous detection
multi_camera_detection_running = False
multi_camera_threads = {}  # Dictionary to store threads for each camera
multi_camera_selected_classes = []
multi_camera_ids = []  # List of camera IDs being processed

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
        
        # Draw label background
        overlay = img.copy()
        cv2.rectangle(overlay, 
                     (label_x, label_y - text_height - baseline - 5),
                     (label_x + text_width + 10, label_y + 5),
                     label_bg_color, -1)
        cv2.addWeighted(overlay, label_alpha, img, 1 - label_alpha, 0, img)
        
        # Draw label text
        cv2.putText(img, label, (label_x + 5, label_y - baseline),
                   font, font_scale, (255, 255, 255), font_thickness)
    
    return img


def draw_violation_box(img, bbox, violations, person_idx=1, color=(0, 0, 255)):
    """
    Draw a bounding box for a person with violations.
    
    Args:
        img: Image to draw on
        bbox: Bounding box coordinates [x1, y1, x2, y2]
        violations: Set of violation class names
        person_idx: Person index number
        color: Bounding box color (B, G, R)
    
    Returns:
        Modified image with violation box drawn
    """
    x1, y1, x2, y2 = [int(coord) for coord in bbox]
    
    # Draw bounding box
    cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
    
    # Create violation label
    violation_list = list(violations)
    if violation_list:
        label = f"Person {person_idx}: {', '.join(violation_list)}"
    else:
        label = f"Person {person_idx}"
    
    # Draw label
    return draw_bounding_box_with_label(img, bbox, label, color=color, 
                                       label_bg_color=(0, 0, 0), label_alpha=0.7)


# NOTE: Original endpoints (demo2, demo3, demo4, live detection, etc.) 
# need to be restored from your backup or editor history.
# The multi-camera endpoints below are new and can be added to your restored file.

# =============================================================================
# MULTI-CAMERA SIMULTANEOUS DETECTION
# =============================================================================

def process_single_camera_feed(camera_id, selected_classes, stop_event):
    """
    Process a single camera feed with PPE detection.
    This function runs in a separate thread for each camera.
    
    Args:
        camera_id: Camera ID string
        selected_classes: List of classes to detect
        stop_event: threading.Event to signal when to stop
    """
    global email_interval_minutes
    
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
            if violation_name.startswith("no_"):
                base = violation_name[3:]
            elif violation_name.startswith("No_"):
                base = violation_name[3:]
            elif violation_name.startswith("NO_"):
                base = violation_name[3:]
            else:
                base = violation_name
            
            if base.lower() == required_lower:
                return True
            
            if violation_name == "No_Gloves" and required_item == "Safety_Gloves":
                return True
            if violation_name == "no_gloves" and required_item == "Safety_Gloves":
                return True
        
        if required_lower in violation_lower and ("no" in violation_lower or violation_name.startswith("No") or violation_name.startswith("NO")):
            return True
        
        return False

    # Get camera configuration
    camera_config = CAMERA_CONFIG.get(camera_id, CAMERA_CONFIG["0"])
    camera_name = camera_config["name"]
    camera_type = camera_config["type"]
    camera_url = camera_config["url"]

    print(f"🎥 Starting multi-camera detection for: {camera_name} (ID: {camera_id})")
    print(f"   Selected classes: {selected_classes}")

    # Open camera based on type
    if camera_type == 'rtsp' and camera_url:
        print(f"Opening RTSP camera: {camera_url}")
        cam = cv2.VideoCapture(camera_url)
    elif camera_type == 'laptop':
        print(f"Opening laptop camera (index 0)")
        cam = cv2.VideoCapture(0)
    else:
        print(f"Opening camera with index: {camera_id}")
        cam = cv2.VideoCapture(int(camera_id))

    if not cam.isOpened():
        print(f"❌ Error: Could not open camera {camera_name} (ID: {camera_id})")
        return

    # Determine required PPE types from selected classes
    required_ppe = set()
    detect_classes_names = set()
    violation_classes_to_show = set()

    if not selected_classes or len(selected_classes) == 0:
        # No classes selected: Show ALL violations
        print(f"[{camera_name}] No classes selected - showing ALL violations")
        detect_classes_names.add("person")
        for idx, name in yolo_model.names.items():
            canon_name = canonicalize(name)
            if (canon_name.startswith("no_") or canon_name.startswith("No_") or 
                canon_name.startswith("NO_")):
                detect_classes_names.add(canon_name)
                violation_classes_to_show.add(canon_name)
            elif canon_name in ["helmet", "safety_vest", "pvc_suit", "shoes", "goggles", "Safety_Gloves"]:
                detect_classes_names.add(canon_name)
    else:
        # Classes selected: Show only violations for selected classes
        print(f"[{camera_name}] Classes selected: {selected_classes} - showing only violations for these classes")
        user_ppe_types = set()
        for cls_name in selected_classes:
            canon_name = canonicalize(cls_name)
            if canon_name.startswith("no_"):
                user_ppe_types.add(canon_name[3:])
            else:
                user_ppe_types.add(canon_name)

        required_ppe = user_ppe_types

        # Build detection class names
        for ppe_type in required_ppe:
            detect_classes_names.add(ppe_type)
            violation_class = f"no_{ppe_type}"
            detect_classes_names.add(violation_class)
            violation_classes_to_show.add(violation_class)
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

    print(f"[{camera_name}] Detection classes: {detect_classes_names}")
    print(f"[{camera_name}] Violation classes to show: {violation_classes_to_show}")

    # Colors
    CLR_OK = (0, 200, 0)
    CLR_MISS = (0, 0, 255)

    frame_count = 0
    window_name = f"Multi-Cam: {camera_name} (ID: {camera_id})"

    try:
        while not stop_event.is_set():
            success, frame = cam.read()
            if not success:
                print(f"[{camera_name}] Failed to read frame from camera")
                time.sleep(0.1)
                continue

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
                        if conf >= 0.3:
                            ppe_items.append({"center": center_of_box(xyxy), "name": class_name, "bbox": xyxy})

            # Create annotated frame
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
                    # No classes selected: Show ALL violations found
                    for item_name in owned_items:
                        canon_item = canonicalize(item_name)
                        if (canon_item.startswith("no_") or canon_item.startswith("No_") or 
                            canon_item.startswith("NO_")):
                            person_violations.add(canon_item)
                else:
                    # Classes selected: Only show violations for selected classes
                    for required_item in required_ppe:
                        violation_found = False
                        
                        violation_class = f"no_{required_item}"
                        if violation_class in owned_items:
                            person_violations.add(required_item)
                            violation_found = True
                        else:
                            for violation_name in owned_items:
                                if violation_indicates_missing_ppe(violation_name, required_item):
                                    person_violations.add(required_item)
                                    violation_found = True
                                    break
                        
                        if not violation_found:
                            for item_name in owned_items:
                                if violation_indicates_missing_ppe(item_name, required_item):
                                    person_violations.add(required_item)
                                    break

                # Only show persons with violations
                if person_violations:
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
                            os.makedirs("media/face_detect", exist_ok=True)
                            cv2.imwrite(f"media/face_detect/output_{camera_id}_{curr_datetime}.jpg", annotated_frame)
                            cv2.imwrite(f"media/face_detect/output_{camera_id}.jpg", annotated_frame)
                            print(f"✅ [{camera_name}] Saved violation image for {violation_name}")
                            
                            detectFace(violation_name, email_interval_minutes)
                        except Exception as face_error:
                            print(f"Warning: [{camera_name}] Face detection error at frame {frame_count}: {face_error}")

            # Add camera info overlay
            info_text = f"Camera: {camera_name} (ID: {camera_id}) | Frame: {frame_count}"
            cv2.putText(annotated_frame, info_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Add classes info
            if selected_classes:
                classes_text = f"Detecting: {', '.join(selected_classes)}"
            else:
                classes_text = "Detecting: ALL violations"
            cv2.putText(annotated_frame, classes_text, (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            # Display frame using cv2.imshow
            cv2.imshow(window_name, annotated_frame)
            
            # Check for 'q' key press to stop (only if this window is focused)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print(f"[{camera_name}] 'q' key pressed - stopping detection for this camera")
                stop_event.set()
                break

            # Small delay to prevent overwhelming the system
            time.sleep(0.033)  # ~30fps

    except Exception as e:
        print(f"❌ Error in multi-camera detection for {camera_name}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cam.release()
        cv2.destroyWindow(window_name)
        print(f"✅ Multi-camera detection stopped for {camera_name} (ID: {camera_id})")


@camera_dashboard_bp.route('/multi_camera_detection', methods=['POST'])
def start_multi_camera_detection():
    """Start simultaneous detection on multiple cameras"""
    global multi_camera_detection_running, multi_camera_threads, multi_camera_selected_classes, multi_camera_ids
    
    if multi_camera_detection_running:
        return jsonify({
            "status": "error",
            "message": "Multi-camera detection is already running. Stop it first."
        }), 400

    try:
        # Check if request has JSON data
        if not request.is_json:
            return jsonify({
                "status": "error",
                "message": "Request must contain JSON data with Content-Type: application/json"
            }), 400
        
        data = request.get_json(force=True)
        if data is None:
            return jsonify({
                "status": "error",
                "message": "Invalid or empty JSON data in request body"
            }), 400
        
        camera_ids = data.get('camera_ids', [])
        selected_classes = data.get('classes', [])
        
        # Validate camera_ids
        if not isinstance(camera_ids, list) or len(camera_ids) == 0:
            return jsonify({
                "status": "error",
                "message": "camera_ids must be a non-empty list of camera IDs"
            }), 400
        
        # Validate and filter classes
        if not isinstance(selected_classes, list):
            selected_classes = []
        selected_classes = [cls for cls in selected_classes if cls and cls.strip()]

        # Validate camera IDs exist in config
        valid_camera_ids = []
        camera_info = []
        for cam_id in camera_ids:
            if cam_id in CAMERA_CONFIG:
                valid_camera_ids.append(cam_id)
                camera_config = CAMERA_CONFIG[cam_id]
                camera_info.append({
                    "camera_id": cam_id,
                    "camera_name": camera_config["name"],
                    "camera_type": camera_config["type"]
                })
            else:
                print(f"Warning: Camera ID {cam_id} not found in config, skipping...")

        if len(valid_camera_ids) == 0:
            return jsonify({
                "status": "error",
                "message": "No valid camera IDs provided"
            }), 400

        # Update global variables
        multi_camera_ids = valid_camera_ids
        multi_camera_selected_classes = selected_classes
        multi_camera_detection_running = True
        multi_camera_threads = {}

        print(f"Starting multi-camera detection with {len(valid_camera_ids)} cameras")
        print(f"Camera IDs: {valid_camera_ids}")
        print(f"Selected classes: {selected_classes}")

        # Start a thread for each camera
        for camera_id in valid_camera_ids:
            stop_event = threading.Event()
            thread = threading.Thread(
                target=process_single_camera_feed,
                args=(camera_id, selected_classes, stop_event)
            )
            thread.daemon = True
            thread.start()
            multi_camera_threads[camera_id] = {
                "thread": thread,
                "stop_event": stop_event
            }
            print(f"Started thread for camera {camera_id}")

        return jsonify({
            "status": "success",
            "message": f"Multi-camera detection started with {len(valid_camera_ids)} cameras",
            "cameras": camera_info,
            "selected_classes": selected_classes,
            "display_mode": "cv2.imshow",
            "instructions": "Each camera will open in a separate window. Press 'q' in any window to stop that camera."
        })

    except Exception as e:
        multi_camera_detection_running = False
        multi_camera_threads = {}
        multi_camera_ids = []
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in start_multi_camera_detection: {str(e)}")
        print(f"Traceback: {error_trace}")
        return jsonify({
            "status": "error",
            "message": f"Failed to start multi-camera detection: {str(e)}"
        }), 500


@camera_dashboard_bp.route('/stop_multi_camera_detection', methods=['POST'])
def stop_multi_camera_detection():
    """Stop all multi-camera detection"""
    global multi_camera_detection_running, multi_camera_threads, multi_camera_ids
    
    if not multi_camera_detection_running:
        return jsonify({
            "status": "error",
            "message": "Multi-camera detection is not running"
        }), 400

    try:
        # Signal all threads to stop
        for camera_id, thread_info in multi_camera_threads.items():
            thread_info["stop_event"].set()
            print(f"Stopped camera {camera_id}")

        # Wait for threads to finish (with timeout)
        for camera_id, thread_info in multi_camera_threads.items():
            thread_info["thread"].join(timeout=2.0)

        multi_camera_detection_running = False
        multi_camera_threads = {}
        multi_camera_ids = []

        return jsonify({
            "status": "success",
            "message": "Multi-camera detection stopped successfully"
        })

    except Exception as e:
        print(f"Error stopping multi-camera detection: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to stop multi-camera detection: {str(e)}"
        }), 500


@camera_dashboard_bp.route('/multi_camera_detection_status', methods=['GET'])
def get_multi_camera_detection_status():
    """Get current multi-camera detection status"""
    global multi_camera_detection_running, multi_camera_selected_classes, multi_camera_ids
    
    camera_info = []
    for cam_id in multi_camera_ids:
        if cam_id in CAMERA_CONFIG:
            camera_config = CAMERA_CONFIG[cam_id]
            camera_info.append({
                "camera_id": cam_id,
                "camera_name": camera_config["name"],
                "camera_type": camera_config["type"]
            })
    
    return jsonify({
        "running": multi_camera_detection_running,
        "camera_ids": multi_camera_ids,
        "cameras": camera_info,
        "selected_classes": multi_camera_selected_classes
    })
