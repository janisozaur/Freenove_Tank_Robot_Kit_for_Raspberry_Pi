"""
Crane and Grabber Control Module for Freenove Tank Robot Kit
Handles the crane lift and grabber servo controls
"""

import time
import threading

class CraneControl:
    def __init__(self):
        """Initialize crane control with servo management"""
        try:
            # Import based on PCB version and Pi capabilities
            self.servo_driver = self._initialize_servo_driver()
            
            # Servo angle limits
            self.crane_min_angle = 90   # Crane down position
            self.crane_max_angle = 150  # Crane up position
            self.grabber_min_angle = 90  # Grabber open position
            self.grabber_max_angle = 150 # Grabber closed position
            
            # Current positions
            self.current_crane_angle = 140   # Start in up position
            self.current_grabber_angle = 90  # Start in open position
            
            # Control lock for thread safety
            self.lock = threading.Lock()
            
            # Set initial positions
            self.set_crane_angle(self.current_crane_angle)
            self.set_grabber_angle(self.current_grabber_angle)
            
            print("Crane control initialized successfully")
            
        except Exception as e:
            print(f"Error initializing crane control: {e}")
            self.servo_driver = None

    def _initialize_servo_driver(self):
        """Initialize the appropriate servo driver based on system capabilities"""
        try:
            # Try to import gpiozero first (most compatible)
            from gpiozero import AngularServo
            
            # PCB v1 GPIO pins for servos
            crane_pin = 7    # GPIO 7 for servo 0 (crane lift)
            grabber_pin = 8  # GPIO 8 for servo 1 (grabber)
            
            # Servo correction values
            correction = 0.0
            max_pw = (2.5 + correction) / 1000
            min_pw = (0.5 - correction) / 1000
            
            # Initialize servos
            crane_servo = AngularServo(
                crane_pin, 
                initial_angle=None,  # Don't set initial angle immediately
                min_angle=0, 
                max_angle=180,
                min_pulse_width=min_pw,
                max_pulse_width=max_pw
            )
            
            grabber_servo = AngularServo(
                grabber_pin,
                initial_angle=None,  # Don't set initial angle immediately
                min_angle=0,
                max_angle=180, 
                min_pulse_width=min_pw,
                max_pulse_width=max_pw
            )
            
            print("Using gpiozero servo driver")
            return {
                'crane': crane_servo,
                'grabber': grabber_servo,
                'type': 'gpiozero'
            }
            
        except ImportError:
            print("gpiozero not available, using fallback")
            return None
        except Exception as e:
            print(f"Error initializing servo driver: {e}")
            return None

    def _ensure_angle_range(self, angle, min_angle, max_angle):
        """Ensure angle is within specified range"""
        return max(min_angle, min(max_angle, angle))

    def set_crane_angle(self, angle):
        """Set crane lift angle (90=down, 150=up)"""
        if not self.servo_driver:
            print("No servo driver available")
            return False
            
        with self.lock:
            try:
                angle = self._ensure_angle_range(angle, self.crane_min_angle, self.crane_max_angle)
                
                if self.servo_driver['type'] == 'gpiozero':
                    self.servo_driver['crane'].angle = angle
                
                self.current_crane_angle = angle
                print(f"Crane angle set to {angle}°")
                return True
                
            except Exception as e:
                print(f"Error setting crane angle: {e}")
                return False

    def set_grabber_angle(self, angle):
        """Set grabber angle (90=open, 150=closed)"""
        if not self.servo_driver:
            print("No servo driver available")
            return False
            
        with self.lock:
            try:
                angle = self._ensure_angle_range(angle, self.grabber_min_angle, self.grabber_max_angle)
                
                if self.servo_driver['type'] == 'gpiozero':
                    self.servo_driver['grabber'].angle = angle
                
                self.current_grabber_angle = angle
                print(f"Grabber angle set to {angle}°")
                return True
                
            except Exception as e:
                print(f"Error setting grabber angle: {e}")
                return False

    def lift_crane(self, speed=1):
        """Lift crane up gradually"""
        if not self.servo_driver:
            return False
            
        target_angle = self.crane_max_angle
        return self._move_crane_gradually(target_angle, speed)

    def lower_crane(self, speed=1):
        """Lower crane down gradually"""
        if not self.servo_driver:
            return False
            
        target_angle = self.crane_min_angle
        return self._move_crane_gradually(target_angle, speed)

    def open_grabber(self, speed=1):
        """Open grabber gradually"""
        if not self.servo_driver:
            return False
            
        target_angle = self.grabber_min_angle
        return self._move_grabber_gradually(target_angle, speed)

    def close_grabber(self, speed=1):
        """Close grabber gradually"""
        if not self.servo_driver:
            return False
            
        target_angle = self.grabber_max_angle
        return self._move_grabber_gradually(target_angle, speed)

    def _move_crane_gradually(self, target_angle, speed):
        """Move crane gradually to target angle"""
        try:
            current = self.current_crane_angle
            step = 2 if target_angle > current else -2
            delay = 0.02 / speed  # Adjust delay based on speed
            
            angles = range(int(current), int(target_angle) + step, step)
            for angle in angles:
                angle = self._ensure_angle_range(angle, self.crane_min_angle, self.crane_max_angle)
                self.set_crane_angle(angle)
                time.sleep(delay)
            
            # Ensure we reach exact target
            self.set_crane_angle(target_angle)
            return True
            
        except Exception as e:
            print(f"Error moving crane gradually: {e}")
            return False

    def _move_grabber_gradually(self, target_angle, speed):
        """Move grabber gradually to target angle"""
        try:
            current = self.current_grabber_angle
            step = 2 if target_angle > current else -2
            delay = 0.02 / speed  # Adjust delay based on speed
            
            angles = range(int(current), int(target_angle) + step, step)
            for angle in angles:
                angle = self._ensure_angle_range(angle, self.grabber_min_angle, self.grabber_max_angle)
                self.set_grabber_angle(angle)
                time.sleep(delay)
            
            # Ensure we reach exact target
            self.set_grabber_angle(target_angle)
            return True
            
        except Exception as e:
            print(f"Error moving grabber gradually: {e}")
            return False

    def stop_crane(self):
        """Stop crane movement"""
        # Servos don't need explicit stopping - they hold position
        pass

    def stop_grabber(self):
        """Stop grabber movement"""
        # Servos don't need explicit stopping - they hold position  
        pass

    def get_status(self):
        """Get current crane and grabber status"""
        return {
            'crane_angle': self.current_crane_angle,
            'grabber_angle': self.current_grabber_angle,
            'crane_position': 'up' if self.current_crane_angle > 120 else 'down',
            'grabber_position': 'closed' if self.current_grabber_angle > 120 else 'open',
            'servo_driver_available': self.servo_driver is not None
        }

    def handle_command(self, command):
        """Handle crane/grabber commands from web interface or gamepad"""
        commands = {
            'crane_up': self.lift_crane,
            'crane_down': self.lower_crane,
            'grabber_open': self.open_grabber,
            'grabber_close': self.close_grabber,
            'crane_stop': self.stop_crane,
            'grabber_stop': self.stop_grabber
        }
        
        if command in commands:
            try:
                result = commands[command]()
                print(f"Executed crane command: {command}")
                return result
            except Exception as e:
                print(f"Error executing crane command {command}: {e}")
                return False
        else:
            print(f"Unknown crane command: {command}")
            return False

    def close(self):
        """Clean up servo resources"""
        try:
            if self.servo_driver and self.servo_driver['type'] == 'gpiozero':
                # Set servos to safe positions before closing
                self.set_crane_angle(140)  # Up position
                self.set_grabber_angle(90)  # Open position
                time.sleep(0.5)
                
                # Close servo objects
                if 'crane' in self.servo_driver:
                    self.servo_driver['crane'].close()
                if 'grabber' in self.servo_driver:
                    self.servo_driver['grabber'].close()
                    
            print("Crane control closed successfully")
        except Exception as e:
            print(f"Error closing crane control: {e}")


# Test the crane control
if __name__ == '__main__':
    print('Crane Control Test Starting...')
    crane = CraneControl()
    
    try:
        print("Testing crane movements...")
        
        print("Lifting crane...")
        crane.lift_crane()
        time.sleep(1)
        
        print("Lowering crane...")
        crane.lower_crane()
        time.sleep(1)
        
        print("Opening grabber...")
        crane.open_grabber()
        time.sleep(1)
        
        print("Closing grabber...")
        crane.close_grabber()
        time.sleep(1)
        
        print("Status:", crane.get_status())
        
    except KeyboardInterrupt:
        print("Test interrupted")
    finally:
        crane.close()
        print("Test completed")
