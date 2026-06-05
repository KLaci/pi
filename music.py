import os
import re
import time
import logging
import subprocess
import sys

import pygame

# Audio file path
mp3_path = "/home/admin/W/pi/demo.mp3"

# Logging setup: timestamped output to stdout so you can spot misconfiguration
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("music")


def find_usb_audio_card():
    """Return the ALSA card number of the USB-connected speaker, or None.

    Parses `aplay -l` looking for a USB audio device.
    """
    log.info("Looking for a USB audio device via 'aplay -l'...")
    try:
        result = subprocess.run(
            ['aplay', '-l'],
            capture_output=True,
            text=True,
            check=True,
        )
        output = result.stdout
    except FileNotFoundError:
        log.error("'aplay' not found. Install ALSA utils: sudo apt install alsa-utils")
        return None
    except subprocess.CalledProcessError as e:
        log.error("'aplay -l' failed (exit %s): %s", e.returncode, e.stderr.strip())
        return None
    except Exception as e:
        log.error("Could not list audio devices: %s", e)
        return None

    log.debug("aplay -l output:\n%s", output.strip())

    # Lines look like: "card 1: Device [USB Audio Device], device 0: ..."
    for line in output.splitlines():
        if 'card' in line.lower() and 'usb' in line.lower():
            match = re.search(r'card (\d+):', line)
            if match:
                card = int(match.group(1))
                log.info("Found USB audio device: %s", line.strip())
                return card

    log.warning("No USB audio device found in 'aplay -l' output.")
    return None


def play_audio():
    try:
        # Initialize pygame mixer (now routed to the USB speaker via ALSA)
        log.info("Initializing pygame mixer...")
        pygame.mixer.init()
        log.debug("Mixer initialized: %s", pygame.mixer.get_init())

        if not os.path.exists(mp3_path):
            log.error("Audio file not found: %s", mp3_path)
            return

        # Load and play the audio file
        log.info("Loading audio file: %s", mp3_path)
        pygame.mixer.music.load(mp3_path)
        pygame.mixer.music.set_volume(0.1)  # Set volume to 10%
        log.debug("Volume set to %.2f", pygame.mixer.music.get_volume())
        pygame.mixer.music.play()
        log.info("Playback started.")

        # Wait for the audio to finish playing
        while pygame.mixer.music.get_busy():
            time.sleep(1)

        log.info("Playback finished.")

    except Exception as e:
        log.exception("Error playing audio: %s", e)
    finally:
        pygame.mixer.quit()
        log.debug("Mixer quit.")


def main():
    log.info("Starting music player (USB speaker mode)")

    # Locate the USB speaker and point SDL/pygame's ALSA backend at it
    card = find_usb_audio_card()
    if card is None:
        log.error("Exiting: no USB speaker detected")
        sys.exit(1)

    # SDL (used by pygame) honours these env vars to pick the ALSA output device
    device = f'hw:{card},0'
    os.environ['SDL_AUDIODRIVER'] = 'alsa'
    os.environ['AUDIODEV'] = device
    log.info("Routing audio: SDL_AUDIODRIVER=alsa AUDIODEV=%s", device)

    log.info("Playing %s on USB speaker (%s)", mp3_path, device)
    play_audio()


if __name__ == "__main__":
    main()
