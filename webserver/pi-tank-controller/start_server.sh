#!/bin/bash

# Pi Tank Controller Startup Script
# This script sets up the environment and starts the tank controller web server

echo "=== Pi Tank Controller Startup ==="
echo "Initializing tank controller web server..."

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    echo "Virtual environment created."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if camera is enabled
# echo "Checking camera interface..."
# if ! vcgencmd get_camera | grep -q "detected=1"; then
#     echo "WARNING: Camera not detected. Please enable camera interface:"
#     echo "  sudo raspi-config"
#     echo "  Navigate to Interface Options > Camera > Enable"
#     echo "  Then reboot: sudo reboot"
# fi

# Check GPIO permissions
echo "Checking GPIO permissions..."
if ! groups $USER | grep -q gpio; then
    echo "WARNING: User not in GPIO group. Adding user to GPIO group:"
    sudo usermod -a -G gpio $USER
    echo "Please log out and log back in for changes to take effect."
fi

# Get IP address for access instructions
IP_ADDRESS=$(hostname -I | awk '{print $1}')

echo ""
echo "=== Starting Tank Controller Web Server ==="
echo "Camera: Pi Camera Module 1"
echo "GPIO Pins: Left Motor (23,24), Right Motor (6,5)"
echo ""
echo "Access the web interface at:"
echo "  Local: http://localhost:5000"
echo "  Network: http://$IP_ADDRESS:5000"
echo ""
echo "Controls:"
echo "  - Web buttons for basic movement"
echo "  - WASD/Arrow keys for keyboard control"
echo "  - Connect gamepad for analog control"
echo "  - Space bar for emergency stop"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo ""

# Start the Flask application
cd src
python app.py
