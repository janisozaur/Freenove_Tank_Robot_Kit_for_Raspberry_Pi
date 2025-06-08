// Modern Tank Controller JavaScript with Gamepad Support
class TankController {
    constructor() {
        this.gamepadIndex = null;
        this.isGamepadConnected = false;
        this.lastCommandTime = 0;
        this.commandCooldown = 50; // ms
        this.deadzone = 0.1;
        
        this.initializeEventListeners();
        this.startGamepadPolling();
        this.updateStatus();
    }

    initializeEventListeners() {
        // Button controls
        document.getElementById('forward').addEventListener('mousedown', () => this.sendCommand('forward'));
        document.getElementById('backward').addEventListener('mousedown', () => this.sendCommand('backward'));
        document.getElementById('left').addEventListener('mousedown', () => this.sendCommand('left'));
        document.getElementById('right').addEventListener('mousedown', () => this.sendCommand('right'));
        document.getElementById('stop').addEventListener('click', () => this.sendCommand('stop'));
        
        // Stop on button release
        ['forward', 'backward', 'left', 'right'].forEach(direction => {
            document.getElementById(direction).addEventListener('mouseup', () => this.sendCommand('stop'));
            document.getElementById(direction).addEventListener('mouseleave', () => this.sendCommand('stop'));
        });
        
        // Crane controls
        document.getElementById('crane-up').addEventListener('mousedown', () => this.sendCraneCommand('crane_up'));
        document.getElementById('crane-down').addEventListener('mousedown', () => this.sendCraneCommand('crane_down'));
        document.getElementById('grabber-open').addEventListener('click', () => this.sendCraneCommand('grabber_open'));
        document.getElementById('grabber-close').addEventListener('click', () => this.sendCraneCommand('grabber_close'));
        
        // Stop crane on button release
        ['crane-up', 'crane-down'].forEach(direction => {
            document.getElementById(direction).addEventListener('mouseup', () => this.sendCraneCommand('crane_stop'));
            document.getElementById(direction).addEventListener('mouseleave', () => this.sendCraneCommand('crane_stop'));
        });

        // Keyboard controls
        document.addEventListener('keydown', this.handleKeyDown.bind(this));
        document.addEventListener('keyup', this.handleKeyUp.bind(this));

        // Virtual tank controls
        const leftTrack = document.getElementById('left-track');
        const rightTrack = document.getElementById('right-track');
        
        leftTrack.addEventListener('input', this.handleVirtualSticks.bind(this));
        rightTrack.addEventListener('input', this.handleVirtualSticks.bind(this));

        // Gamepad connection events
        window.addEventListener("gamepadconnected", this.onGamepadConnected.bind(this));
        window.addEventListener("gamepaddisconnected", this.onGamepadDisconnected.bind(this));
    }

    handleKeyDown(event) {
        switch(event.code) {
            case 'ArrowUp':
            case 'KeyW':
                event.preventDefault();
                this.sendCommand('forward');
                break;
            case 'ArrowDown':
            case 'KeyS':
                event.preventDefault();
                this.sendCommand('backward');
                break;
            case 'ArrowLeft':
            case 'KeyA':
                event.preventDefault();
                this.sendCommand('left');
                break;
            case 'ArrowRight':
            case 'KeyD':
                event.preventDefault();
                this.sendCommand('right');
                break;
            case 'Space':
                event.preventDefault();
                this.sendCommand('stop');
                break;
            case 'KeyQ':
                event.preventDefault();
                this.sendCraneCommand('crane_up');
                break;
            case 'KeyE':
                event.preventDefault();
                this.sendCraneCommand('crane_down');
                break;
            case 'KeyR':
                event.preventDefault();
                this.sendCraneCommand('grabber_open');
                break;
            case 'KeyF':
                event.preventDefault();
                this.sendCraneCommand('grabber_close');
                break;
        }
    }

