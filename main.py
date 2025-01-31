import pygame
import time
import subprocess
import sys
from pirc522 import RFID

# Bluetooth speaker MAC address
mac_address = "AB:76:6F:5B:A3:D4"

# RFID to music mapping
RFID_MUSIC_MAP = {
    "99,22,142,228,31": "01.mp3",
    # Add more mappings as needed
}

class RFIDMusicPlayer:
    def __init__(self):
        self.rdr = RFID()
        self.currently_playing = False
        self.missing_readings = 0
        self.MAX_MISSING_READINGS = 3
        pygame.mixer.init()
        
    def connect_bluetooth(self):
        try:
            print(f"Attempting to connect to {mac_address}...")
            subprocess.run(['bluetoothctl', 'connect', mac_address], check=True)
            time.sleep(2)
            print("Successfully connected to Bluetooth speaker")
            return True
        except Exception as e:
            print(f"Failed to connect to Bluetooth speaker: {str(e)}")
            return False

    def play_music(self, music_file):
        try:
            if not self.currently_playing:
                full_path = f"/home/admin/W/pi/{music_file}"
                pygame.mixer.music.load(full_path)
                pygame.mixer.music.set_volume(0.1)
                pygame.mixer.music.play(-1)  # -1 means loop indefinitely
                self.currently_playing = True
                print(f"Started playing: {music_file}")
        except Exception as e:
            print(f"Error playing audio: {str(e)}")

    def stop_music(self):
        if self.currently_playing:
            pygame.mixer.music.stop()
            self.currently_playing = False
            print("Stopped playing music")

    def get_tag_uid(self):
        (error, tag_type) = self.rdr.request()
        if not error:
            (error, uid) = self.rdr.anticoll()
            if not error:
                return ','.join(map(str, uid))
        return None

    def cleanup(self):
        self.rdr.cleanup()
        pygame.mixer.quit()

    def run(self):
        print("Starting RFID Music Player...")
        if not self.connect_bluetooth():
            print("Exiting due to Bluetooth connection failure")
            return

        try:
            while True:
                print("waiting for tag")
                # Wait for tag with timeout
                tag_present = self.rdr.wait_for_tag(timeout=2)
                print("tag_present:", tag_present)
                if not tag_present:
                    print("no tag")
                    if self.currently_playing:
                        self.missing_readings += 1
                        print(f"Tag missing: count {self.missing_readings}")
                        
                        if self.missing_readings >= self.MAX_MISSING_READINGS:
                            self.stop_music()
                            self.missing_readings = 0
                    continue
                
                print("tag present")
                uid_str = self.get_tag_uid()
                print("uid_str:", uid_str)
                
                if uid_str and uid_str in RFID_MUSIC_MAP:
                    print(f"Tag detected: {uid_str}")
                    self.missing_readings = 0
                    self.play_music(RFID_MUSIC_MAP[uid_str])
                    print("music playing")
                
                time.sleep(0.3)  # Small delay to prevent CPU overuse

        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.cleanup()

if __name__ == "__main__":
    player = RFIDMusicPlayer()
    player.run() 
