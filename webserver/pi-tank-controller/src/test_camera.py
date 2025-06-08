#!/usr/bin/env python3
"""
Test camera stream functionality
"""

import sys
import os
import time

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from camera.stream import CameraStream

def test_camera_stream():
    print("Testing camera stream...")
    
    # Create camera stream
    camera = CameraStream()
    print(f"Camera initialized: {camera.camera is not None}")
    print(f"Use fallback: {camera.use_fallback}")
    
    # Start streaming
    camera.start()
    print(f"Streaming started: {camera.is_streaming}")
    
    # Wait a moment for capture to start
    time.sleep(2)
    
    # Test getting frames
    for i in range(5):
        frame = camera.get_frame()
        print(f"Frame {i+1}: {'OK' if frame and len(frame) > 0 else 'EMPTY'} ({len(frame) if frame else 0} bytes)")
        time.sleep(0.5)
    
    # Stop streaming
    camera.stop()
    print("Camera stream stopped")

if __name__ == '__main__':
    test_camera_stream()