    handleKeyUp(event) {
        switch(event.code) {
            case 'ArrowUp':
            case 'KeyW':
            case 'ArrowDown':
            case 'KeyS':
            case 'ArrowLeft':
            case 'KeyA':
            case 'ArrowRight':
            case 'KeyD':
                event.preventDefault();
                this.sendCommand('stop');
                break;
            case 'KeyQ':
            case 'KeyE':
                event.preventDefault();
                this.sendCraneCommand('crane_stop');
                break;
        }
    }

    handleVirtualSticks() {
        const leftValue = parseInt(document.getElementById('left-track').value);
        const rightValue = parseInt(document.getElementById('right-track').value);
        
        // Update display values
        document.getElementById('left-value').textContent = leftValue;
        document.getElementById('right-value').textContent = rightValue;
        
        // Send to server
        this.sendGamepadControl(leftValue / 100.0, rightValue / 100.0);
    }

    onGamepadConnected(event) {
        console.log("Gamepad connected:", event.gamepad.id);
        this.gamepadIndex = event.gamepad.index;
        this.isGamepadConnected = true;
        this.updateGamepadStatus();
    }

    onGamepadDisconnected(event) {
        console.log("Gamepad disconnected:", event.gamepad.id);
        this.gamepadIndex = null;
        this.isGamepadConnected = false;
        this.updateGamepadStatus();
    }

    startGamepadPolling() {
        const pollGamepad = () => {
            if (this.isGamepadConnected && this.gamepadIndex !== null) {
                this.updateGamepadInput();
            }
            requestAnimationFrame(pollGamepad);
        };
        pollGamepad();
    }

    updateGamepadInput() {
        const gamepads = navigator.getGamepads();
        const gamepad = gamepads[this.gamepadIndex];
        
        if (!gamepad) return;

        const now = Date.now();
        if (now - this.lastCommandTime < this.commandCooldown) return;

        // Read analog sticks
        const leftStickY = this.applyDeadzone(gamepad.axes[1]);   // Left stick Y
        const rightStickY = gamepad.axes[3] !== undefined ? 
                           this.applyDeadzone(gamepad.axes[3]) :  // Right stick Y (if available)
                           this.applyDeadzone(gamepad.axes[1]);   // Use left stick if no right stick

        // If no right stick, use left stick X for turning
        if (gamepad.axes[3] === undefined) {
            const leftStickX = this.applyDeadzone(gamepad.axes[0]);
            
            // Tank-style control: forward/back + turning
            const leftTrack = leftStickY - leftStickX;
            const rightTrack = leftStickY + leftStickX;
            
            // Normalize values
            const maxVal = Math.max(Math.abs(leftTrack), Math.abs(rightTrack), 1.0);
            this.sendGamepadControl(leftTrack / maxVal, rightTrack / maxVal);
        } else {
            // Dual stick tank control
            this.sendGamepadControl(leftStickY, rightStickY);
        }

        // Handle buttons
        if (gamepad.buttons[0] && gamepad.buttons[0].pressed) { // A button - stop
            this.sendCommand('stop');
        }
        if (gamepad.buttons[1] && gamepad.buttons[1].pressed) { // B button - crane up
            this.sendCraneCommand('crane_up');
        }
        if (gamepad.buttons[2] && gamepad.buttons[2].pressed) { // X button - crane down
            this.sendCraneCommand('crane_down');
        }
        if (gamepad.buttons[3] && gamepad.buttons[3].pressed) { // Y button - grabber toggle
            this.toggleGrabber();
        }

        this.lastCommandTime = now;
    }

    applyDeadzone(value) {
        if (Math.abs(value) < this.deadzone) {
            return 0.0;
        }
        
        // Scale the remaining range to -1 to 1
        if (value > 0) {
            return (value - this.deadzone) / (1.0 - this.deadzone);
        } else {
            return (value + this.deadzone) / (1.0 - this.deadzone);
        }
    }

