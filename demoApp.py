#!/usr/bin/env python3

import dbus
import dbus.mainloop.glib
import dbus.service
from gi.repository import GLib
from gpiozero import LED

# GPIO Setup
control_pin = LED(18)  # Replace with your GPIO pin

# Constants
BLUEZ_SERVICE_NAME = 'org.bluez'
GATT_MANAGER_IFACE = 'org.bluez.GattManager1'
ADAPTER_IFACE = 'org.bluez.Adapter1'
SERVICE_IFACE = 'org.bluez.GattService1'
CHAR_IFACE = 'org.bluez.GattCharacteristic1'
MAIN_LOOP = None

def register_app_cb():
    print('GATT application registered')

def register_app_error_cb(error):
    print('Failed to register application: ' + str(error))
    MAIN_LOOP.quit()

class Application(dbus.service.Object):
    PATH_BASE = '/org/bluez/example/service'

    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method('org.freedesktop.DBus.ObjectManager',
                         out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
        return response

class Service(dbus.service.Object):
    def __init__(self, bus, index, uuid, primary):
        self.path = self.get_path(index)
        self.bus = bus
        self.uuid = uuid
        self.primary = primary
        self.characteristics = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
            SERVICE_IFACE: {
                'UUID': self.uuid,
                'Primary': self.primary,
                'Characteristics': dbus.Array(
                    [chrc.get_path() for chrc in self.characteristics],
                    signature='o')
            }
        }

    def get_path(self, index):
        return dbus.ObjectPath('/org/bluez/example/service' + str(index))

    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)

    def get_characteristics(self):
        return self.characteristics

class Characteristic(dbus.service.Object):
    def __init__(self, bus, index, uuid, flags, service):
        self.path = self.get_path(service.get_path(), index)
        self.bus = bus
        self.uuid = uuid
        self.flags = flags
        self.service = service
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self, service_path, index):
        return dbus.ObjectPath(service_path + '/char' + str(index))

    def get_properties(self):
        return {
            CHAR_IFACE: {
                'UUID': self.uuid,
                'Service': self.service.get_path(),
                'Flags': self.flags
            }
        }

    @dbus.service.method(CHAR_IFACE, in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options):
        value = []
        # Return 'start' or 'stop' based on the GPIO state
        state = 'start' if control_pin.is_active else 'stop'
        for c in state:
            value.append(dbus.Byte(ord(c)))
        return value

    @dbus.service.method(CHAR_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        action = ''.join([chr(b) for b in value])
        if action == 'start':
            control_pin.on()
            print('Machine Started')
        elif action == 'stop':
            control_pin.off()
            print('Machine Stopped')
        else:
            print('Invalid Action')

class ControlService(Service):
    CONTROL_SVC_UUID = '12345678-1234-5678-1234-56789abcdef0'

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.CONTROL_SVC_UUID, True)
        self.add_characteristic(ControlCharacteristic(bus, 0, self))

class ControlCharacteristic(Characteristic):
    CONTROL_CHAR_UUID = '12345678-1234-5678-1234-56789abcdef1'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index, self.CONTROL_CHAR_UUID,
            ['read', 'write'], service)

def main():
    global MAIN_LOOP

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()
    adapter = find_adapter(bus)

    if not adapter:
        print('BLE adapter not found')
        return

    adapter_props = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter), 'org.freedesktop.DBus.Properties')
    adapter_props.Set(ADAPTER_IFACE, 'Powered', dbus.Boolean(1))

    service_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter), GATT_MANAGER_IFACE)

    app = Application(bus)
    app.add_service(ControlService(bus, 0))

    MAIN_LOOP = GLib.MainLoop()

    service_manager.RegisterApplication(app.get_path(), {},
                                        reply_handler=register_app_cb,
                                        error_handler=register_app_error_cb)

    print('GATT server running...')
    MAIN_LOOP.run()

def find_adapter(bus):
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'),
                               'org.freedesktop.DBus.ObjectManager')
    objects = remote_om.GetManagedObjects()
    for obj, props in objects.items():
        if ADAPTER_IFACE in props:
            return obj
    return None

if __name__ == '__main__':
    main()
