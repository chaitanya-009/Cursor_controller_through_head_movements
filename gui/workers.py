# gui/workers.py
import cv2
import time
from PyQt6.QtCore import QObject, pyqtSignal
from core.face_processor import FaceProcessor
from core.head_tracker import HeadTracker
from core.blink_detector import BlinkDetector
from core.cursor_controller import MacCursorController, WindowsCursorController

class CameraWorker(QObject):
    frame_processed = pyqtSignal(object, int, int, str)  # frame, x, y, action
    error_occurred = pyqtSignal(str)

    def __init__(self, config, os_type):
        super().__init__()
        self.config = config
        self.os_type = os_type
        self.running = False
        self._init_core_components()

    def _init_core_components(self):
        """Initialize all computer vision and control components"""
        from core import FaceProcessor, HeadTracker, BlinkDetector
        from core.cursor_controller import MacCursorController, WindowsCursorController
        
        try:
            self.face_processor = FaceProcessor()
            self.cursor = MacCursorController() if self.os_type == "mac" else WindowsCursorController()
            self.head_tracker = HeadTracker(self.config, self.cursor)
            self.blink_detector = BlinkDetector(self.config)
            
            
            
        except Exception as e:
            self.error_occurred.emit(f"Component initialization failed: {str(e)}")

    def start_processing(self):
        """Main processing loop running in background thread"""
        self.running = True
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            self.error_occurred.emit("Could not access camera")
            return

        try:
            while self.running:
                start_time = time.time()
                
                # Capture frame
                ret, frame = self.cap.read()
                if not ret:
                    continue

                # Process frame
                landmarks = self.face_processor.process_frame(frame)
                if not landmarks:
                    continue

                # Head tracking
                x, y = self.head_tracker.update_position(landmarks, frame.shape)
                
                # Blink detection
                action = self.blink_detector.detect(landmarks, frame.shape, self.head_tracker.moving)
                
                # Move actual cursor
                self.cursor.move(int(x), int(y))
                
                # Handle actions
                if action == "single":
                    self.cursor.click(int(x), int(y))
                elif action == "double":
                    self.cursor.double_click(int(x), int(y))
                
                # Calculate FPS
                fps = 1 / (time.time() - start_time + 1e-6)
                
                # Emit results for UI update
                self.frame_processed.emit(frame, int(x), int(y), action)

        except Exception as e:
            self.error_occurred.emit(f"Processing error: {str(e)}")
        finally:
            self.cap.release()

    def stop_processing(self):
        """Cleanup resources"""
        self.running = False
        if hasattr(self, "cap") and self.cap.isOpened():
            self.cap.release()