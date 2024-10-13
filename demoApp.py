from bluepy.btle import Peripheral, UUID, Service, Characteristic, Descriptor
from time import sleep

class ControlService(Service):
    CONTROL_UUID = UUID("12345678-1234-5678-1234-56789abcdef0")

    def __init__(self, periph):
        Service.__init__(self, periph, self.CONTROL_UUID)
        self.addCharacteristic(ControlCharacteristic(self))

class ControlCharacteristic(Characteristic):
    CHAR_UUID = UUID("abcdefab-1234-5678-1234-56789abcdef1")

    def __init__(self, service):
        Characteristic.__init__(self, service, self.CHAR_UUID,
                                props=Characteristic.propWrite | Characteristic.propRead,
                                perms=Characteristic.permRead | Characteristic.permWrite)

    def write(self, value, offset, withResponse):
        action = value.decode('utf-8')
        if action == 'start':
            print("Machine Started")
        elif action == 'stop':
            print("Machine Stopped")
        else:
            print("Invalid Action")

def main():
    # Initialize Peripheral
    periph = Peripheral()
    periph.addService(ControlService(periph))
    periph.publish()
    print("BLE Peripheral Running...")
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        periph.stop()
        print("BLE Peripheral Stopped")

if __name__ == "__main__":
    main()
