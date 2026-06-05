import os
import re
import pygame
import time
import subprocess
import sys
from pirc522 import RFID

def find_usb_audio_card():
    """Return the ALSA card number of the USB-connected speaker, or None.

    Parses `aplay -l` looking for a USB audio device.
    """
    try:
        result = subprocess.run(
            ['aplay', '-l'],
            capture_output=True,
            text=True,
            check=True,
        )
        output = result.stdout
    except Exception as e:
        print(f"Could not list audio devices: {str(e)}")
        return None

    # Lines look like: "card 1: Device [USB Audio Device], device 0: ..."
    for line in output.splitlines():
        if 'card' in line.lower() and 'usb' in line.lower():
            match = re.search(r'card (\d+):', line)
            if match:
                card = int(match.group(1))
                print(f"Found USB audio device: {line.strip()}")
                return card

    print("No USB audio device found in 'aplay -l' output.")
    return None

class RFIDMusicPlayer:
    def __init__(self):
        self.rdr = RFID()
        self.currently_playing = False
        self.missing_readings = 0
        self.MAX_MISSING_READINGS = 3

    def connect_speaker(self):
        # Locate the USB speaker and point SDL/pygame's ALSA backend at it
        card = find_usb_audio_card()
        if card is None:
            print("No USB speaker detected")
            return False

        # SDL (used by pygame) honours these env vars to pick the ALSA output device
        device = f'hw:{card},0'
        os.environ['SDL_AUDIODRIVER'] = 'alsa'
        os.environ['AUDIODEV'] = device
        print(f"Routing audio: SDL_AUDIODRIVER=alsa AUDIODEV={device}")

        pygame.mixer.init()
        return True

    def play_music(self, music_file):
        try:
            if not self.currently_playing:
                full_path = f"/home/admin/W/pi/{music_file}"
                pygame.mixer.music.load(full_path)
                pygame.mixer.music.set_volume(0.6)
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
        if not self.connect_speaker():
            print("Exiting due to USB speaker setup failure")
            return

        try:
            while True:
                print("waiting for tag")
                # Wait for tag with timeout
                self.rdr.wait_for_tag(timeout=0.3)
                uid_str = self.get_tag_uid()
                print("uid_str:", uid_str)
                if not uid_str:
                    print("no tag")
                    if self.currently_playing:
                            self.stop_music()
                    continue
                
            
                print(f"Tag detected: {uid_str}")
                self.missing_readings = 0
                self.play_music(f"music/{uid_str}.mp3")
                print("music playing")
                
                time.sleep(0.3)  # Small delay to prevent CPU overuse

        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.cleanup()

if __name__ == "__main__":
    player = RFIDMusicPlayer()
    player.run() 
