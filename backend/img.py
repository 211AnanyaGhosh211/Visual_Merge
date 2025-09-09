from ultralytics import YOLO
import cv2
import numpy as np
import time
import os
from pathlib import Path

def generate_unique_colors(num_classes):
    """Generate visually distinct colors for each class"""
    colors = []
    
    # Pre-defined distinct colors for common classes
    predefined_colors = [
        (255, 0, 0),     # Red
        (0, 255, 0),     # Green  
        (0, 0, 255),     # Blue
        (255, 255, 0),   # Yellow
        (255, 0, 255),   # Magenta
        (0, 255, 255),   # Cyan
        (255, 165, 0),   # Orange
        (128, 0, 128),   # Purple
        (255, 192, 203), # Pink
        (0, 128, 0),     # Dark Green
        (128, 128, 0),   # Olive
        (0, 0, 128),     # Navy
        (128, 0, 0),     # Maroon
        (255, 20, 147),  # Deep Pink
        (32, 178, 170),  # Light Sea Green
        (255, 69, 0),    # Red Orange
        (138, 43, 226),  # Blue Violet
        (34, 139, 34),   # Forest Green
        (220, 20, 60),   # Crimson
        (255, 215, 0),   # Gold
    ]
    
    # Use predefined colors first
    for i in range(min(num_classes, len(predefined_colors))):
        colors.append(predefined_colors[i])
    
    # Generate additional colors if needed using HSV color space
    if num_classes > len(predefined_colors):
        for i in range(len(predefined_colors), num_classes):
            # Create colors in HSV space for better distribution
            hue = int((i - len(predefined_colors)) * 360 / (num_classes - len(predefined_colors)))
            saturation = 255
            value = 255
            
            # Convert HSV to RGB
            hsv = np.uint8([[[hue, saturation, value]]])  # type: ignore
            rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)[0][0]  # type: ignore
            colors.append(tuple(map(int, rgb)))
    
    return colors

def regions_overlap(region1, region2):
    """Check if two rectangular regions overlap"""
    x1, y1, w1, h1 = region1
    x2, y2, w2, h2 = region2
    
    return not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1)

def draw_text_with_background(img, text, position, font_scale=0.5, font_thickness=1, 
                             text_color=(255, 255, 255), bg_color=(0, 0, 0), 
                             bg_alpha=0.7):
    """Draw text with semi-transparent background"""
    x, y = position
    
    # Ensure coordinates are within image bounds
    if x < 0 or y < 0 or x >= img.shape[1] or y >= img.shape[0]:
        return
    
    # Get text size
    (text_width, text_height), baseline = cv2.getTextSize(
        text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness
    )
    
    # Create background rectangle with bounds checking
    padding = 2
    bg_x1 = max(0, x - padding)
    bg_y1 = max(0, y - text_height - padding)
    bg_x2 = min(img.shape[1], x + text_width + padding)
    bg_y2 = min(img.shape[0], y + baseline + padding)
    
    # Only draw if rectangle is valid
    if bg_x2 > bg_x1 and bg_y2 > bg_y1:
        # Draw semi-transparent background
        overlay = img.copy()
        cv2.rectangle(overlay, (bg_x1, bg_y1), (bg_x2, bg_y2), bg_color, -1)
        cv2.addWeighted(overlay, bg_alpha, img, 1 - bg_alpha, 0, img)
        
        # Draw text
        cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 
                    font_scale, text_color, font_thickness)

