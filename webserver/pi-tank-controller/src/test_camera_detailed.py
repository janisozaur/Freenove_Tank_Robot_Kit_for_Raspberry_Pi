#!/usr/bin/env python3

"""
Comprehensive camera testing script for Pi Tank Controller
Tests different camera initialization methods and provides detailed debug info
"""

import sys
import os
import cv2
import numpy as np

def test_libcamera_detection():
    """Test if libcamera is available and working"""
    print("=== Testing libcamera detection ===")
    try:
        import subprocess
        result = subprocess.run(['libcamera-hello', '--list-cameras'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✓ libcamera is available")
            print(f"Camera list output:\n{result.stdout}")
            return True
        else:
            print(f"✗ libcamera command failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error testing libcamera: {e}")
        return False

def test_picamera2_import():
    """Test picamera2 import and basic functionality"""
    print("\n=== Testing picamera2 import ===")
    try:
        from picamera2 import Picamera2
        print("✓ picamera2 imported successfully")
        
        # Try to create instance
        picam2 = Picamera2()
        print("✓ Picamera2 instance created")
        
        return picam2
    except ImportError as e:
        print(f"✗ Cannot import picamera2: {e}")
        return None
    except Exception as e:
        print(f"✗ Error creating Picamera2 instance: {e}")
        return None

def test_picamera2_configurations(picam2):
    """Test different picamera2 configuration methods"""
    print("\n=== Testing picamera2 configurations ===")
    
    if not picam2:
        print("No picamera2 instance available")
        return None
    
    # Test 1: Basic preview configuration
    try:
        print("Testing basic preview configuration...")
        config = picam2.create_preview_configuration()
        print("✓ Basic preview configuration created")
        print(f"Configuration: {config}")
        
        picam2.configure(config)
        print("✓ Basic configuration applied successfully")
        return config
    except Exception as e:
        print(f"✗ Basic preview configuration failed: {e}")
    
    # Test 2: Preview with size
    try:
        print("Testing preview configuration with size...")
        config = picam2.create_preview_configuration(main={"size": (640, 480)})
        print("✓ Size-specific preview configuration created")
        
        picam2.configure(config)
        print("✓ Size configuration applied successfully")
        return config
    except Exception as e:
        print(f"✗ Size preview configuration failed: {e}")
    
    # Test 3: Still configuration
    try:
        print("Testing still configuration...")
        config = picam2.create_still_configuration()
        print("✓ Still configuration created")
        
        picam2.configure(config)
        print("✓ Still configuration applied successfully")
        return config
    except Exception as e:
        print(f"✗ Still configuration failed: {e}")
    
    # Test 4: No explicit configuration
    try:
        print("Testing without explicit configuration...")
        print("✓ Skipping configuration step")
        return "no_config"
    except Exception as e:
        print(f"✗ No configuration approach failed: {e}")
    
    return None

def test_picamera2_capture(picam2, config):
    """Test picamera2 frame capture"""
    print("\n=== Testing picamera2 capture ===")
    
    if not picam2:
        print("No picamera2 instance available")
        return False
    
    try:
        print("Starting camera...")
        picam2.start()
        print("✓ Camera started")
        
        import time
        time.sleep(1)  # Give camera time to warm up
        
        print("Attempting to capture array...")
        frame = picam2.capture_array()
        print(f"✓ Captured frame: shape={frame.shape}, dtype={frame.dtype}")
        
        # Test conversion
        if len(frame.shape) == 3:
            if frame.shape[2] == 3:
                print("Frame appears to be RGB, testing BGR conversion...")
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                print("✓ RGB to BGR conversion successful")
            elif frame.shape[2] == 4:
                print("Frame appears to be RGBA, testing BGR conversion...")
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                print("✓ RGBA to BGR conversion successful")
            else:
                print(f"Unknown frame format with {frame.shape[2]} channels")
                frame_bgr = frame
        else:
            print(f"Unexpected frame shape: {frame.shape}")
            frame_bgr = frame
        
        # Test JPEG encoding
        _, jpeg = cv2.imencode('.jpg', frame_bgr)
        print(f"✓ JPEG encoding successful: {len(jpeg)} bytes")
        
        picam2.stop()
        print("✓ Camera stopped")
        return True
        
    except Exception as e:
        print(f"✗ Capture test failed: {e}")
        try:
            picam2.stop()
        except:
            pass
        return False

def test_opencv_cameras():
    """Test OpenCV camera detection"""
    print("\n=== Testing OpenCV cameras ===")
    
    working_cameras = []
    
    for i in range(5):  # Test indices 0-4
        print(f"Testing camera index {i}...")
        cap = cv2.VideoCapture(i)
        
        if cap.isOpened():
            print(f"  ✓ Camera {i} opened")
            
            # Test frame capture
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                print(f"  ✓ Camera {i} can capture frames: {frame.shape}")
                working_cameras.append(i)
            else:
                print(f"  ✗ Camera {i} cannot capture frames")
            
            cap.release()
        else:
            print(f"  ✗ Camera {i} cannot be opened")
    
    print(f"Working OpenCV cameras: {working_cameras}")
    return working_cameras

def test_camera_stream():
    """Test our CameraStream class"""
    print("\n=== Testing CameraStream class ===")
    
    # Add the current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from camera.stream import CameraStream
        
        print("Creating CameraStream instance...")
        camera = CameraStream()
        print(f"✓ CameraStream created")
        print(f"  Camera object: {camera.camera is not None}")
        print(f"  Use fallback: {camera.use_fallback}")
        
        print("Starting camera stream...")
        camera.start()
        print(f"✓ Stream started: {camera.is_streaming}")
        
        import time
        time.sleep(2)  # Wait for first frames
        
        print("Testing frame capture...")
        for i in range(3):
            frame = camera.get_frame()
            if frame and len(frame) > 0:
                print(f"  ✓ Frame {i+1}: {len(frame)} bytes")
            else:
                print(f"  ✗ Frame {i+1}: empty")
            time.sleep(0.5)
        
        camera.stop()
        print("✓ Camera stream stopped")
        return True
        
    except Exception as e:
        print(f"✗ CameraStream test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Pi Tank Controller - Comprehensive Camera Test")
    print("=" * 50)
    
    # Test libcamera
    libcamera_ok = test_libcamera_detection()
    
    # Test picamera2
    picam2 = test_picamera2_import()
    
    if picam2:
        config = test_picamera2_configurations(picam2)
        if config:
            test_picamera2_capture(picam2, config)
    
    # Test OpenCV cameras
    opencv_cameras = test_opencv_cameras()
    
    # Test our camera stream implementation
    camera_stream_ok = test_camera_stream()
    
    print("\n=== FINAL SUMMARY ===")
    print(f"libcamera available: {libcamera_ok}")
    print(f"picamera2 available: {picam2 is not None}")
    print(f"Working OpenCV cameras: {opencv_cameras}")
    print(f"CameraStream working: {camera_stream_ok}")
    
    if not libcamera_ok and not opencv_cameras:
        print("\n⚠️  No working cameras found!")
        print("Suggestions:")
        print("- Check camera module connection")
        print("- Run 'sudo raspi-config' and enable camera")
        print("- Install camera dependencies: sudo apt-get install libcamera-dev libcamera-tools")
        print("- Try connecting a USB camera")
    elif libcamera_ok and not picam2:
        print("\n⚠️  libcamera detected but picamera2 not working")
        print("Try: pip install picamera2 --upgrade")
    elif opencv_cameras:
        print(f"\n✓ OpenCV cameras available as fallback: {opencv_cameras}")
    
    if camera_stream_ok:
        print("\n✓ CameraStream is working - the web server should be able to stream video!")
    else:
        print("\n⚠️  CameraStream not working - check individual component tests above")

if __name__ == "__main__":
    main()
