#!/bin/bash

# Pi Tank Controller Installation Script
echo "Installing Pi Tank Controller dependencies..."

# Update system
echo "Updating system packages..."
sudo apt update

# Install system dependencies for camera and GPIO
echo "Installing system dependencies..."
sudo apt install -y python3-pip python3-venv libcamera-dev libcamera-tools

# Install uv (fast Python package installer)
echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment with uv..."
    uv venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies using uv
echo "Installing Python dependencies with uv..."
uv pip install -r requirements.txt

# Additional picamera2 installation with specific flags for Pi
echo "Installing picamera2 with Pi optimizations..."
uv pip install --upgrade picamera2[gui]

echo "Testing camera functionality..."
python3 src/test_camera_detailed.py

echo "Creating startup script..."
cat > start_tank_server.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 src/app.py
EOF

chmod +x start_tank_server.sh
echo "Created start_tank_server.sh script"

echo "Installation complete!"
echo ""
echo "To run the server:"
echo "  source venv/bin/activate"
echo "  python3 src/app.py"
echo ""
echo "Or use the new startup script:"
echo "  ./start_tank_server.sh"
