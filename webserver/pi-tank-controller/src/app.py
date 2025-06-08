from flask import Flask, render_template, Response, request, jsonify
from camera.stream import CameraStream
from gamepad.controller import GamepadController
from tank.crane_control import CraneControl
import signal
import sys
import os
import time

# Get the directory containing this script
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to the pi-tank-controller directory
project_root = os.path.dirname(current_dir)

app = Flask(__name__, 
           template_folder=os.path.join(project_root, 'templates'),
           static_folder=os.path.join(project_root, 'static'))

# Initialize components
camera_stream = CameraStream()
crane_control = CraneControl()
gamepad_controller = GamepadController(crane_control=crane_control)

# Flag to prevent multiple starts
_components_started = False

def signal_handler(sig, frame):
    """Handle shutdown gracefully"""
    global _components_started
    print('\nShutting down gracefully...')
    camera_stream.stop()
    gamepad_controller.close()
    crane_control.close()
    _components_started = False
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

@app.route('/')
def index():
    """Main page with camera stream and controls"""
    return render_template('index.html')

def generate_frames():
    """Generate video frames for streaming"""
    while True:
        try:
            frame = camera_stream.get_frame()
            if frame and len(frame) > 0:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                # If no frame is available, wait a bit and try again
                time.sleep(0.1)
        except Exception as e:
            print(f"Error in generate_frames: {e}")
            time.sleep(0.1)

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/control', methods=['POST'])
def control():
    """Handle tank control commands from web interface"""
    try:
        data = request.get_json()
        command = data.get('command') if data else request.form.get('command')
        
        if command:
            gamepad_controller.handle_command(command)
            return jsonify({'status': 'success', 'command': command})
        else:
            return jsonify({'status': 'error', 'message': 'No command provided'}), 400
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/status')
def status():
    """Get current system status"""
    try:
        return jsonify({
            'camera_streaming': camera_stream.is_streaming,
            'gamepad_status': gamepad_controller.get_status()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/gamepad_control', methods=['POST'])
def gamepad_control():
    """Handle direct gamepad input from web interface"""
    try:
        data = request.get_json()
        left_stick_y = data.get('left_stick_y', 0)
        right_stick_y = data.get('right_stick_y', 0)
        
        gamepad_controller.motor_control.handle_gamepad_input(left_stick_y, right_stick_y)
        return jsonify({'status': 'success'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/crane_control', methods=['POST'])
def crane_control_endpoint():
    """Handle crane and grabber control commands"""
    try:
        data = request.get_json()
        command = data.get('command') if data else request.form.get('command')
        
        if command:
            # Handle via gamepad controller which has crane control integration
            success = gamepad_controller.handle_command(command)
            return jsonify({'status': 'success', 'command': command})
        else:
            return jsonify({'status': 'error', 'message': 'No command provided'}), 400
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/crane_status')
def crane_status():
    """Get current crane and grabber status"""
    try:
        status = crane_control.get_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    global _components_started
    
    print("Starting Pi Tank Controller Web Server...")
    
    try:
        # Only start components once
        if not _components_started:
            # Start camera stream
            camera_stream.start()
            print("Camera stream started")
            
            # Start gamepad controller
            gamepad_controller.start()
            print("Gamepad controller started")
            
            _components_started = True
        else:
            print("Components already started, skipping initialization...")

        print("Web server starting on http://0.0.0.0:5000")
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True, use_reloader=False)
        
    except Exception as e:
        print(f"Error starting web server: {e}")
    except KeyboardInterrupt:
        print("\nReceived shutdown signal")
    finally:
        global _components_started
        print("Cleaning up...")
        try:
            camera_stream.stop()
        except Exception as e:
            print(f"Error stopping camera: {e}")
        try:
            gamepad_controller.close()
        except Exception as e:
            print(f"Error closing gamepad: {e}")
        try:
            crane_control.close()
        except Exception as e:
            print(f"Error closing crane control: {e}")
        
        _components_started = False