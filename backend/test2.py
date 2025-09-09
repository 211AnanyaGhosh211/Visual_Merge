import cv2
import time
import datetime
from pathlib import Path
from ultralytics import YOLO
# from deep_sort_realtime.deepsort_tracker import DeepSort  # Commented out - install with: pip install deep-sort-realtime

# ----------------------------
# CONFIG
# ----------------------------
MODEL_PATH = r"C:\Users\LENOVO\Desktop\Visual_Merge\backend\best700.pt"   # <- your YOLOv8/9/11 PPE model path
VIDEO_PATH = r"C:\Users\LENOVO\Downloads\WhatsApp Video 2025-09-08 at 15.24.23.mp4"
# Optional: Define VideoWriter to save output
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # type: ignore


CONF_THRES = 0.25
IOU_THRES = 0.45

# Which PPEs are required by zone:
REQUIRED_LEFT  = {"L"}
# REQUIRED_LEFT  = {"helmet", "shoes", "goggles","safety_vest","pvc_suit","no_helmet", "no_safety_shoes","no_goggles", "no_pvc_suit","no_safety_vest"}

#REQUIRED_RIGHT = {"helmet", "shoes", "goggles","safety_vest","pvc_suit"}
REQUIRED_RIGHT = {"helmet", "shoes", "goggles","safety_vest","pvc_suit","no_helmet", "no_safety_shoes","no_goggles", "no_pvc_suit","no_safety_vest"}


# Class name aliases to normalize to canonical names
ALIASES = {
    "helmet": {"helmet", "hardhat", "safety_helmet","Helmet"},
    "shoes": {"shoes", "safety_shoes", "boots","Safety Shoes"},
    "goggles": {"goggles", "safety_goggles", "glasses", "eye_protection","Safety Goggles"},
    "pvc_suit": {"pvc_suit", "pvc", "chem_suit", "hazmat_suit","PVC Suit"},
    "safety_vest": {"vest", "safety_vest", "vest"},
    "no_safety_vest": {"no_vest", "no_safety_vest", "no_vest"},
    "no_pvc_suit": {"no_suit", "no_safety_suit", "no_safety_vest"},
    "no_goggles": {"no_goggles", "no_safety_goggles", "no_eye_protection", "no_safety_goggles"},
    "no_safety_shoes": {"no_shoes", "no_safety_shoes", "no_boots", "no_safety_shoes"},
    "no_helmet": {"no_helmet", "no_safety_helmet", "no_hardhat", "no_safety_helmet"}
}

# Colors
CLR_OK = (0, 200, 0)
CLR_MISS = (255, 0, 0) # Changed to blue
CLR_LINE = (255, 255, 255)
CLR_MISS_TEXT = (255, 255, 255) # White text
CLR_MISS_BG = (255, 0, 0) # Blue background

# Logging
WRITE_LOG = True
LOG_PATH = "ppe_violations_log.txt"
OUTPUT_VIDEO_PATH = "output_video.mp4"

# ----------------------------
# Helpers
# ----------------------------
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
    """
    Returns sign of cross product for vertical line:
    >0 = left side of line
    <0 = right side
    =0 = on the line
    """
    return (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)


def inside_bbox(px, py, xyxy):
    x1, y1, x2, y2 = xyxy
    return x1 <= px <= x2 and y1 <= py <= y2

