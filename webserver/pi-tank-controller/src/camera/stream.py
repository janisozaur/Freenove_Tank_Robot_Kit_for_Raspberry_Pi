import cv2
import threading
import time
from io import BytesIO

class CameraStream:
    def __init__(self):
        try:
            from picamera2 import Picamera2
            self.camera = Picamera2()
            
            # Configure camera for Pi Camera Module 1 on Pi 3
            camera_config = self.camera.create_still_configuration(
                main={"size": (640, 480), "format": "RGB888"}
            )
            self.camera.configure(camera_config)
            
            self.is_streaming = False
            self.frame = None
            self.lock = threading.Lock()
            self.thread = None
            print("Camera initialized successfully")
        except Exception as e:
            print(f"Error initializing camera: {e}")
            self.camera = None

    def start(self):
        if self.camera and not self.is_streaming:
            try:
                self.camera.start()
                self.is_streaming = True
                self.thread = threading.Thread(target=self._capture_frames)
                self.thread.daemon = True
                self.thread.start()
                print("Camera stream started")
            except Exception as e:
                print(f"Error starting camera: {e}")

    def stop(self):
        if self.is_streaming:
            self.is_streaming = False
            if self.thread:
                self.thread.join()
            if self.camera:
                try:
                    self.camera.stop()
                    print("Camera stream stopped")
                except Exception as e:
                    print(f"Error stopping camera: {e}")

    def _capture_frames(self):
        while self.is_streaming:
            try:
                # Capture frame as numpy array
                frame_array = self.camera.capture_array()
                
                # Convert RGB to BGR for OpenCV
                frame_bgr = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
                
                # Encode frame as JPEG
                _, jpeg = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
                
                with self.lock:
                    self.frame = jpeg.tobytes()
                    
                time.sleep(0.033)  # ~30 FPS
            except Exception as e:
                print(f"Error capturing frame: {e}")
                time.sleep(0.1)

    def get_frame(self):
        with self.lock:
            return self.frame if self.frame is not None else b''