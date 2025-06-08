import cv2
import threading
import time
from io import BytesIO
import numpy as np

class CameraStream:
    def __init__(self):
        self.camera = None
        self.is_streaming = False
        self.frame = None
        self.lock = threading.Lock()
        self.thread = None
        self.use_fallback = False
        
        # Try to initialize Pi camera first
        try:
            from picamera2 import Picamera2
            self.camera = Picamera2()
            
            # Configure camera for Pi Camera Module 1 on Pi 3
            camera_config = self.camera.create_still_configuration(
                main={"size": (640, 480), "format": "RGB888"}
            )
            self.camera.configure(camera_config)
            print("Pi Camera initialized successfully")
        except ImportError as e:
            print(f"Pi Camera not available (libcamera missing): {e}")
            self._init_fallback_camera()
        except Exception as e:
            print(f"Error initializing Pi Camera: {e}")
            self._init_fallback_camera()
    
    def _init_fallback_camera(self):
        """Initialize fallback camera using OpenCV"""
        try:
            # Try USB camera first
            self.camera = cv2.VideoCapture(0)
            if self.camera.isOpened():
                # Test if we can actually read a frame
                ret, test_frame = self.camera.read()
                if ret and test_frame is not None:
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.use_fallback = True
                    print("USB camera initialized successfully")
                else:
                    print("USB camera opened but cannot read frames")
                    self.camera.release()
                    self.camera = None
                    print("No camera available - using dummy frames")
            else:
                self.camera = None
                print("No camera available - using dummy frames")
        except Exception as e:
            print(f"Error initializing fallback camera: {e}")
            self.camera = None

    def start(self):
        if self.is_streaming:
            print("Camera stream already started, skipping...")
            return
            
        if not self.is_streaming:
            try:
                # Generate initial dummy frame to ensure get_frame() always returns something
                self._generate_dummy_frame()
                
                if self.camera:
                    if not self.use_fallback:
                        # Pi camera
                        self.camera.start()
                    # OpenCV camera is already "started" when opened
                self.is_streaming = True
                self.thread = threading.Thread(target=self._capture_frames)
                self.thread.daemon = True
                self.thread.start()
                print("Camera stream started")
            except Exception as e:
                print(f"Error starting camera: {e}")
                self.is_streaming = False
                # Ensure we have at least a dummy frame
                self._generate_dummy_frame()

    def stop(self):
        if self.is_streaming:
            self.is_streaming = False
            if self.thread:
                self.thread.join()
            if self.camera:
                try:
                    if self.use_fallback:
                        # OpenCV camera
                        self.camera.release()
                    else:
                        # Pi camera
                        self.camera.stop()
                    print("Camera stream stopped")
                except Exception as e:
                    print(f"Error stopping camera: {e}")

    def _capture_frames(self):
        """Capture frames in a separate thread"""
        print(f"Starting frame capture thread, use_fallback={self.use_fallback}, camera={self.camera is not None}")
        
        while self.is_streaming:
            try:
                if self.camera:
                    if self.use_fallback:
                        # OpenCV camera
                        ret, frame_bgr = self.camera.read()
                        if ret:
                            # Encode frame as JPEG
                            _, jpeg = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
                            
                            with self.lock:
                                self.frame = jpeg.tobytes()
                        else:
                            print(f"Failed to read frame from USB camera, ret={ret}")
                            # Fall back to dummy frame if camera read fails
                            self._generate_dummy_frame()
                    else:
                        # Pi camera
                        frame_array = self.camera.capture_array()
                        
                        # Convert RGB to BGR for OpenCV
                        frame_bgr = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
                        
                        # Encode frame as JPEG
                        _, jpeg = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
                        
                        with self.lock:
                            self.frame = jpeg.tobytes()
                else:
                    # No camera - generate dummy frame
                    self._generate_dummy_frame()
                    
                time.sleep(0.033)  # ~30 FPS
            except Exception as e:
                print(f"Error capturing frame: {e}")
                # Generate dummy frame on error
                self._generate_dummy_frame()
                time.sleep(0.1)
    
    def _generate_dummy_frame(self):
        """Generate a dummy frame when no camera is available"""
        try:
            # Create a 640x480 image with text
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            img.fill(50)  # Dark gray background
            
            # Add text
            text = "No Camera Available"
            font = cv2.FONT_HERSHEY_SIMPLEX
            text_size = cv2.getTextSize(text, font, 1, 2)[0]
            text_x = (img.shape[1] - text_size[0]) // 2
            text_y = (img.shape[0] + text_size[1]) // 2
            
            cv2.putText(img, text, (text_x, text_y), font, 1, (255, 255, 255), 2)
            
            # Add timestamp
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(img, timestamp, (10, 30), font, 0.7, (200, 200, 200), 1)
            
            # Encode as JPEG
            _, jpeg = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 80])
            
            with self.lock:
                self.frame = jpeg.tobytes()
        except Exception as e:
            print(f"Error generating dummy frame: {e}")
            # Create minimal valid JPEG frame
            with self.lock:
                # Create a minimal black image
                minimal_img = np.zeros((100, 200, 3), dtype=np.uint8)
                _, minimal_jpeg = cv2.imencode('.jpg', minimal_img)
                self.frame = minimal_jpeg.tobytes()

    def get_frame(self):
        with self.lock:
            return self.frame if self.frame is not None else b''