def draw_label(img, text, x, y, color=(255,255,255), bg=(0,0,0)):
    (tw, th), base = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv2.rectangle(img, (x, y - th - 6), (x + tw + 6, y + 2), bg, -1)
    cv2.putText(img, text, (x + 3, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

def ensure_log(path):
    # Creates the log file and writes a header if it doesn't exist.
    if not Path(path).exists():
        with open(path, "w") as f:
            f.write("--- PPE VIOLATION LOG ---\n")
            f.write("Timestamp           | Person ID | Zone     | Missing Items\n")
            f.write("--------------------+-----------+----------+-----------------\n")

# ----------------------------
# Main
# ----------------------------
def main():
    if WRITE_LOG:
        ensure_log(LOG_PATH)

    model = YOLO(MODEL_PATH)

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video file: {VIDEO_PATH}")

    # Initialize DeepSort tracker with increased max_age for more consistent IDs
    # tracker = DeepSort(max_age=70, n_init=3)  # Commented out - requires deep-sort-realtime
    tracker = None  # Fallback when DeepSort is not available

    # Calculate the video width and height
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))


    # Set vertical divider
    x_mid = W // 2
    divider = [x_mid, 0, x_mid, H - 1]
    zone_names = ("LEFT", "RIGHT")


    out = cv2.VideoWriter(OUTPUT_VIDEO_PATH, fourcc, 30.0, (W, H))


    x1, y1, x2, y2 = divider

    person_class_ids = set()

    # Class name map
    model_names = {i: canonicalize(n) for i, n in model.names.items()}

    # Detect person class ID(s)
    for idx, name in model.names.items():
        if name.lower() == "person":
            person_class_ids.add(idx)

    if not person_class_ids:
        print("⚠️ Warning: model has no 'person' class.")


    while True:
        ret, frame = cap.read()
        if not ret:
            break  # end of video


        # Run YOLO detection
        results = model.predict(frame, conf=CONF_THRES, iou=IOU_THRES, verbose=False)
        dets = results[0].boxes

        # Prepare detections for DeepSort
        detections_for_tracker = []
        persons_detections = []
        ppe_items = []

        if dets is not None and dets.shape[0] > 0:
            for i in range(len(dets)):
                xyxy = dets.xyxy[i].cpu().tolist()
                cls = int(dets.cls[i].cpu().item())
                conf = float(dets.conf[i].cpu().item())
                name = model.names.get(cls, str(cls))
                cname = model_names.get(cls, canonicalize(name))

                if cls in person_class_ids or cname == "person":
                    # DeepSort expects [x1, y1, w, h]
                    w = xyxy[2] - xyxy[0]
                    h = xyxy[3] - xyxy[1]
                    detections_for_tracker.append(([xyxy[0], xyxy[1], w, h], conf, cname))
                    persons_detections.append({"bbox": xyxy, "conf": conf})
                else:
                    cx, cy = center_of_box(xyxy)
                    ppe_items.append({"bbox": xyxy, "center": (cx, cy), "name": cname, "conf": conf})

        # Update DeepSort tracker with person detections
        if tracker is not None:
            tracks = tracker.update_tracks(detections_for_tracker, frame=frame)
        else:
            # Fallback: create simple tracks without DeepSort
            tracks = []
            for i, det in enumerate(detections_for_tracker):
                # Create a simple track object
                class SimpleTrack:
                    def __init__(self, track_id, bbox):
                        self.track_id = track_id
                        self.bbox = bbox
                    
                    def is_confirmed(self):
                        return True
                    
                    def to_ltrb(self):
                        return self.bbox
                
                bbox, conf, name = det
                tracks.append(SimpleTrack(i, [bbox[0], bbox[1], bbox[0] + bbox[2], bbox[1] + bbox[3]]))

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


            # Identify missing items by checking if any of the "no_" classes are present in the owned_set
            missing_items = []
            for required_item in required:
                if f"no_{required_item}" in owned_set:
                    missing_items.append(required_item)

            color = CLR_OK if not missing_items else CLR_MISS

            # Draw bbox + label for tracked person
            cv2.rectangle(annotated, (int(px1), int(py1)), (int(px2), int(py2)), color, 2)
            label = f"ID:{track_id} {zone} {'OK' if not missing_items else 'MISSING:' + ','.join(missing_items)}"
            # Use updated colors for missing label
            text_color = CLR_OK if not missing_items else CLR_MISS_TEXT
            bg_color = (40, 40, 40) if not missing_items else CLR_MISS_BG

            # Adjust text position based on zone
            text_x = int(px1)
            text_y = int(py1) - 8
            (tw, th), base = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            if zone == "RIGHT":
                text_x = int(px2) - tw - 6 # Align text to the right of the bounding box


            draw_label(annotated, label, text_x, text_y, color=text_color, bg=bg_color)


            if WRITE_LOG and missing_items: # Log missing PPE regardless of zone
                # Get current timestamp
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                missing_str = ", ".join(missing_items)
                # Format the log entry string to include the zone
                log_entry = f"{timestamp} | {track_id:<9} | {zone:<8} | {missing_str}\n"
                with open(LOG_PATH, "a") as f:
                    f.write(log_entry)

        # Draw divider line
        cv2.line(annotated, (int(x1), int(y1)), (int(x2), int(y2)), CLR_LINE, 2)
        draw_label(annotated, f"AUTO DIVIDER (VERTICAL)", int((x1 + x2) / 2), int((y1 + y2) / 2) - 6,
                   color=(0,0,0), bg=(255,255,255))

        # HUD info
        cv2.putText(annotated, f"Required {zone_names[0]}: {', '.join(sorted(REQUIRED_LEFT))}", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1, cv2.LINE_AA)
        cv2.putText(annotated, f"Required {zone_names[1]}: {', '.join(sorted(REQUIRED_RIGHT))}", (10, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1, cv2.LINE_AA)


        cv2.imshow('PPE Detection', annotated)  # Use cv2.imshow for local environment
        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord('q'):  # quit
            break
        out.write(annotated) # Write the frame to the output video

    cap.release()
    out.release() # Release the VideoWriter
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()