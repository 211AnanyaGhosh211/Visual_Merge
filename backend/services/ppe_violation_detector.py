import os
import mysql.connector
import cv2
import torch
import pandas as pd
from facenet_pytorch import InceptionResnetV1, MTCNN
from PIL import Image
from datetime import datetime, timedelta
from collections import defaultdict
import requests


# Load FaceNet model & MTCNN detector
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = InceptionResnetV1(pretrained='vggface2').eval().to(device)
mtcnn = MTCNN(keep_all=False, device=device)

# Initialize directories
os.makedirs('media/faces', exist_ok=True)
os.makedirs('media/face_detect', exist_ok=True)

# Import database configuration from db.py
from db.db import db_config

# Allowed classes for SQL insertion
allowed_classes = {'NO-Hardhat', 'NO-Mask', 'NO-Safety Vest'}

# Cache face embeddings from MySQL database
def cache_embeddings_from_db():
    embeddings = []

    try:
        # Connect to MySQL
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Query to fetch user information
        query = "SELECT EmployeeName, EmployeeID, Images FROM EmployeeInfo.Registered_Employees"
        cursor.execute(query)
        users = cursor.fetchall()

        # Process each user's folder
        for name, roll_no, folder_path in users:
            folder_path = str(folder_path)  # Convert to string
            if not os.path.exists(folder_path):
                print(f"Skipping missing folder: {folder_path}")
                continue

            try:
                for file_name in os.listdir(folder_path):
                    image_path = os.path.join(folder_path, file_name)
                    try:
                        img = Image.open(image_path)
                        with torch.no_grad():
                            face, _ = mtcnn(img, return_prob=True)
                            if face is not None:
                                face = face.unsqueeze(0).to(device)
                                embedding = model(face)
                                embeddings.append((embedding[0].cpu(), name, roll_no))
                    except Exception as e:
                        print(f"Error processing {image_path}: {e}")
            except Exception as e:
                print(f"Error accessing folder {folder_path}: {e}")

        cursor.close()
        connection.close()

    except mysql.connector.Error as db_error:
        print(f"Database error: {db_error}")

    return embeddings

# Initialize known embeddings from MySQL
try:
    known_embeddings = cache_embeddings_from_db()
except Exception as e:
    print(f"Error initializing embeddings: {e}")
    known_embeddings = []

# Dictionary to store the last detection time for each (Username, Exception_Type)
last_logged_exceptions = defaultdict(lambda: datetime.min)

# Function to detect and recognize faces
def detectFace(currentClass):
    frame = cv2.imread("output.jpg")
    if frame is None:
        print("Error: Received an empty frame.")
        return

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    detection = mtcnn.detect(rgb_frame)
    faces = detection[0] if detection is not None else None
    identity = 'Unknown'
    roll_no = 'Unknown'
    face_detected = False

    if faces is not None:
        for box in faces:
            x1, y1, x2, y2 = map(int, box)
            if x1 < 0 or y1 < 0 or x2 > frame.shape[1] or y2 > frame.shape[0]:
                continue

            face = frame[y1:y2, x1:x2]
            if face is None or face.size == 0:
                print("Warning: Empty face region detected.")
                continue

            try:
                face = Image.fromarray(cv2.cvtColor(face, cv2.COLOR_BGR2RGB))
                with torch.no_grad():
                    face_tensor, _ = mtcnn(face, return_prob=True)
                    if face_tensor is not None:
                        face_tensor = face_tensor.unsqueeze(0).to(device)
                        embedding = model(face_tensor)

                        min_dist = float('inf')
                        for known_embedding, name, stored_roll_no in known_embeddings:
                            dist = torch.dist(embedding[0], known_embedding)
                            if dist < min_dist:
                                min_dist = dist
                                if dist < 0.6:
                                    identity = name
                                    roll_no = stored_roll_no

                        cv2.putText(frame, f"{identity} ({roll_no})", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        face_detected = True

            except Exception as e:
                print(f"Error processing face: {e}")

    # Save the frame (with or without face detection)
    curr_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    image_path = f"media/face_detect/face_detect_{curr_datetime}.jpg"
    cv2.imwrite(image_path, frame)

    # Check if we should log this violation
    if currentClass in allowed_classes:
        # Check if the same exception has been logged within the last 10 minutes
        last_logged_key = (identity, currentClass)
        current_time = datetime.now()
        if current_time - last_logged_exceptions[last_logged_key] < timedelta(seconds=180):
            print("Skipping duplicate notification within 30sec window.")
            return

        # Update last logged time
        last_logged_exceptions[last_logged_key] = current_time

        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()

            query = """INSERT INTO Exception_Logs 
                       (time_occurred, Username, Employee_id, Exception_Type, Incident_image) 
                       VALUES (%s, %s, %s, %s, %s)"""
            values = (curr_datetime, identity, roll_no, currentClass, image_path)

            cursor.execute(query, values)
            connection.commit()

            if cursor.rowcount > 0:
                print("Record inserted successfully.")
            else:
                print("No records inserted.")

            cursor.close()
            connection.close()

        except mysql.connector.Error as db_error:
            print(f"Database error: {db_error}")

        # Log to notifications.txt
        with open("log/notifications.txt", "a") as log_file:
            log_file.write(f"Time: {curr_datetime}\n")
            log_file.write(f"Username: {identity}\n")
            log_file.write(f"Employee ID: {roll_no}\n")
            log_file.write(f"Exception Type: {currentClass}\n")
            log_file.write(f"Incident Image: {image_path}\n")
            log_file.write("\n")
            
        
        
        url = "https://backend.aisensy.com/campaign/t1/api/v2"  # Replace with actual URL

        payload = {
                   
                        "apiKey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY3Y2U4YzRkMjkzOGM1MDM4ZmQ0YTYzMyIsIm5hbWUiOiJZb3V0aCBDb21wdXRlciBUcmFpbmluZyBDZW50cmUgIiwiYXBwTmFtZSI6IkFpU2Vuc3kiLCJjbGllbnRJZCI6IjY3Y2U4YzRkMjkzOGM1MDM4ZmQ0YTYyZCIsImFjdGl2ZVBsYW4iOiJGUkVFX0ZPUkVWRVIiLCJpYXQiOjE3NDE1ODk1ODF9.RTXa7AU_8M9JGkEBoptS9mSH6Izxdg8fADZ9NW_rADM",
                        "campaignName": "Visual Analytics",
                        "destination": "917003840021",
                        "userName": "Youth Computer Training Centre ",
                        "templateParams": [
                            f"{identity}",
                            f"{roll_no}",
                            f"{currentClass}",
                            f"{curr_datetime}"
                        ],
                        "source": "new-landing-page form",
                        "media": {},
                        "buttons": [],
                        "carouselCards": [],
                        "location": {},
                        "attributes": {},
                        "paramsFallbackValue": {
                            "FirstName": "user"
                        }
                    
                }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)

        print(response.status_code)
        print(response.text)
                    
                