def find_non_overlapping_position(boxes, confidences, class_ids, class_names, img_shape):
    """Find non-overlapping positions for text labels"""
    text_positions = []
    occupied_regions = []
    
    img_height, img_width = img_shape[:2]
    
    for i, (box, conf, class_id) in enumerate(zip(boxes, confidences, class_ids)):
        x, y, w, h = box
        
        # Bounds checking for box coordinates
        x = max(0, min(x, img_width - 1))
        y = max(0, min(y, img_height - 1))
        w = max(1, min(w, img_width - x))
        h = max(1, min(h, img_height - y))
        
        # Safe class name retrieval
        if isinstance(class_names, dict):
            class_name = class_names.get(class_id, f"Class {class_id}")
        elif isinstance(class_names, list) and class_id < len(class_names):
            class_name = class_names[class_id]
        else:
            class_name = f"Class {class_id}"
        
        text = f"{class_name}: {conf:.2f}"
        
        # Calculate text size
        font_scale = 0.5
        font_thickness = 1
        (text_width, text_height), baseline = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness
        )
        
        # Try different positions in order of preference
        candidate_positions = [
            (x, y - 5),                           # Above box (default)
            (x, y + h + text_height + 5),         # Below box
            (x + w + 5, y + text_height),         # Right of box
            (x - text_width - 5, y + text_height), # Left of box
            (x + w//2 - text_width//2, y + h//2 + text_height//2), # Center of box
        ]
        
        text_pos = None
        for pos_x, pos_y in candidate_positions:
            # Check boundaries
            if (pos_x < 0 or pos_y < 0 or 
                pos_x + text_width > img_width or 
                pos_y > img_height):
                continue
            
            # Create text region
            text_region = [pos_x, pos_y - text_height, text_width, text_height]
            
            # Check if this region overlaps with any existing text
            overlap = False
            for occupied in occupied_regions:
                if regions_overlap(text_region, occupied):
                    overlap = True
                    break
            
            if not overlap:
                text_pos = (pos_x, pos_y)
                occupied_regions.append(text_region)
                break
        
        # If no position found, use offset position
        if text_pos is None:
            offset_y = len(occupied_regions) * (text_height + 5)
            text_pos = (x, max(text_height + 5, y - 5 - offset_y))
            occupied_regions.append([x, text_pos[1] - text_height, text_width, text_height])
        
        text_positions.append((text_pos, text, font_scale, font_thickness))
    
    return text_positions

def draw_hierarchical_labels(img, boxes, confidences, class_ids, class_names):
    """Draw labels in a hierarchical manner to avoid overlaps"""
    if len(boxes) == 0:
        return img
    
    # Sort by confidence (highest first)
    sorted_indices = np.argsort(confidences)[::-1]
    
    # Create layers for text positioning
    text_layers = []
    layer_height = 25
    
    for idx in sorted_indices:
        box = boxes[idx]
        conf = confidences[idx]
        class_id = class_ids[idx]
        
        x, y, w, h = box
        
        # Safe class name retrieval
        if isinstance(class_names, dict):
            class_name = class_names.get(class_id, f"Class {class_id}")
        elif isinstance(class_names, list) and class_id < len(class_names):
            class_name = class_names[class_id]
        else:
            class_name = f"Class {class_id}"
        
        text = f"{class_name}: {conf:.2f}"
        
        # Find appropriate layer
        layer = 0
        text_y = y - 5 - (layer * layer_height)
        
        # Check if this position conflicts with existing text in this layer
        while any(abs(existing_x - x) < 100 and existing_layer == layer 
                 for existing_x, existing_layer in text_layers):
            layer += 1
            text_y = y - 5 - (layer * layer_height)
        
        # Ensure text doesn't go above image
        if text_y < 20:
            text_y = y + h + 20 + (layer * layer_height)
        
        text_layers.append((x, layer))
        
        # Draw text with background
        draw_text_with_background(img, text, (x, text_y))
    
    return img

def draw_detections_with_side_panel(img, boxes, confidences, class_ids, class_names, colors):
    """Draw detections with labels in a side panel (only for safety violations)"""
    panel_width = 250
    img_height, img_width = img.shape[:2]
    
    # Create extended image with side panel
    extended_img = np.zeros((img_height, img_width + panel_width, 3), dtype=np.uint8)
    extended_img[:, :img_width] = img
    extended_img[:, img_width:] = (50, 50, 50)  # Dark gray panel
    
    # Define safety violation classes
    safety_violations = [
        'no helmet', 'no vest', 'no goggles', 'no safety shoes',
        'no_helmet', 'no_vest', 'no_goggles', 'no_safety_shoes',
        'without helmet', 'without vest', 'without goggles', 'without safety shoes'
    ]
    
    panel_item_count = 0
    
    for i, (box, conf, class_id) in enumerate(zip(boxes, confidences, class_ids)):
        x, y, w, h = box
        
        # Bounds checking
        x = max(0, min(x, img_width - 1))
        y = max(0, min(y, img_height - 1))
        w = max(1, min(w, img_width - x))
        h = max(1, min(h, img_height - y))
        
        # Use consistent color for this class
        color = colors[class_id] if class_id < len(colors) else colors[class_id % len(colors)]
        
        # Draw bounding box (for all detections)
        cv2.rectangle(extended_img, (x, y), (x + w, y + h), color, 2)
        
        # Get class name
        if isinstance(class_names, dict):
            class_name = class_names.get(class_id, f"Class {class_id}")
        elif isinstance(class_names, list) and class_id < len(class_names):
            class_name = class_names[class_id]
        else:
            class_name = f"Class {class_id}"
        
        # Check if this is a safety violation
        is_safety_violation = any(violation.lower() in class_name.lower() for violation in safety_violations)
        
        if is_safety_violation:
            # Draw number on box for safety violations only
            cv2.putText(extended_img, str(panel_item_count + 1), (x+5, y+20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            # Draw label in side panel
            label_text = f"{panel_item_count + 1}. {class_name}: {conf:.2f}"
            
            panel_y = 30 + panel_item_count * 25
            if panel_y < img_height:  # Check bounds
                cv2.putText(extended_img, label_text, (img_width + 10, panel_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            panel_item_count += 1
    
    return extended_img

def draw_yolo_detections(img, boxes, confidences, class_ids, class_names, colors,
                        method='smart_positioning'):
    """Draw YOLO detections with selective text labels for safety violations only"""
    if len(boxes) == 0:
        return img
    
    # Define safety violation classes that should show text
    safety_violations = [
        'no helmet', 'no vest', 'no goggles', 'no safety shoes',
        'no_helmet', 'no_vest', 'no_goggles', 'no_safety_shoes',
        'without helmet', 'without vest', 'without goggles', 'without safety shoes'
    ]
    
    # Draw bounding boxes first (for ALL detections)
    for i, (box, conf, class_id) in enumerate(zip(boxes, confidences, class_ids)):
        x, y, w, h = box
        
        # Bounds checking
        img_height, img_width = img.shape[:2]
        x = max(0, min(x, img_width - 1))
        y = max(0, min(y, img_height - 1))
        w = max(1, min(w, img_width - x))
        h = max(1, min(h, img_height - y))
        
        # Use consistent color for this class
        color = colors[class_id] if class_id < len(colors) else colors[class_id % len(colors)]
        
        # Draw bounding box
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
    
    # Filter boxes and data for safety violations only
    safety_boxes = []
    safety_confidences = []
    safety_class_ids = []
    
    for i, (box, conf, class_id) in enumerate(zip(boxes, confidences, class_ids)):
        # Get class name
        if isinstance(class_names, dict):
            class_name = class_names.get(class_id, f"Class {class_id}")
        elif isinstance(class_names, list) and class_id < len(class_names):
            class_name = class_names[class_id]
        else:
            class_name = f"Class {class_id}"
        
        # Check if this is a safety violation
        if any(violation.lower() in class_name.lower() for violation in safety_violations):
            safety_boxes.append(box)
            safety_confidences.append(conf)
            safety_class_ids.append(class_id)
    
    # Draw text labels only for safety violations
    if len(safety_boxes) > 0:
        if method == 'smart_positioning':
            text_positions = find_non_overlapping_position(
                safety_boxes, safety_confidences, safety_class_ids, class_names, img.shape
            )
            
            for (pos, text, font_scale, font_thickness) in text_positions:
                draw_text_with_background(img, text, pos, font_scale, font_thickness)
        
        elif method == 'hierarchical':
            img = draw_hierarchical_labels(img, safety_boxes, safety_confidences, safety_class_ids, class_names)
        
        elif method == 'no_text':
            # Only draw boxes, no text
            pass
        
        elif method == 'side_panel':
            img = draw_detections_with_side_panel(img, safety_boxes, safety_confidences, safety_class_ids, class_names, colors)
        
        elif method == 'minimal_text':
            # Only show class ID as small text for safety violations
            for i, (box, conf, class_id) in enumerate(zip(safety_boxes, safety_confidences, safety_class_ids)):
                x, y, w, h = box
                cv2.putText(img, str(class_id), (x, y-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    return img

def process_video_with_clean_labels(video_path, model_path='yolov8n.pt', 
                                   label_method='smart_positioning',
                                   output_path=None, conf_threshold=0.25,
                                   show_fps=True, resize_factor=1.0,
                                   display_video=True):
    """
    Process video with YOLO detection and clean, non-overlapping labels
    
    Args:
        video_path: Path to input video
        model_path: Path to YOLO model
        label_method: Method for label positioning
        output_path: Path to save output video (optional)
        conf_threshold: Confidence threshold for detections
        show_fps: Whether to display FPS on video
        resize_factor: Factor to resize video (1.0 = original size)
        display_video: Whether to display video window (set False for Colab)
    """
    # Check if files exist
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        return
    
    if not os.path.exists(model_path):
        print(f"Error: Model file not found: {model_path}")
        return
    
    try:
        # Load model
        print("Loading YOLO model...")
        model = YOLO(model_path)
        print("Model loaded successfully!")
        
        # Generate unique colors for all classes
        num_classes = len(model.names)
        colors = generate_unique_colors(num_classes)
        print(f"Generated {num_classes} unique colors for classes")
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"Error: Could not open video {video_path}")
            return
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Validate video properties
        if fps <= 0:
            fps = 30  # Default FPS
        if width <= 0 or height <= 0:
            print("Error: Invalid video dimensions")
            return
        
        # Apply resize factor
        if resize_factor != 1.0:
            width = int(width * resize_factor)
            height = int(height * resize_factor)
        
        print(f"Video info: {width}x{height} @ {fps}fps, {total_frames} frames")
        
        # Setup video writer if output path is provided
        out = None
        if output_path:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Adjust width for side panel method
            output_width = width + 250 if label_method == 'side_panel' else width
            
            # Try different codecs for better Colab compatibility
            codecs = ['mp4v', 'XVID', 'MJPG']
            for codec in codecs:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*codec)  # type: ignore
                    out = cv2.VideoWriter(output_path, fourcc, fps, (output_width, height))
                    if out.isOpened():
                        print(f"Using codec: {codec}")
                        break
                    else:
                        out.release()
                        out = None
                except:
                    continue
            
            if out is None:
                print("Warning: Could not create video writer. Video will not be saved.")
        
        # Initialize variables for FPS calculation
        prev_time = time.time()
        frame_count = 0
        
        print("Processing video... Press 'q' to quit")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Resize frame if needed
            if resize_factor != 1.0:
                frame = cv2.resize(frame, (width, height))
            
            try:
                # Run YOLO inference
                results = model(frame, conf=conf_threshold, verbose=False)
                
                # Extract detections
                boxes = []
                confidences = []
                class_ids = []
                
                for result in results:
                    if result.boxes is not None:
                        for box in result.boxes:
                            # Extract box coordinates
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            x, y, w, h = int(x1), int(y1), int(x2-x1), int(y2-y1)
                            
                            # Validate coordinates
                            if w > 0 and h > 0:
                                boxes.append([x, y, w, h])
                                confidences.append(float(box.conf[0]))
                                class_ids.append(int(box.cls[0]))
                
                # Get class names
                class_names = model.names
                
                # Draw detections with clean labels using consistent colors
                result_frame = draw_yolo_detections(
                    frame, boxes, confidences, class_ids, class_names, colors,
                    method=label_method
                )
                
                # Add FPS counter
                if show_fps:
                    current_time = time.time()
                    if current_time - prev_time > 0:
                        current_fps = 1 / (current_time - prev_time)
                        cv2.putText(result_frame, f'FPS: {current_fps:.1f}', 
                                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    prev_time = current_time
                
                # Add frame counter
                cv2.putText(result_frame, f'Frame: {frame_count}/{total_frames}', 
                           (10, result_frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.5, (255, 255, 255), 1)
                
                # Write frame to output video
                if out and out.isOpened():
                    out.write(result_frame)
                
                # Display frame (only if not in headless mode)
                if display_video:
                    cv2.imshow('YOLO Video Detection', result_frame)
                    
                    # Check for quit
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                # Progress indicator
                if frame_count % 30 == 0:
                    progress = (frame_count / total_frames) * 100
                    print(f"Progress: {progress:.1f}% ({frame_count}/{total_frames})")
                    
            except Exception as e:
                print(f"Error processing frame {frame_count}: {e}")
                continue
        
        # Cleanup
        cap.release()
        if out:
            out.release()
        if display_video:
            cv2.destroyAllWindows()
        
        print("Video processing completed!")
        
        # Display output path if video was saved
        if output_path and os.path.exists(output_path):
            print(f"Output video saved to: {output_path}")
            
    except Exception as e:
        print(f"Error during video processing: {e}")
        import traceback
        traceback.print_exc()

def process_webcam_with_clean_labels(model_path='yolov8n.pt', 
                                    label_method='smart_positioning',
                                    conf_threshold=0.25, camera_id=0):
    """
    Process webcam feed with YOLO detection and clean labels
    """
    try:
        # Load model
        model = YOLO(model_path)
        
        # Generate unique colors for all classes
        num_classes = len(model.names)
        colors = generate_unique_colors(num_classes)
        print(f"Generated {num_classes} unique colors for classes")
        
        # Open webcam
        cap = cv2.VideoCapture(camera_id)
        
        if not cap.isOpened():
            print(f"Error: Could not open camera {camera_id}")
            return
        
        # Set camera properties (optional)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        prev_time = time.time()
        
        print("Processing webcam... Press 'q' to quit")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Run YOLO inference
            results = model(frame, conf=conf_threshold, verbose=False)
            
            # Extract detections
            boxes = []
            confidences = []
            class_ids = []
            
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        # Extract box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        x, y, w, h = int(x1), int(y1), int(x2-x1), int(y2-y1)
                        
                        if w > 0 and h > 0:
                            boxes.append([x, y, w, h])
                            confidences.append(float(box.conf[0]))
                            class_ids.append(int(box.cls[0]))
            
            # Get class names
            class_names = model.names
            
            # Draw detections with clean labels using consistent colors
            result_frame = draw_yolo_detections(
                frame, boxes, confidences, class_ids, class_names, colors,
                method=label_method
            )
            
            # Add FPS counter
            current_time = time.time()
            if current_time - prev_time > 0:
                fps = 1 / (current_time - prev_time)
                cv2.putText(result_frame, f'FPS: {fps:.1f}', 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            prev_time = current_time
            
            # Display frame
            cv2.imshow('YOLO Webcam Detection', result_frame)
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Error during webcam processing: {e}")
        import traceback
        traceback.print_exc()
