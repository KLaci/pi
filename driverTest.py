import pigpio
import time

# Define GPIO pin connected to the signal input of the ESC
ESC_PIN = 18  # Adjust as needed

# Initialize pigpio
pi = pigpio.pi()

if not pi.connected:
    exit()

# Make sure the GPIO pin is set to output
pi.set_mode(ESC_PIN, pigpio.OUTPUT)

# Function to arm the ESC
def arm_esc():
    print("Arming ESC...")
    pi.set_servo_pulsewidth(ESC_PIN, 1000)  # Minimum throttle
    time.sleep(1)
    pi.set_servo_pulsewidth(ESC_PIN, 2000)  # Maximum throttle
    time.sleep(1)
    pi.set_servo_pulsewidth(ESC_PIN, 1000)  # Back to minimum
    time.sleep(1)
    print("ESC Armed and ready.")

# Arm the ESC before sending throttle signals
arm_esc()

# Control the ESC by varying the pulse width
try:
    while True:
        # Ramp up the throttle from minimum to maximum
        for pulsewidth in range(1000, 2001, 50):
            pi.set_servo_pulsewidth(ESC_PIN, pulsewidth)
            time.sleep(0.1)
        # Ramp down the throttle from maximum to minimum
        for pulsewidth in range(2000, 999, -50):
            pi.set_servo_pulsewidth(ESC_PIN, pulsewidth)
            time.sleep(0.1)
except KeyboardInterrupt:
    pass
finally:
    # Stop the ESC
    pi.set_servo_pulsewidth(ESC_PIN, 0)
    pi.stop()
