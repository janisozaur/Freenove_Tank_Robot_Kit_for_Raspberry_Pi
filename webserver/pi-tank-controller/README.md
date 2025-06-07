# Pi Tank Controller Web Server

A modern Python-based web server for controlling the Freenove Tank Robot Kit with real-time camera streaming and gamepad support.

## Features

- **Real-time Camera Streaming**: Live video feed from Pi Camera Module 1
- **Gamepad Control**: Support for USB/Bluetooth gamepads with analog stick controls
- **Web Interface**: Modern responsive UI with virtual tank controls
- **Tank-Style Movement**: Independent left/right track control for precise maneuvering
- **Keyboard Controls**: WASD/Arrow keys for quick control
- **Status Monitoring**: Real-time display of system and motor status

## Hardware Requirements

- Raspberry Pi 3
- Pi Camera Module 1
- Freenove Tank Robot Kit PCB v1
- USB or Bluetooth Gamepad (optional)
- Tank motors connected to GPIO pins 23, 24 (left) and 6, 5 (right)

## Software Requirements

- Raspberry Pi OS (Bullseye or newer recommended)
- Python 3.7+
- Camera interface enabled

## Installation

### 1. Enable Camera Interface

```bash
sudo raspi-config
# Navigate to Interface Options > Camera > Enable
sudo reboot
```

### 2. Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv libcamera-dev
sudo apt install -y python3-opencv python3-numpy
```

### 3. Create Virtual Environment

```bash
cd /home/pi
git clone <repository-url>
cd Freenove_Tank_Robot_Kit_for_Raspberry_Pi/webserver/pi-tank-controller
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. GPIO Permissions (if needed)

```bash
sudo usermod -a -G gpio pi
```

## Configuration

### GPIO Pin Configuration (PCB v1)

The motor control is configured for Freenove Tank Robot Kit PCB v1:

- Left Motor: GPIO 23 (forward), GPIO 24 (backward)
- Right Motor: GPIO 6 (forward), GPIO 5 (backward)

If your setup uses different pins, modify `src/tank/motor_control.py`:

```python
# In TankMotorControl.__init__()
self.left_motor = Motor(23, 24)   # Change these pins
self.right_motor = Motor(6, 5)    # Change these pins
```

### Camera Configuration

The camera is configured for Pi Camera Module 1 with 640x480 resolution. To modify:

```python
# In src/camera/stream.py
camera_config = self.camera.create_still_configuration(
    main={"size": (640, 480), "format": "RGB888"}  # Modify size here
)
```

## Usage

### Starting the Server

```bash
cd /home/pi/Freenove_Tank_Robot_Kit_for_Raspberry_Pi/webserver/pi-tank-controller
source venv/bin/activate
python src/app.py
```

The server will start on `http://0.0.0.0:5000`

### Accessing the Web Interface

1. **Local Access**: Open `http://localhost:5000` on the Raspberry Pi
2. **Network Access**: Find your Pi's IP address and open `http://[PI_IP]:5000`

### Control Methods

#### Web Interface
- Click directional buttons for basic movement
- Use virtual tank controls for independent track control
- View real-time camera stream and system status

#### Keyboard Controls
- **W/↑**: Forward
- **S/↓**: Backward  
- **A/←**: Turn Left
- **D/→**: Turn Right
- **Space**: Stop

#### Gamepad Controls
- **Left Stick**: Tank movement (Y-axis for forward/back, X-axis for turning)
- **Right Stick**: Independent right track control (if available)
- **A Button**: Emergency stop

## API Endpoints

- `GET /`: Main web interface
- `GET /video_feed`: Camera stream endpoint
- `POST /control`: Send movement commands
- `POST /gamepad_control`: Send analog gamepad input
- `GET /status`: Get system status

### Example API Usage

```bash
# Send movement command
curl -X POST http://[PI_IP]:5000/control \
  -H "Content-Type: application/json" \
  -d '{"command": "forward"}'

# Send gamepad input
curl -X POST http://[PI_IP]:5000/gamepad_control \
  -H "Content-Type: application/json" \
  -d '{"left_stick_y": 0.5, "right_stick_y": 0.5}'
```

## Testing Components

### Test Camera Stream

```bash
python src/camera/stream.py
```

### Test Motor Control

```bash
python src/tank/motor_control.py
```

### Test Gamepad Controller

```bash
python src/gamepad/controller.py
```

## Troubleshooting

### Camera Issues

```bash
# Check camera detection
libcamera-hello --list-cameras

# Test camera capture
libcamera-still -o test.jpg
```

### GPIO/Motor Issues

```bash
# Check GPIO permissions
groups $USER

# Test GPIO manually
python3 -c "from gpiozero import LED; led = LED(23); led.on()"
```

### Network Access Issues

```bash
# Find Pi IP address
hostname -I

# Check if port is open
sudo netstat -tlnp | grep :5000
```

### Performance Optimization

For better performance on Raspberry Pi 3:

1. **Reduce Camera Resolution**:
   ```python
   main={"size": (320, 240), "format": "RGB888"}
   ```

2. **Lower Frame Rate**:
   ```python
   time.sleep(0.05)  # 20 FPS instead of 30
   ```

3. **Disable Debug Mode**:
   ```python
   app.run(host='0.0.0.0', port=5000, debug=False)
   ```

## Auto-Start on Boot

Create a systemd service:

```bash
sudo nano /etc/systemd/system/tank-controller.service
```

```ini
[Unit]
Description=Pi Tank Controller
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Freenove_Tank_Robot_Kit_for_Raspberry_Pi/webserver/pi-tank-controller
ExecStart=/home/pi/Freenove_Tank_Robot_Kit_for_Raspberry_Pi/webserver/pi-tank-controller/venv/bin/python src/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable tank-controller.service
sudo systemctl start tank-controller.service
```

## Development

### Project Structure

```
src/
├── app.py              # Main Flask application
├── camera/
│   └── stream.py       # Camera streaming module
├── gamepad/
│   └── controller.py   # Gamepad input handling
└── tank/
    └── motor_control.py # Motor control module
static/
├── css/
│   └── style.css       # Modern UI styles
└── js/
    └── gamepad.js      # Frontend gamepad support
templates/
└── index.html          # Main web interface
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Test on actual hardware
4. Submit a pull request

## License

This project is part of the Freenove Tank Robot Kit and follows the original license terms.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the original Freenove documentation
3. Create an issue with hardware details and error logs