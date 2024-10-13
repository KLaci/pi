import time
import sys
from bluepy import btle


# Global variable to store current speed
speed = 0
speed_increment = 10  # Set speed step increment

# Function to set servo speed
def set_servo_speed(speed):
    # Limit the speed to avoid stalling at low values
    min_speed_limit = -400  # Prevent motor from stalling
    max_speed_limit = 400   # Max speed limit (avoid overdrive)
    
    if speed < min_speed_limit:
        speed = min_speed_limit
    elif speed > max_speed_limit:
        speed = max_speed_limit

    # Convert speed to pulse width, where 1500 is stopped
    pulse_width = 1500 + speed
    print(pulse_width)

class SpeedControlService(btle.Peripheral):
    def __init__(self):
        btle.Peripheral.__init__(self)
        self.speed_char.addDescriptor(btle.UUID("2901"), "Speed")

    def increase_speed(self):
        global speed
        speed += speed_increment
        set_servo_speed(speed)
        self.speed_char.write(str(speed).encode())

    def decrease_speed(self):
        global speed
        speed -= speed_increment
        set_servo_speed(speed)
        self.speed_char.write(str(speed).encode())

if __name__ == '__main__':
    try:
        speed_control = SpeedControlService()
        speed_control.advertise("Speed Control")
        print("BLE peripheral started. Waiting for connections...")
        while True:
            if speed_control.waitForConnection(timeout=1.0):
                print("Connected. Use the client to control the speed.")
                speed_control.waitForDisconnection()
    except KeyboardInterrupt:
        pass
        # Turn off the servo
