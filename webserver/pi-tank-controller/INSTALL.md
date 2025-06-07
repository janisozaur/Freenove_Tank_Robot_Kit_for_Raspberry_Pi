# Quick Installation Guide for Raspberry Pi

## Prerequisites
- Raspberry Pi 3 with Raspberry Pi OS
- Pi Camera Module 1 connected
- Freenove Tank Robot Kit assembled with PCB v1
- Internet connection

## One-Command Installation

```bash
# Copy this entire command and paste it into your Pi terminal:
cd /home/pi && \
curl -L https://github.com/yourusername/repository/archive/main.zip -o tank.zip && \
unzip tank.zip && \
cd Freenove_Tank_Robot_Kit_for_Raspberry_Pi/webserver/pi-tank-controller && \
chmod +x start_server.sh && \
./start_server.sh
```

## Manual Installation Steps

1. **Enable Camera Interface:**
   ```bash
   sudo raspi-config
   # Interface Options > Camera > Enable
   sudo reboot
   ```

2. **Clone Repository:**
   ```bash
   cd /home/pi
   git clone [REPOSITORY_URL]
   cd Freenove_Tank_Robot_Kit_for_Raspberry_Pi/webserver/pi-tank-controller
   ```

3. **Run Startup Script:**
   ```bash
   chmod +x start_server.sh
   ./start_server.sh
   ```

4. **Access Web Interface:**
   - Find your Pi's IP: `hostname -I`
   - Open browser: `http://[PI_IP]:5000`

## Troubleshooting

### Camera Not Working
```bash
# Test camera
libcamera-hello --list-cameras

# If no camera found
sudo raspi-config  # Enable camera interface
sudo reboot
```

### Motors Not Working
```bash
# Check GPIO permissions
groups $USER

# If 'gpio' not in groups
sudo usermod -a -G gpio pi
# Log out and back in
```

### Can't Access Web Interface
```bash
# Check if server is running
sudo netstat -tlnp | grep :5000

# Check firewall (if enabled)
sudo ufw allow 5000
```

### Performance Issues
- Reduce camera resolution in `src/camera/stream.py`
- Lower frame rate by increasing sleep time
- Close other applications

## Default Controls

| Control | Action |
|---------|--------|
| W/↑ | Forward |
| S/↓ | Backward |
| A/← | Turn Left |
| D/→ | Turn Right |
| Space | Stop |
| Gamepad Left Stick | Tank movement |
| Gamepad A Button | Emergency stop |

## GPIO Pins (PCB v1)
- Left Motor: GPIO 23 (forward), GPIO 24 (backward)
- Right Motor: GPIO 6 (forward), GPIO 5 (backward)

## Support
- Check README.md for detailed documentation
- Test individual components using the test scripts
- Ensure hardware connections match PCB v1 pinout
