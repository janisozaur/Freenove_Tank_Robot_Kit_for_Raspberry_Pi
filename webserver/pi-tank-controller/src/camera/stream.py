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
            
            # Try different configuration approaches for compatibility
            try:
                # First try the most basic configuration without specifying format/size
                print("Trying basic preview configuration...")
                camera_config = self.camera.create_preview_configuration()
                self.camera.configure(camera_config)
                print("Pi Camera initialized successfully (basic configuration)")
            except Exception as basic_error:
                print(f"Basic configuration failed: {basic_error}")
                try:
                    # Try with specific size but no format
                    print("Trying preview configuration with size...")
                    camera_config = self.camera.create_preview_configuration(
                        main={"size": (640, 480)}
                    )
                    self.camera.configure(camera_config)
                    print("Pi Camera initialized successfully (size configuration)")
                except Exception as size_error:
                    print(f"Size configuration failed: {size_error}")
                    try:
                        # Try still configuration as fallback
                        print("Trying still configuration...")
                        camera_config = self.camera.create_still_configuration()
                        self.camera.configure(camera_config)
                        print("Pi Camera initialized successfully (still configuration)")
                    except Exception as still_error:
                        print(f"Still configuration failed: {still_error}")
                        # Try to configure with minimal setup
                        try:
                            print("Trying minimal configuration...")
                            # Don't call configure, just try to use the camera as-is
                        except Exception as minimal_error:
                            print(f"Minimal configuration also failed: {minimal_error}")
                            raise minimal_error
                    
        except ImportError as e:
            print(f"Pi Camera not available (libcamera missing): {e}")
            self._init_fallback_camera()
        except Exception as e:
            print(f"Error initializing Pi Camera: {e}")
            self._init_fallback_camera()
    
    def _init_fallback_camera(self):
        """Initialize fallback camera using OpenCV"""
        try:
            # Try multiple camera indices (0, 1, 2) as different systems may have different camera assignments
            for camera_index in [0, 1, 2]:
                print(f"Trying camera index {camera_index}...")
                self.camera = cv2.VideoCapture(camera_index)
                
                if self.camera.isOpened():
                    # Set camera properties before testing
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.camera.set(cv2.CAP_PROP_FPS, 30)
                    
                    # Test if we can actually read a frame
                    print(f"Testing frame read from camera {camera_index}...")
                    ret, test_frame = self.camera.read()
                    
                    if ret and test_frame is not None and test_frame.size > 0:
                        print(f"USB camera {camera_index} initialized successfully")
                        self.use_fallback = True
                        return
                    else:
                        print(f"Camera {camera_index} opened but cannot read frames (ret={ret})")
                        self.camera.release()
                        
                else:
                    print(f"Camera {camera_index} could not be opened")
                    if self.camera:
                        self.camera.release()
            
            # If we get here, no cameras worked
            self.camera = None
            print("No working camera found - using dummy frames")
            
        except Exception as e:
            print(f"Error initializing fallback camera: {e}")
            self.camera = None

    def start(self):
        if self.is_streaming:
            print("Camera stream already started, skipping...")
            return
            
        if not self.is_streaming:
            try:
                print("Starting camera stream...")
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
                print("Camera stream started successfully")
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
                        try:
                            frame_array = self.camera.capture_array()
                            
                            # Handle different formats that might be returned
                            if frame_array is None:
                                raise Exception("capture_array() returned None")
                            
                            # Check if it's already in BGR format or needs conversion
                            if len(frame_array.shape) == 3 and frame_array.shape[2] == 3:
                                # Assume RGB format and convert to BGR for OpenCV
                                frame_bgr = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
                            elif len(frame_array.shape) == 3 and frame_array.shape[2] == 4:
                                # RGBA format, convert to BGR
                                frame_bgr = cv2.cvtColor(frame_array, cv2.COLOR_RGBA2BGR)
                            else:
                                # Unknown format, try to use as-is
                                frame_bgr = frame_array
                            
                            # Encode frame as JPEG
                            _, jpeg = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
                            
                            with self.lock:
                                self.frame = jpeg.tobytes()
                        except Exception as picam_error:
                            print(f"Pi Camera capture error: {picam_error}")
                            # Fall back to dummy frame if Pi camera fails
                            self._generate_dummy_frame()
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