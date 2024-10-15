#!/usr/bin/python3

import dbus
import pigpio

from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"

# Initialize pigpio library
pi = pigpio.pi()

# Check if pigpio daemon is running
if not pi.connected:
    exit()

# Define the GPIO pin connected to the signal wire of the servo
servo_pin = 18

# Set the mode for the servo pin
pi.set_mode(servo_pin, pigpio.OUTPUT)

class TennisBallMachineAdvertisement(Advertisement):
    def __init__(self, index):
        super().__init__(index, "peripheral")
        self.add_local_name("TennisBallMachine")
        self.include_tx_power = True

class TennisBallMachineService(Service):
    TENNIS_MACHINE_SVC_UUID = "00000010-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, index):
        super().__init__(index, self.TENNIS_MACHINE_SVC_UUID, True)
        self.add_characteristic(SpeedCharacteristic(self))

class SpeedCharacteristic(Characteristic):
    SPEED_CHARACTERISTIC_UUID = "00000011-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service):
        super().__init__(
                self.SPEED_CHARACTERISTIC_UUID,
                ["write"], service)
        self.speed = 0

    def WriteValue(self, value, options):
        # Convert the list of bytes to an integer speed value
        speed_str = ''.join([chr(byte) for byte in value])
        try:
            speed = int(speed_str)
            self.set_servo_speed(speed)
            self.speed = speed
            print(f"Speed set to {speed}")
        except ValueError:
            print("Invalid speed value received")

    def set_servo_speed(self, speed):
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

app = Application()
app.add_service(TennisBallMachineService(0))
app.register()

adv = TennisBallMachineAdvertisement(0)
adv.register()

try:
    app.run()
except KeyboardInterrupt:
    pass
finally:
    # Turn off the servo
    pi.set_servo_pulsewidth(servo_pin, 0)
    pi.stop()
