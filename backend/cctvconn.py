import cv2
import numpy as np
import time
import threading
import queue
from ultralytics import YOLO
import os
import argparse
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CCTVProcessor:
    def __init__(self, model_path="best (3).pt", conf_threshold=0.45):
        """
        Initialize CCTV processor with YOLO model
        
        Args:
            model_path (str): Path to YOLO model file
            conf_threshold (float): Confidence threshold for detections
        """
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.model = None
        self.frame_queue = queue.Queue(maxsize=10)
        self.result_queue = queue.Queue(maxsize=10)
        self.running = False
        self.colors = self.generate_colors()
        
        # Load model
        self.load_model()
    
    def generate_colors(self):
        """Generate unique colors for different classes"""
        colors = [
            (168, 50, 50),    # Red-ish
            (0, 255, 0),      # Green
            (50, 156, 168),   # Teal
            (50, 78, 168),    # Blue
            (168, 50, 168),   # Purple
            (0, 128, 255),    # Light Blue
            (128, 128, 0),    # Dark Olive
            (255, 165, 0),    # Orange
            (255, 0, 255),    # Magenta
            (0, 255, 255)     # Cyan
        ]
        return colors
    
    def load_model(self):
        """Load YOLO model"""
        try:
            if not os.path.exists(self.model_path):
                logger.error(f"Model file not found: {self.model_path}")
                raise FileNotFoundError(f"Model file not found: {self.model_path}")
            
            logger.info(f"Loading model from: {self.model_path}")
            self.model = YOLO(self.model_path)
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def connect_to_nvr(self, connection_string, connection_type="rtsp"):
        """
        Connect to NVR using different protocols
        
        Args:
            connection_string (str): Connection string (URL, IP:port, etc.)
            connection_type (str): Type of connection ('rtsp', 'http', 'ip')
        
        Returns:
            cv2.VideoCapture: Video capture object
        """
        cap = None
        
        try:
            if connection_type.lower() == "rtsp":
                # RTSP connection
                if not connection_string.startswith("rtsp://"):
                    connection_string = f"rtsp://{connection_string}"
                logger.info(f"Connecting to RTSP stream: {connection_string}")
                cap = cv2.VideoCapture(connection_string)
                
            elif connection_type.lower() == "http":
                # HTTP stream
                if not connection_string.startswith("http://"):
                    connection_string = f"http://{connection_string}"
                logger.info(f"Connecting to HTTP stream: {connection_string}")
                cap = cv2.VideoCapture(connection_string)
                
            elif connection_type.lower() == "ip":
                # IP camera with authentication
                logger.info(f"Connecting to IP camera: {connection_string}")
                cap = cv2.VideoCapture(connection_string)
                
            else:
                raise ValueError(f"Unsupported connection type: {connection_type}")
            
            # Set buffer size for real-time processing
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Test connection
            if not cap.isOpened():
                raise ConnectionError(f"Failed to connect to {connection_string}")
            
            logger.info("Successfully connected to NVR")
            return cap
            
        except Exception as e:
            logger.error(f"Error connecting to NVR: {e}")
            if cap:
                cap.release()
            raise
    
    def process_frame(self, frame):
        """
        Process a single frame with YOLO model
        
        Args:
            frame: Input frame
            
        Returns:
            tuple: (processed_frame, detections)
        """
        try:
            # Run YOLO inference
            if self.model is None:
                logger.error("Model not loaded")
                return frame, []
            results = self.model.predict(source=frame, show=False, stream=True, conf=self.conf_threshold)
            
            detections = []
            processed_frame = frame.copy()
            
            for r in results:
                boxes = r.boxes
                if boxes is not None:
                    for box in boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        class_name = self.model.names[cls_id] if self.model and hasattr(self.model, 'names') else f"Class_{cls_id}"
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        
                        detections.append({
                            'class': class_name,
                            'confidence': conf,
                            'bbox': (x1, y1, x2, y2),
                            'class_id': cls_id
                        })
                        
                        # Draw bounding box
                        color = self.colors[cls_id % len(self.colors)]
                        cv2.rectangle(processed_frame, (x1, y1), (x2, y2), color, 2)
                        
                        # Draw label
                        label = f"{class_name} {conf:.2f}"
                        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                        
                        # Label background
                        cv2.rectangle(processed_frame, (x1, y1 - th - 10), (x1 + tw, y1), color, -1)
                        cv2.rectangle(processed_frame, (x1, y1 - th - 10), (x1 + tw, y1), color, 2)
                        
                        # Label text
                        cv2.putText(processed_frame, label, (x1, y1 - 5), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            return processed_frame, detections
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return frame, []
    
    def frame_processor_thread(self):
        """Thread for processing frames from queue"""
        while self.running:
            try:
                if not self.frame_queue.empty():
                    frame, timestamp = self.frame_queue.get(timeout=1)
                    processed_frame, detections = self.process_frame(frame)
                    
                    if not self.result_queue.full():
                        self.result_queue.put((processed_frame, detections, timestamp))
                    else:
                        # Drop oldest result if queue is full
                        try:
                            self.result_queue.get_nowait()
                            self.result_queue.put((processed_frame, detections, timestamp))
                        except queue.Empty:
                            pass
                else:
                    time.sleep(0.01)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in frame processor thread: {e}")
    
    def start_processing(self, connection_string, connection_type="rtsp", 
                        save_video=False, output_path=None, display=True):
        """
        Start processing CCTV feed
        
        Args:
            connection_string (str): NVR connection string
            connection_type (str): Connection type
            save_video (bool): Whether to save processed video
            output_path (str): Output video path
            display (bool): Whether to display video
        """
        try:
            # Connect to NVR
            cap = self.connect_to_nvr(connection_string, connection_type)
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Initialize video writer if needed
            out = None
            if save_video:
                if output_path is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_path = f"cctv_output_{timestamp}.mp4"
                
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # type: ignore
                out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
                
                if not out.isOpened():
                    logger.warning("Could not create video writer")
                    out = None
            
            # Start processing thread
            self.running = True
            processor_thread = threading.Thread(target=self.frame_processor_thread)
            processor_thread.daemon = True
            processor_thread.start()
            
            logger.info("Starting CCTV feed processing... Press 'q' to quit")
            
            frame_count = 0
            start_time = time.time()
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Failed to read frame from NVR")
                    break
                
                frame_count += 1
                timestamp = time.time()
                
                # Add frame to processing queue
                if not self.frame_queue.full():
                    self.frame_queue.put((frame, timestamp))
                
                # Get processed result
                try:
                    processed_frame, detections, _ = self.result_queue.get(timeout=0.1)
                    
                    # Add FPS and detection count
                    current_fps = frame_count / (time.time() - start_time)
                    cv2.putText(processed_frame, f'FPS: {current_fps:.1f}', 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(processed_frame, f'Detections: {len(detections)}', 
                               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Save frame if needed
                    if out and out.isOpened():
                        out.write(processed_frame)
                    
                    # Display frame
                    if display:
                        cv2.imshow('CCTV Live Detection', processed_frame)
                        
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                    
                    # Log detections
                    if detections:
                        for det in detections:
                            logger.info(f"Detection: {det['class']} (conf: {det['confidence']:.2f})")
                
                except queue.Empty:
                    # Use original frame if no processed result available
                    if display:
                        cv2.imshow('CCTV Live Detection', frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
            
            # Cleanup
            self.running = False
            cap.release()
            if out:
                out.release()
            if display:
                cv2.destroyAllWindows()
            
            logger.info(f"Processing completed. Processed {frame_count} frames.")
            if save_video and output_path:
                logger.info(f"Video saved to: {output_path}")
                
        except Exception as e:
            logger.error(f"Error in processing: {e}")
            self.running = False
            if 'cap' in locals():
                cap.release()
            if 'out' in locals() and out:
                out.release()
            if display:
                cv2.destroyAllWindows()

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='CCTV NVR Live Feed Processor')
    parser.add_argument('--connection', '-c', required=True, 
                       help='NVR connection string (e.g., rtsp://ip:port/stream, http://ip:port/stream)')
    parser.add_argument('--type', '-t', default='rtsp', choices=['rtsp', 'http', 'ip'],
                       help='Connection type (default: rtsp)')
    parser.add_argument('--model', '-m', default='best (3).pt',
                       help='Path to YOLO model file (default: best (3).pt)')
    parser.add_argument('--conf', default=0.45, type=float,
                       help='Confidence threshold (default: 0.45)')
    parser.add_argument('--save', '-s', action='store_true',
                       help='Save processed video')
    parser.add_argument('--output', '-o', default=None,
                       help='Output video path')
    parser.add_argument('--no-display', action='store_true',
                       help='Disable video display')
    
    args = parser.parse_args()
    
    # Create processor
    processor = CCTVProcessor(model_path=args.model, conf_threshold=args.conf)
    
    # Start processing
    processor.start_processing(
        connection_string=args.connection,
        connection_type=args.type,
        save_video=args.save,
        output_path=args.output,
        display=not args.no_display
    )

if __name__ == "__main__":
    # Example usage without command line arguments
    # Uncomment and modify the following lines for direct usage
    
    # processor = CCTVProcessor(model_path="best (3).pt", conf_threshold=0.45)
    # 
    # # Example connection strings - modify these for your NVR
    # # RTSP: rtsp://username:password@ip:port/stream
    # # HTTP: http://ip:port/stream
    # # IP Camera: ip:port
    # 
    # processor.start_processing(
    #     connection_string="rtsp://admin:password@192.168.1.100:554/stream1",
    #     connection_type="rtsp",
    #     save_video=True,
    #     display=True
    # )
    
    main()
