from bluezero import peripheral
from gpiozero import LED

# GPIO Setup
control_pin = LED(18)  # Replace with your GPIO pin number

# Define read and write functions
def read_state():
    # Return the current state as bytes
    state = 'start' if control_pin.is_active else 'stop'
    return bytes(state, 'utf-8')

def write_state(value):
    action = value.decode('utf-8')
    if action == 'start':
        control_pin.on()
        print('Machine Started')
    elif action == 'stop':
        control_pin.off()
        print('Machine Stopped')
    else:
        print('Invalid Action Received:', action)

# Create the characteristic
control_characteristic = peripheral.Characteristic(
    uuid='12345678-1234-5678-1234-56789abcdef1',
    flags=['read', 'write'],
    read=read_state,
    write=write_state
)

# Create the service
control_service = peripheral.Service(
    uuid='12345678-1234-5678-1234-56789abcdef0',
    primary=True,
    characteristics=[control_characteristic]
)

# Get the adapter address
import subprocess

def get_adapter_address():
    result = subprocess.run(['hciconfig'], stdout=subprocess.PIPE)
    output = result.stdout.decode()
    import re
    match = re.search(r'BD Address: ([0-9A-F:]{17})', output)
    if match:
        return match.group(1)
    else:
        raise Exception('Bluetooth adapter address not found.')

adapter_address = get_adapter_address()

# Create and start the peripheral
device = peripheral.Peripheral(
    adapter_addr=adapter_address,
    local_name='TennisBallMachine',
    services=[control_service]
)

device.run()
