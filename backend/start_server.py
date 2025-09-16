#!/usr/bin/env python3
"""
Simple startup script for the PPE detection backend
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Starting PPE Detection Backend...")
    print("=" * 50)
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check required modules
    required_modules = ['flask', 'cv2', 'torch', 'ultralytics']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module}: OK")
        except ImportError:
            print(f"✗ {module}: MISSING")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\nMissing modules: {', '.join(missing_modules)}")
        print("Please install missing modules with: pip install <module_name>")
        sys.exit(1)
    
    # Try to import the main app
    try:
        from newapp3 import app
        print("✓ Main app imported successfully")
    except Exception as e:
        print(f"✗ Failed to import main app: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("Starting Flask server...")
    print("Backend will be available at: http://127.0.0.1:5000")
    print("Health check: http://127.0.0.1:5000/health")
    print("Test video stream: http://127.0.0.1:5000/test_video_stream")
    print("=" * 50)
    
    # Start the Flask app
    app.run(debug=True, host='127.0.0.1', port=5000, threaded=True)
    
except KeyboardInterrupt:
    print("\nServer stopped by user")
except Exception as e:
    print(f"Error starting server: {e}")
    import traceback
    traceback.print_exc()