    sendCommand(command) {
        fetch('/control', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ command: command }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status !== 'success') {
                console.error('Command failed:', data.message);
            }
        })
        .catch(error => {
            console.error('Error sending command:', error);
        });
    }

    sendCraneCommand(command) {
        fetch('/crane_control', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ command: command }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status !== 'success') {
                console.error('Crane command failed:', data.message);
            }
            this.updateCraneStatus();
        })
        .catch(error => {
            console.error('Error sending crane command:', error);
        });
    }

    toggleGrabber() {
        // Get current grabber status and toggle
        fetch('/crane_status')
        .then(response => response.json())
        .then(data => {
            if (data.grabber_position === 'open') {
                this.sendCraneCommand('grabber_close');
            } else {
                this.sendCraneCommand('grabber_open');
            }
        })
        .catch(error => {
            console.error('Error getting crane status:', error);
        });
    }

    updateCraneStatus() {
        fetch('/crane_status')
        .then(response => response.json())
        .then(data => {
            if (data.crane_position) {
                document.getElementById('crane-position').textContent = data.crane_position;
            }
            if (data.grabber_position) {
                document.getElementById('grabber-position').textContent = data.grabber_position;
            }
        })
        .catch(error => {
            console.error('Error updating crane status:', error);
        });
    }

    sendGamepadControl(leftStickY, rightStickY) {
        fetch('/gamepad_control', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                left_stick_y: leftStickY,
                right_stick_y: rightStickY
            }),
        })
        .catch(error => {
            console.error('Error sending gamepad control:', error);
        });
    }

    updateGamepadStatus() {
        const statusElement = document.getElementById('gamepad-connected');
        const infoElement = document.getElementById('gamepad-info');
        
        if (this.isGamepadConnected) {
            const gamepads = navigator.getGamepads();
            const gamepad = gamepads[this.gamepadIndex];
            
            statusElement.textContent = 'Gamepad Connected ✅';
            statusElement.style.color = '#4a90e2';
            
            if (gamepad) {
                infoElement.innerHTML = `
                    <p><strong>Name:</strong> ${gamepad.id}</p>
                    <p><strong>Buttons:</strong> ${gamepad.buttons.length}</p>
                    <p><strong>Axes:</strong> ${gamepad.axes.length}</p>
                `;
            }
        } else {
            statusElement.textContent = 'No Gamepad Connected ❌';
            statusElement.style.color = '#e74c3c';
            infoElement.innerHTML = '<p>Connect a gamepad for enhanced control</p>';
        }
    }

    updateStatus() {
        fetch('/status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('camera-status').textContent = 
                    data.camera_streaming ? 'Active ✅' : 'Inactive ❌';
                
                if (data.gamepad_status && data.gamepad_status.motor_speeds) {
                    document.getElementById('motor-left').textContent = 
                        data.gamepad_status.motor_speeds.left || 0;
                    document.getElementById('motor-right').textContent = 
                        data.gamepad_status.motor_speeds.right || 0;
                }
                
                // Update crane status
                if (data.gamepad_status && data.gamepad_status.crane_status) {
                    const craneStatus = data.gamepad_status.crane_status;
                    document.getElementById('crane-position').textContent = 
                        craneStatus.crane_position || 'Unknown';
                    document.getElementById('grabber-position').textContent = 
                        craneStatus.grabber_position || 'Unknown';
                }
            })
            .catch(error => {
                console.error('Error updating status:', error);
            });
        
        // Update status every 2 seconds
        setTimeout(() => this.updateStatus(), 2000);
    }
}

// Initialize the tank controller when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const tankController = new TankController();
    
    // Make it globally available for debugging
    window.tankController = tankController;
    
    console.log('Tank Controller initialized');
    console.log('Controls:');
    console.log('- Arrow keys or WASD for movement');
    console.log('- Space bar to stop');
    console.log('- Q/E for crane up/down');
    console.log('- R for grabber open, F for grabber close');
    console.log('- Mouse buttons for manual control');
    console.log('- Connect a gamepad for analog control');
    console.log('- Gamepad: A=stop, B=crane up, X=crane down, Y=toggle grabber');
});