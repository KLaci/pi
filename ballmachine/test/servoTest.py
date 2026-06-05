import time
import pigpio
import sys
import termios
import tty

# Initialize pigpio library
pi = pigpio.pi()

# Check if pigpio daemon is running
if not pi.connected:
    exit()

# Define the GPIO pin connected to the signal wire of the servo
servo_pin = 18

# Set the frequency and initial pulse width
pi.set_mode(servo_pin, pigpio.OUTPUT)

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
    pi.set_servo_pulsewidth(servo_pin, pulse_width)

# Function to read a single character from standard input
def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

speed = 0
speed_increment = 10  # Set speed step increment

try:
    while True:
        char = getch()
        if char == 'a':
            # Gradually increase speed
            speed += speed_increment
        elif char == 's':
            # Gradually decrease speed
            speed -= speed_increment
        elif char == 'q':
            break

        # Set the speed to the servo motor
        set_servo_speed(speed)
        
        # Short delay to allow the motor to respond smoothly
        time.sleep(0.05)

except KeyboardInterrupt:
    pass

finally:
    # Turn off the servo
    pi.set_servo_pulsewidth(servo_pin, 0)
    pi.stop()
