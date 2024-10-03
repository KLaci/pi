import time
import pigpio
import sys
from flask import Flask, request, jsonify

# Initialize pigpio library
pi = pigpio.pi()

# Check if pigpio daemon is running
if not pi.connected:
    exit()

# Define the GPIO pin connected to the signal wire of the servo
servo_pin = 18

# Set the frequency and initial pulse width
pi.set_mode(servo_pin, pigpio.OUTPUT)

# Initialize Flask app
app = Flask(__name__)

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
    pi.set_servo_pulsewidth(servo_pin, pulse_width)

@app.route('/', methods=['GET'])
def hello_world():
    return "Hello, World!"

@app.route('/adjust_speed', methods=['POST'])
def adjust_speed():
    global speed
    data = request.json
    increase = data.get('increase', False)

    if increase:
        speed += speed_increment
    else:
        speed -= speed_increment

    set_servo_speed(speed)
    return jsonify({"current_speed": speed}), 200

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        pass
    finally:
        # Turn off the servo
        pi.set_servo_pulsewidth(servo_pin, 0)
        pi.stop()
