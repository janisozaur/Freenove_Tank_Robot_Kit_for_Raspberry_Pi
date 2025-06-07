import time
import threading

class TankMotorControl:
    def __init__(self):
        """Initialize tank motor control for Raspberry Pi 3 with PCB v1"""
        try:
            from gpiozero import Motor
            # GPIO pins for tank motors based on Freenove Tank Robot Kit PCB v1
            self.left_motor = Motor(23, 24)   # Left motor: forward=23, backward=24
            self.right_motor = Motor(6, 5)    # Right motor: forward=6, backward=5
            
            self.current_left_speed = 0
            self.current_right_speed = 0
            self.max_speed = 1.0  # Maximum speed (0-1 for gpiozero)
            self.lock = threading.Lock()
            print("Tank motor control initialized successfully")
        except Exception as e:
            print(f"Error initializing motors: {e}")
            self.left_motor = None
            self.right_motor = None

    def duty_range(self, duty1, duty2):
        """Ensure the duty cycle values are within the valid range (-4095 to 4095)"""
        duty1 = max(-4095, min(4095, duty1))
        duty2 = max(-4095, min(4095, duty2))
        return duty1, duty2

    def set_motor_speeds(self, left_duty, right_duty):
        """Set motor speeds with duty cycle values (-4095 to 4095)"""
        if not self.left_motor or not self.right_motor:
            return
            
        with self.lock:
            left_duty, right_duty = self.duty_range(left_duty, right_duty)
            
            # Convert duty cycle to speed percentage (0-1)
            left_speed = abs(left_duty) / 4095.0
            right_speed = abs(right_duty) / 4095.0
            
            try:
                # Control left motor
                if left_duty > 0:
                    self.left_motor.forward(left_speed)
                elif left_duty < 0:
                    self.left_motor.backward(left_speed)
                else:
                    self.left_motor.stop()
                
                # Control right motor
                if right_duty > 0:
                    self.right_motor.forward(right_speed)
                elif right_duty < 0:
                    self.right_motor.backward(right_speed)
                else:
                    self.right_motor.stop()
                    
                self.current_left_speed = left_duty
                self.current_right_speed = right_duty
                
            except Exception as e:
                print(f"Error setting motor speeds: {e}")

    def move_forward(self, speed=2000):
        """Move tank forward"""
        self.set_motor_speeds(speed, speed)

    def move_backward(self, speed=2000):
        """Move tank backward"""
        self.set_motor_speeds(-speed, -speed)

    def turn_left(self, speed=2000):
        """Turn tank left (left motor backward, right motor forward)"""
        self.set_motor_speeds(-speed, speed)

    def turn_right(self, speed=2000):
        """Turn tank right (left motor forward, right motor backward)"""
        self.set_motor_speeds(speed, -speed)

    def stop(self):
        """Stop both motors"""
        self.set_motor_speeds(0, 0)

    def handle_gamepad_input(self, left_stick_y, right_stick_y):
        """Handle gamepad input for tank-style controls
        left_stick_y: -1 to 1 (left track control)
        right_stick_y: -1 to 1 (right track control)
        """
        # Convert stick values to motor duty cycles
        left_duty = int(left_stick_y * 4095)
        right_duty = int(right_stick_y * 4095)
        
        # Invert Y axis (gamepad up = positive, but we want positive = forward)
        left_duty = -left_duty
        right_duty = -right_duty
        
        self.set_motor_speeds(left_duty, right_duty)

    def control_tank(self, command):
        """Control tank with simple commands for compatibility"""
        if command == 'forward':
            self.move_forward()
        elif command == 'backward':
            self.move_backward()
        elif command == 'left':
            self.turn_left()
        elif command == 'right':
            self.turn_right()
        elif command == 'stop':
            self.stop()

    def close(self):
        """Clean up motor resources"""
        try:
            if self.left_motor:
                self.left_motor.close()
            if self.right_motor:
                self.right_motor.close()
            print("Motors closed successfully")
        except Exception as e:
            print(f"Error closing motors: {e}")

# Test the motor control
if __name__ == '__main__':
    print('Tank Motor Control Test Starting...')
    tank = TankMotorControl()
    
    try:
        print("Moving forward...")
        tank.move_forward(2000)
        time.sleep(1)
        
        print("Moving backward...")
        tank.move_backward(2000)
        time.sleep(1)
        
        print("Turning right...")
        tank.turn_right(2000)
        time.sleep(1)
        
        print("Turning left...")
        tank.turn_left(2000)
        time.sleep(1)
        
        print("Stopping...")
        tank.stop()
        
    except KeyboardInterrupt:
        print("Test interrupted")
    finally:
        tank.stop()
        tank.close()
        print("Test completed")