#!/usr/bin/env python3
"""
Simple test to verify all dependencies are working
"""

try:
    # Test all the imports from your main application
    from ultralytics import YOLO
    import cv2
    import cvzone
    import pandas as pd
    import torch
    from facenet_pytorch import InceptionResnetV1, MTCNN
    from PIL import Image
    from flask import Flask
    import mysql.connector
    import psutil
    from werkzeug.utils import secure_filename
    
    print("✅ All dependencies imported successfully!")
    print(f"✅ Python executable: {__import__('sys').executable}")
    print(f"✅ PyTorch version: {torch.__version__}")
    print(f"✅ OpenCV version: {cv2.__version__}")
    print(f"✅ CUDA available: {torch.cuda.is_available()}")
    
    # Test YOLO model loading (this will work if the model file exists)
    try:
        # This will fail if ppe.pt doesn't exist, but that's expected
        model = YOLO("backend/models/aparava_300_epoch.pt")
        print("✅ YOLO model loaded successfully!")
    except Exception as e:
        print(f"ℹ️ YOLO model file not found (expected): {e}")
    
    print("\n🎉 Your environment is ready to run the PPE detection app!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}") 