# Camera Configuration File
# SIMPLE: Just add your cameras here with numbers 0-10
# Frontend will send camera number (0-10) and backend will automatically use the right camera

CAMERA_CONFIG = {
    "0": {
        "name": "Laptop Camera", 
        "type": "laptop", 
        "url": None,
        "description": "Built-in laptop webcam"
    },
    "1": {
        "name": "Main Entrance", 
        "type": "rtsp", 
        "url": "rtsp://admin:admin%401966@192.168.100.112:554/cam/realmonitor?channel=1&subtype=0",
        "description": "Main entrance camera"
    },
    "2": {
        "name": "Parking Lot", 
        "type": "rtsp", 
        "url": "rtsp://admin:admin%401966@192.168.100.112:554/cam/realmonitor?channel=2&subtype=0",
        "description": "Parking lot camera"
    },
    "3": {
        "name": "Workshop Area", 
        "type": "rtsp", 
        "url": "rtsp://admin:admin%401966@192.168.100.112:554/cam/realmonitor?channel=3&subtype=0",
        "description": "Workshop area camera"
    },
    "4": {
        "name": "Office Area", 
        "type": "rtsp", 
        "url": "rtsp://admin:admin%401966@192.168.100.112:554/cam/realmonitor?channel=4&subtype=0",
        "description": "Office area camera"
    },
    "5": {
        "name": "Storage Area", 
        "type": "rtsp", 
        "url": "rtsp://admin:admin%401966@192.168.100.112:554/cam/realmonitor?channel=5&subtype=0",
        "description": "Storage area camera"
    },
    "6": {
        "name": "Loading Dock", 
        "type": "rtsp", 
        "url": "rtsp://admin:admin%401966@192.168.100.112:554/cam/realmonitor?channel=6&subtype=0",
        "description": "Loading dock camera"
    },
    "7": {
        "name": "Break Room", 
        "type": "rtsp", 
        "url": "rtsp://admin:admin%401966@192.168.100.112:554/cam/realmonitor?channel=7&subtype=0",
        "description": "Break room camera"
    },
    "8": {
        "name": "Conference Room", 
        "type": "rtsp", 
        "url": "rtsp://admin:admin%401966@192.168.100.112:554/cam/realmonitor?channel=8&subtype=0",
        "description": "Conference room camera"
    },
    "9": {
        "name": "Reception Area", 
        "type": "rtsp", 
        "url": "rtsp://admin:admin%401966@192.168.100.112:554/cam/realmonitor?channel=9&subtype=0",
        "description": "Reception area camera"
    },
    "10": {
        "name": "Emergency Exit", 
        "type": "rtsp", 
        "url": "rtsp://admin:admin%401966@192.168.100.112:554/cam/realmonitor?channel=10&subtype=0",
        "description": "Emergency exit camera"
    }
}

# HOW TO ADD YOUR CAMERAS:
# 1. Just add a new entry with the next number
# 2. Set the name, type, and URL
# 3. That's it! Frontend will automatically show it in the dropdown

# Example:
# "11": {
#     "name": "New Camera", 
#     "type": "rtsp", 
#     "url": "rtsp://username:password@192.168.1.100:554/stream1",
#     "description": "Your new camera description"
# }

# Camera types
CAMERA_TYPES = {
    "laptop": "Built-in laptop camera",
    "rtsp": "Network RTSP camera",
    "usb": "USB camera",
    "ip": "IP camera"
}

# Default settings
DEFAULT_CAMERA_ID = "0"
DEFAULT_CAMERA_NAME = "Laptop Camera"
DEFAULT_CAMERA_TYPE = "laptop"
