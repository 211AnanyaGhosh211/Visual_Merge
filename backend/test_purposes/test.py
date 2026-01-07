# ppe_zone_checker_video.py
import cv2
import csv
import time
from pathlib import Path
from ultralytics import YOLO

# ----------------------------
# CONFIG
# ----------------------------
MODEL_PATH = "/Users/shounakchoudhury/Desktop/Visual_Analytics/backend/Indorama_pvc_suit_best.pt"    # <- your YOLOv8/9/11 PPE model path
VIDEO_PATH = "/Users/shounakchoudhury/Desktop/Visual_Analytics/backend/10.20.200.204_09_20250730170621894.mp4"            # <- your pre-recorded video file

CONF_THRES = 0.25
IOU_THRES = 0.45

# Divider line (x1, y1) -> (x2, y2) in pixels
# Using the pipe in the middle as divider
# Vertical divider line
KEEP_DYNAMIC_MIDLINE = False
DIVIDER = [810, 1080, 945, 500]  # perfect for this video -> DIVIDER = [835, 1050, 890, 0]
   
# Which PPEs are required by zone:
REQUIRED_LEFT  = {"helmet", "shoes", "goggles"}
REQUIRED_RIGHT = {"pvc_suit", "helmet"}

# Class name aliases to normalize to canonical names
ALIASES = {
    "helmet": {"helmet", "hardhat", "safety_helmet","Helmet"},
    "shoes": {"shoes", "safety_shoes", "boots","Safety Shoes"},
    "goggles": {"goggles", "safety_goggles", "glasses", "eye_protection","Safety Goggles"},
    "pvc_suit": {"pvc_suit", "pvc", "chem_suit", "hazmat_suit","PVC Suit"}
}

# Colors
CLR_OK = (0, 200, 0)
CLR_MISS = (0, 0, 255)
CLR_LINE = (255, 255, 255)

# Logging
WRITE_CSV = True
CSV_PATH = "ppe_violations.csv"

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
    Returns sign of cross product:
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

def ensure_csv(path):
    if not Path(path).exists():
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["timestamp", "person_id", "zone", "missing"])

# ----------------------------
# Main
# ----------------------------
def main():
    if WRITE_CSV:
        ensure_csv(CSV_PATH)

    model = YOLO(MODEL_PATH)

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video file: {VIDEO_PATH}")

    divider = DIVIDER[:]  # copy
    W, H = None, None
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

        if W is None or H is None:
            H, W = frame.shape[:2]
            if KEEP_DYNAMIC_MIDLINE:
                x_mid = W // 2
                divider = [x_mid, 0, x_mid, H-1]

        x1, y1, x2, y2 = divider

        # Run YOLO detection
        results = model.predict(frame, conf=CONF_THRES, iou=IOU_THRES, verbose=False)
        dets = results[0].boxes

        persons = []
        ppe_items = []

        if dets is not None and dets.shape[0] > 0:
            for i in range(len(dets)):
                xyxy = dets.xyxy[i].cpu().tolist()
                cls = int(dets.cls[i].cpu().item())
                conf = float(dets.conf[i].cpu().item())
                name = model.names.get(cls, str(cls))
                cname = model_names.get(cls, canonicalize(name))

                if cls in person_class_ids or cname == "person":
                    persons.append({"bbox": xyxy, "conf": conf})
                else:
                    cx, cy = center_of_box(xyxy)
                    ppe_items.append({"bbox": xyxy, "center": (cx, cy), "name": cname, "conf": conf})

        annotated = frame.copy()

        # Assign PPE to each person
        for pid, p in enumerate(persons):
            px1, py1, px2, py2 = p["bbox"]
            pcx, pcy = center_of_box(p["bbox"])

            sign = point_side_of_line(pcx, pcy, x1, y1, x2, y2)
            zone = "LEFT" if sign > 0 else "RIGHT" if sign < 0 else "ON_LINE"

            owned = []
            for it in ppe_items:
                cx, cy = it["center"]
                if inside_bbox(cx, cy, p["bbox"]):
                    owned.append(it["name"])

            owned_set = set(owned)

            # Zone rules
            if zone == "LEFT":
                required = REQUIRED_LEFT
            elif zone == "RIGHT":
                required = REQUIRED_RIGHT
            else:
                required = REQUIRED_LEFT | REQUIRED_RIGHT

            missing = sorted(list(required - owned_set))
            color = CLR_OK if not missing else CLR_MISS

            # Draw bbox + label
            cv2.rectangle(annotated, (int(px1), int(py1)), (int(px2), int(py2)), color, 2)
            label = f"ID:{pid} {zone} {'OK' if not missing else 'MISSING:' + ','.join(missing)}"
            draw_label(annotated, label, int(px1), int(py1) - 8, color=color, bg=(40, 40, 40))

            if WRITE_CSV and missing:
                with open(CSV_PATH, "a", newline="") as f:
                    w = csv.writer(f)
                    w.writerow([int(time.time()), pid, zone, "|".join(missing)])

        # Draw PPE items
        for it in ppe_items:
            x1i, y1i, x2i, y2i = [int(v) for v in it["bbox"]]
            cx, cy = it["center"]
            cv2.rectangle(annotated, (x1i, y1i), (x2i, y2i), (200, 200, 0), 1)
            draw_label(annotated, it["name"], x1i, y1i - 4, color=(0, 0, 0), bg=(200, 200, 0))
            cv2.circle(annotated, (int(cx), int(cy)), 2, (200, 200, 0), -1)

        # Draw divider line
        cv2.line(annotated, (int(x1), int(y1)), (int(x2), int(y2)), CLR_LINE, 2)
        draw_label(annotated, "PIPE DIVIDER", int((x1 + x2) / 2), int((y1 + y2) / 2) - 6,
                   color=(0,0,0), bg=(255,255,255))

        # HUD info
        cv2.putText(annotated, f"Required LEFT: {', '.join(sorted(REQUIRED_LEFT))}", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1, cv2.LINE_AA)
        cv2.putText(annotated, f"Required RIGHT: {', '.join(sorted(REQUIRED_RIGHT))}", (10, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1, cv2.LINE_AA)

        cv2.imshow("PPE Zone Checker", annotated)
        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord('q'):  # quit
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
