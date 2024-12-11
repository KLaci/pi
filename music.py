import bluetooth
import pygame
import time
import subprocess
import sys

# Bluetooth speaker MAC address and audio file path
mac_address = "AB:76:6F:5B:A3:D4"
mp3_path = "/home/admin/W/pi/demo.mp3"

def connect_bluetooth():
    try:
        # Try to connect to the Bluetooth speaker
        print(f"Attempting to connect to {mac_address}...")
        
        # Use bluetoothctl to connect (more reliable than pure Python approach)
        subprocess.run(['bluetoothctl', 'connect', mac_address], check=True)
        
        # Wait for connection to establish
        time.sleep(2)
        print("Successfully connected to Bluetooth speaker")
        return True
        
    except Exception as e:
        print(f"Failed to connect to Bluetooth speaker: {str(e)}")
        return False

def play_audio():
    try:
        # Initialize pygame mixer
        pygame.mixer.init()
        
        # Load and play the audio file
        pygame.mixer.music.load(mp3_path)
        pygame.mixer.music.set_volume(0.1)  # Set volume to 30%
        pygame.mixer.music.play()
        
        # Wait for the audio to finish playing
        while pygame.mixer.music.get_busy():
            time.sleep(1)
            
    except Exception as e:
        print(f"Error playing audio: {str(e)}")
    finally:
        pygame.mixer.quit()

def main():
    # First, try to connect to the Bluetooth speaker
    if connect_bluetooth():
        # If connection successful, play the audio
        print(f"Playing: {mp3_path}")
        play_audio()
    else:
        print("Exiting due to connection failure")
        sys.exit(1)

if __name__ == "__main__":
    main()
