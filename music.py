import bluetooth
import time
import difflib
import sys
import os
import subprocess
import dbus

device_name = "LAMAX Beat SE-1"  # The friendly name of your Bluetooth device
mp3_path = "/home/admin/W/pi/demo.mp3"  # Path to the MP3 file you want to play

def setup_bluetooth_audio():
    try:
        # Make sure Bluetooth audio services are running
        os.system('pulseaudio -k')
        time.sleep(1)
        os.system('pulseaudio --start')
        time.sleep(2)
        os.system('bluetoothctl -- power on')
        print("Bluetooth audio services initialized")
    except Exception as e:
        print(f"Error setting up Bluetooth audio: {e}")

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

def connect_bluetooth_audio(address):
    try:
        print("Attempting to connect Bluetooth audio...")
        
        # Connect using bluetoothctl
        commands = [
            f'connect {address}',
            'trust {address}',
            f'pair {address}',
            'info {address}'
        ]
        
        for cmd in commands:
            result = subprocess.run(['bluetoothctl', cmd.format(address=address)], 
                                 capture_output=True, text=True)
            print(f"Executing: {cmd}")
            print(result.stdout)
            time.sleep(2)
        
        # Wait for audio profile to be set up
        time.sleep(3)
        
        # Check if device is connected
        result = subprocess.run(['bluetoothctl', 'info', address], 
                              capture_output=True, text=True)
        
        if "Connected: yes" in result.stdout:
            print("Successfully connected to Bluetooth audio device!")
            return True
        else:
            print("Failed to connect to Bluetooth audio device")
            return False
            
    except Exception as e:
        print(f"Error connecting Bluetooth audio: {e}")
        return False

def play_audio():
    try:
        print(f"Playing: {mp3_path}")
        # Use VLC to stream audio through Bluetooth
        cmd = ['cvlc', '--play-and-exit', mp3_path]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for playback to complete
        process.wait()
        
    except Exception as e:
        print(f"Error playing audio: {e}")
        print("\nTroubleshooting steps:")
        print("1. Install required packages:")
        print("   sudo apt-get install -y pulseaudio pulseaudio-module-bluetooth vlc")
        print("2. Make sure Bluetooth is powered on:")
        print("   bluetoothctl -- power on")
        print("3. Check Bluetooth audio status:")
        print("   pactl list sinks")

def main():
    # Setup Bluetooth audio
    setup_bluetooth_audio()
    
    # Find and connect to the Bluetooth device
    device = find_bluetooth_devices()
    if not device:
        sys.exit(1)
        
    address, name = device
    print(f"\nAttempting to connect to {name} ({address})")
    
    # Make sure the device is in pairing mode
    input("Please put your Bluetooth device in pairing mode and press Enter to continue...")
    
    if not connect_bluetooth_audio(address):
        sys.exit(1)
    
    try:
        # Play the audio file
        play_audio()
    finally:
        # Clean up
        print("Playback completed")

if __name__ == "__main__":
    main()
