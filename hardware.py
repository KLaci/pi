import logging
import os
import re
import subprocess
import time

log = logging.getLogger("hardware")

READ_TIMEOUT = 0.3


def find_usb_audio_card():
    """Return the ALSA card number of the USB speaker, or None (parses `aplay -l`)."""
    try:
        result = subprocess.run(["aplay", "-l"], capture_output=True, text=True, check=True)
    except FileNotFoundError:
        log.error("aplay not found, install alsa-utils")
        return None
    except Exception as e:
        log.error("Could not list audio devices: %s", e)
        return None
    for line in result.stdout.splitlines():
        if "card" in line.lower() and "usb" in line.lower():
            match = re.search(r"card (\d+):", line)
            if match:
                log.info("Found USB audio device: %s", line.strip())
                return int(match.group(1))
    log.warning("No USB audio device found in aplay -l output")
    return None


class NullPlayer:
    """Logs instead of playing. Used for local development."""

    def play(self, path):
        log.info("[null player] play %s", path)
        return True

    def stop(self):
        log.info("[null player] stop")

    def close(self):
        pass


class PygamePlayer:
    """Plays through the USB speaker via pygame. Initialises lazily so a missing
    speaker at boot does not take the whole process down."""

    def __init__(self, volume=0.6):
        self.volume = volume
        self.ready = False

    def _ensure_init(self):
        if self.ready:
            return True
        card = find_usb_audio_card()
        if card is None:
            return False
        import pygame
        os.environ["SDL_AUDIODRIVER"] = "alsa"
        os.environ["AUDIODEV"] = f"hw:{card},0"
        try:
            pygame.mixer.init()
        except Exception as e:
            log.error("pygame mixer init failed: %s", e)
            return False
        self.pygame = pygame
        self.ready = True
        log.info("Audio ready on hw:%s,0", card)
        return True

    def play(self, path):
        if not self._ensure_init():
            return False
        try:
            music = self.pygame.mixer.music
            music.load(str(path))
            music.set_volume(self.volume)
            music.play(-1)
            return True
        except Exception as e:
            log.error("Error playing %s: %s", path, e)
            return False

    def stop(self):
        if self.ready:
            self.pygame.mixer.music.stop()

    def close(self):
        if self.ready:
            self.pygame.mixer.quit()


class FakeReader:
    """Simulated reader driven by the dashboard: holds a uid until an expiry."""

    def __init__(self):
        self.uid = None
        self.until = 0.0

    def set(self, uid, hold=4.0):
        self.uid = uid
        self.until = time.monotonic() + float(hold)

    def release(self):
        self.uid = None
        self.until = 0.0

    def read(self):
        time.sleep(READ_TIMEOUT)
        if self.uid and time.monotonic() < self.until:
            return self.uid
        return None

    def close(self):
        pass


class Pirc522Reader:
    def __init__(self):
        from pirc522 import RFID
        self.rdr = RFID()

    def read(self):
        self.rdr.wait_for_tag(timeout=READ_TIMEOUT)
        error, _ = self.rdr.request()
        if error:
            return None
        error, uid = self.rdr.anticoll()
        if error:
            return None
        return ",".join(map(str, uid))

    def close(self):
        self.rdr.cleanup()


def is_dev_mode():
    if os.environ.get("PI_DEV") == "1":
        return True
    try:
        import pirc522  # noqa: F401
        return False
    except ImportError:
        return True


def make_reader(dev):
    if dev:
        log.info("Using FakeReader (dev mode)")
        return FakeReader()
    log.info("Using Pirc522Reader")
    return Pirc522Reader()


def make_player(dev):
    if dev:
        log.info("Using NullPlayer (dev mode)")
        return NullPlayer()
    return PygamePlayer()
