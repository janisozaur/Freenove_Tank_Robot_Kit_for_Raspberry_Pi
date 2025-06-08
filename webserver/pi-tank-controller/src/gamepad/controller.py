import pygame
import threading
import time
from tank.motor_control import TankMotorControl
from tank.crane_control import CraneControl

class GamepadController:
    def __init__(self):
        """Initialize gamepad controller with pygame"""
        self.motor_control = TankMotorControl()
        self.crane_control = CraneControl()
        self.running = False
        self.thread = None
        self.gamepad = None
        self.pygame_initialized = False
        
        # Initialize pygame
        try:
            pygame.init()
            pygame.joystick.init()
            # Initialize pygame display to avoid "video system not initialized" error
            try:
                pygame.display.init()
                # Create a minimal display surface
                pygame.display.set_mode((1, 1), pygame.NOFRAME)
            except:
                # If display init fails, continue without it
                pass
            
            self.pygame_initialized = True
            print(f"Number of joysticks: {pygame.joystick.get_count()}")
            
            if pygame.joystick.get_count() > 0:
                self.gamepad = pygame.joystick.Joystick(0)
                self.gamepad.init()
                print(f"Gamepad connected: {self.gamepad.get_name()}")
            else:
                print("No gamepad detected")
                
        except Exception as e:
            print(f"Error initializing gamepad: {e}")
            self.pygame_initialized = False
            
        # Button and axis states
        self.button_states = {}
        self.axis_states = {}
        
        # Deadzone for analog sticks
        self.deadzone = 0.1

    def start(self):
        """Start gamepad input thread"""
        if self.running:
            print("Gamepad controller already started, skipping...")
            return
            
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._input_loop)
            self.thread.daemon = True
            self.thread.start()
            print("Gamepad controller started")

    def stop(self):
        """Stop gamepad input thread"""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            self.motor_control.stop()
            print("Gamepad controller stopped")

    def _apply_deadzone(self, value, deadzone=None):
        """Apply deadzone to analog stick values"""
        if deadzone is None:
            deadzone = self.deadzone
        
        if abs(value) < deadzone:
            return 0.0
        
        # Scale the remaining range to -1 to 1
        if value > 0:
            return (value - deadzone) / (1.0 - deadzone)
        else:
            return (value + deadzone) / (1.0 - deadzone)

    def _input_loop(self):
        """Main input processing loop"""
        if not self.pygame_initialized:
            print("Pygame not initialized, skipping input loop")
            return
            
        clock = pygame.time.Clock()
        
        while self.running:
            try:
                pygame.event.pump()
                
                if self.gamepad:
                    # Read analog sticks for tank-style control
                    left_stick_y = self.gamepad.get_axis(1)   # Left stick Y-axis
                    right_stick_y = self.gamepad.get_axis(4) if self.gamepad.get_numaxes() > 4 else 0  # Right stick Y-axis (if available)
                    
                    # Apply deadzone
                    left_stick_y = self._apply_deadzone(left_stick_y)
                    
                    # If no right stick, use left stick X for turning
                    if self.gamepad.get_numaxes() < 5:
                        left_stick_x = self.gamepad.get_axis(0)  # Left stick X-axis
                        left_stick_x = self._apply_deadzone(left_stick_x)
                        
                        # Tank-style control: forward/back + turning
                        left_track = left_stick_y - left_stick_x
                        right_track = left_stick_y + left_stick_x
                        
                        # Normalize values
                        max_val = max(abs(left_track), abs(right_track), 1.0)
                        left_track /= max_val
                        right_track /= max_val
                    else:
                        # Dual stick tank control
                        right_stick_y = self._apply_deadzone(right_stick_y)
                        left_track = left_stick_y
                        right_track = right_stick_y
                        right_track = right_stick_y
                    
                    # Send to motor control
                    self.motor_control.handle_gamepad_input(left_track, right_track)
                    
                    # Update axis states
                    self.axis_states = {
                        'left_stick_y': left_stick_y,
                        'right_stick_y': right_stick_y if 'right_stick_y' in locals() else 0,
                        'left_track': left_track,
                        'right_track': right_track
                    }
                    
                    # Read buttons
                    button_count = self.gamepad.get_numbuttons()
                    for i in range(button_count):
                        self.button_states[f'button_{i}'] = self.gamepad.get_button(i)
                    
                    # Handle specific button actions
                    if self.button_states.get('button_0', False):  # A button (stop)
                        self.motor_control.stop()
                    
                    # Crane controls using gamepad buttons
                    if self.button_states.get('button_1', False):  # B button (crane up)
                        self.crane_control.lift_crane()
                    if self.button_states.get('button_2', False):  # X button (crane down)  
                        self.crane_control.lower_crane()
                    if self.button_states.get('button_3', False):  # Y button (grabber toggle)
                        # Simple toggle based on current position
                        status = self.crane_control.get_status()
                        if status['grabber_position'] == 'open':
                            self.crane_control.close_grabber()
                        else:
                            self.crane_control.open_grabber()
                
                clock.tick(60)  # 60 FPS
                
            except Exception as e:
                print(f"Error in gamepad input loop: {e}")
                time.sleep(0.1)

    def handle_command(self, command):
        """Handle web-based commands"""
        try:
            # Tank movement commands
            if command == 'forward':
                self.motor_control.move_forward()
            elif command == 'backward':
                self.motor_control.move_backward()
            elif command == 'left':
                self.motor_control.turn_left()
            elif command == 'right':
                self.motor_control.turn_right()
            elif command == 'stop':
                self.motor_control.stop()
            # Crane control commands
            elif command == 'crane_up':
                self.crane_control.lift_crane()
            elif command == 'crane_down':
                self.crane_control.lower_crane()
            elif command == 'grabber_open':
                self.crane_control.open_grabber()
            elif command == 'grabber_close':
                self.crane_control.close_grabber()
            elif command == 'crane_stop':
                self.crane_control.stop_crane()
            elif command == 'grabber_stop':
                self.crane_control.stop_grabber()
            else:
                print(f"Unknown command: {command}")
        except Exception as e:
            print(f"Error handling command {command}: {e}")

    def get_status(self):
        """Get current gamepad and motor status"""
        motor_status = {
            'left': self.motor_control.current_left_speed,
            'right': self.motor_control.current_right_speed
        }
        
        crane_status = self.crane_control.get_status() if self.crane_control else {}
        
        return {
            'gamepad_connected': self.gamepad is not None,
            'gamepad_name': self.gamepad.get_name() if self.gamepad else None,
            'button_states': self.button_states,
            'axis_states': self.axis_states,
            'motor_speeds': motor_status,
            'crane_status': crane_status
        }

    def close(self):
        """Clean up resources"""
        try:
            self.stop()
        except Exception as e:
            print(f"Error stopping gamepad controller: {e}")
        
        try:
            self.motor_control.close()
        except Exception as e:
            print(f"Error closing motor control: {e}")
            
        try:
            if self.crane_control:
                self.crane_control.close()
        except Exception as e:
            print(f"Error closing crane control: {e}")
        
        try:
            if self.gamepad:
                self.gamepad.quit()
        except Exception as e:
            print(f"Error quitting gamepad: {e}")
        
        try:
            if self.pygame_initialized:
                pygame.quit()
        except Exception as e:
            print(f"Error quitting pygame: {e}")

# Test the gamepad controller
if __name__ == '__main__':
    print('Gamepad Controller Test Starting...')
    controller = GamepadController()
    
    try:
        controller.start()
        print("Press gamepad buttons or use analog sticks to control tank")
        print("Press Ctrl+C to exit")
        
        while True:
            status = controller.get_status()
            if any(status['button_states'].values()) or any(abs(v) > 0.1 for v in status['axis_states'].values()):
                print(f"Status: {status}")
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("Test interrupted")
    finally:
        controller.close()
        print("Test completed")