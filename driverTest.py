import RPi.GPIO as GPIO
import time

# Set up GPIO pins
PWM_PIN = 18  # GPIO pin for PWM
DIR_PIN = 23  # GPIO pin for direction control

GPIO.setmode(GPIO.BCM)
GPIO.setup(PWM_PIN, GPIO.OUT)
GPIO.setup(DIR_PIN, GPIO.OUT)

# Set up PWM on the PWM_PIN at 1kHz frequency
pwm = GPIO.PWM(PWM_PIN, 1000)
pwm.start(0)  # Start PWM with 0% duty cycle (motor off)

def set_speed(speed):
    if speed >= 0:
        GPIO.output(DIR_PIN, GPIO.HIGH)  # Forward
    else:
        GPIO.output(DIR_PIN, GPIO.LOW)  # Reverse
        speed = -speed  # Make speed positive

    pwm.ChangeDutyCycle(speed)  # Change motor speed

try:
    while True:
        for speed in range(0, 101, 10):  # Gradually increase speed
            set_speed(speed)
            time.sleep(1)
        for speed in range(100, -1, -10):  # Gradually decrease speed
            set_speed(speed)
            time.sleep(1)
except KeyboardInterrupt:
    pass

pwm.stop()
GPIO.cleanup()
