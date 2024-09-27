import pigpio
import time

# Define GPIO pin connected to the PWM input of BDC80P
PWM_PIN = 18  # Adjust as needed

# Initialize pigpio
pi = pigpio.pi()

if not pi.connected:
    exit()

# Set the GPIO pin as PWM output
pi.set_mode(PWM_PIN, pigpio.OUTPUT)

# Set PWM frequency
frequency = 1000  # You may need to adjust this depending on the controller's requirements

# Set speed using PWM duty cycle (0-255 for pigpio)
try:
    while True:
        for speed in range(0, 256, 10):  # Ramp up the speed
            pi.set_PWM_dutycycle(PWM_PIN, speed)
            time.sleep(0.1)

        for speed in range(255, -1, -10):  # Ramp down the speed
            pi.set_PWM_dutycycle(PWM_PIN, speed)
            time.sleep(0.1)
except KeyboardInterrupt:
    pass

# Turn off PWM and clean up
pi.set_PWM_dutycycle(PWM_PIN, 0)
pi.stop()
