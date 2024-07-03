import time
import pigpio

# Initialize pigpio library
pi = pigpio.pi()

# Check if pigpio daemon is running
if not pi.connected:
    exit()

# Define the GPIO pin connected to the signal wire of the servo
servo_pin = 18

# Set the frequency and initial pulse width
pi.set_mode(servo_pin, pigpio.OUTPUT)

# Function to set servo angle
def set_servo_angle(angle):
    # Convert angle to pulse width
    pulse_width = 500 + (angle * 2000 / 180)
    pi.set_servo_pulsewidth(servo_pin, pulse_width)

try:
    while True:
        # Example: Sweep the servo from 0 to 180 degrees
        for angle in range(0, 181, 1):
            set_servo_angle(angle)
            time.sleep(0.02)  # Small delay to allow servo to move

        for angle in range(180, -1, -1):
            set_servo_angle(angle)
            time.sleep(0.02)

except KeyboardInterrupt:
    # Turn off the servo
    pi.set_servo_pulsewidth(servo_pin, 0)
    pi.stop()
