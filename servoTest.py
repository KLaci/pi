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
    # Convert speed to pulse width
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

try:
    while True:
        char = getch()
        if char == 'a':
            speed += 10
        elif char == 's':
            speed -= 10
        elif char == 'q':
            break
        set_servo_speed(speed)
        time.sleep(0.02)

except KeyboardInterrupt:
    pass

finally:
    # Turn off the servo
    pi.set_servo_pulsewidth(servo_pin, 0)
    pi.stop()
