import bluetooth
import pygame
import time
import difflib
import sys

device_name = "LAMAX Beat SE-1"  # The friendly name of your Bluetooth device
mp3_path = "/home/admin/W/pi/demo.mp3"  # Path to the MP3 file you want to play

def find_bluetooth_devices():
    print("Scanning for Bluetooth devices...")
    nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True)
    
    if not nearby_devices:
        print("No Bluetooth devices found")
        return None
    
    print("\nFound devices:")
    for addr, name in nearby_devices:
        print(f"  {name} ({addr})")
    
    # Find the best match for our device name
    device_names = [name for _, name in nearby_devices]
    closest_match = difflib.get_close_matches(device_name, device_names, n=1, cutoff=0.5)
    
    if not closest_match:
        print(f"\nNo device similar to '{device_name}' found")
        return None
    
    # Get the address for the matched device
    for addr, name in nearby_devices:
        if name == closest_match[0]:
            return (addr, name)
    
    return None

def find_rfcomm_channel(addr):
    print("Searching for available RFCOMM channels...")
    services = bluetooth.find_service(address=addr)
    if not services:
        print("No services found. Using default channel.")
        return None
    
    for svc in services:
        if "RFCOMM" in str(svc):
            return svc["port"]
    return None

def connect_bluetooth(address):
    # First, try to find the correct RFCOMM channel
    channel = find_rfcomm_channel(address)
    if channel is None:
        # Try common channels if service discovery fails
        channels_to_try = [1, 2, 3, 4]
    else:
        channels_to_try = [channel]

    for channel in channels_to_try:
        try:
            print(f"Trying to connect on channel {channel}...")
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            sock.connect((address, channel))
            print(f"Successfully connected to the device on channel {channel}!")
            return sock
        except bluetooth.BluetoothError as e:
            print(f"Failed to connect on channel {channel}: {e}")
            continue
    
    print("Could not connect on any channel")
    return None

def play_audio():
    try:
        # Initialize pygame mixer
        pygame.mixer.init()
        pygame.mixer.music.load(mp3_path)
        
        print(f"Playing: {mp3_path}")
        pygame.mixer.music.play()
        
        # Wait for the music to play
        while pygame.mixer.music.get_busy():
            time.sleep(1)
            
    except Exception as e:
        print(f"Error playing audio: {e}")
    finally:
        pygame.mixer.quit()

def main():
    # Find and connect to the Bluetooth device
    device = find_bluetooth_devices()
    if not device:
        sys.exit(1)
        
    address, name = device
    print(f"\nAttempting to connect to {name} ({address})")
    
    # Make sure the device is in pairing mode
    input("Please put your Bluetooth device in pairing mode and press Enter to continue...")
    
    sock = connect_bluetooth(address)
    if not sock:
        sys.exit(1)
    
    try:
        # Play the audio file
        play_audio()
    finally:
        # Clean up
        sock.close()
        print("Bluetooth connection closed")

if __name__ == "__main__":
    main()
