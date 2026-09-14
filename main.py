import logging
import os
import queue
import signal
import sys
from pathlib import Path

from hardware import is_dev_mode, make_player, make_reader
from store import Store
from web import create_app, start_web

BASE_DIR = Path(__file__).resolve().parent
MUSIC_DIR = BASE_DIR / "music"
DATA_DIR = BASE_DIR / "data"
HOST = os.environ.get("PI_HOST", "0.0.0.0")
PORT = int(os.environ.get("PI_PORT", "8080"))
MAX_MISSING_READINGS = 3

log = logging.getLogger("player")


class PlayerLoop:
    def __init__(self, reader, player, store, commands):
        self.reader = reader
        self.player = player
        self.store = store
        self.commands = commands
        self.current = None      # uid of the card on the reader
        self.playing = None      # uid whose file is playing
        self.source = None       # "card" or "dashboard"
        self.missing = 0
        self.running = True

    def _path(self, uid):
        return MUSIC_DIR / f"{uid}.mp3"

    def _publish(self):
        self.store.set_status(now_playing=self.playing, card_present=self.current, source=self.source)

    def _play(self, uid, source):
        path = self._path(uid)
        if not path.is_file():
            return "no_file"
        if not self.player.play(path):
            return "no_speaker"
        self.playing = uid
        self.source = source
        return "played"

    def _stop_playback(self):
        if self.playing:
            self.player.stop()
            self.store.note_stop(self.playing)
            log.info("Stopped %s", self.playing)
        self.playing = None
        self.source = None

    def _card_placed(self, uid):
        self._stop_playback()
        self.current = uid
        action = self._play(uid, "card")
        self.store.note_tap(uid, action)
        log.info("Tap %s: %s", uid, action)
        self._publish()

    def _card_removed(self):
        log.info("Card removed: %s", self.current)
        self.current = None
        self.missing = 0
        if self.source == "card":
            self._stop_playback()
        self._publish()

    def _handle_command(self, cmd, uid):
        if cmd == "reload":
            # Restart the playing card, or start a present card that had no file
            if uid == self.playing or (uid == self.current and self.playing is None):
                action = self._play(uid, "card")
                log.info("Reloading %s after upload: %s", uid, action)
        elif cmd == "play":
            self._stop_playback()
            action = self._play(uid, "dashboard")
            log.info("Dashboard play %s: %s", uid, action)
        elif cmd == "stop":
            if uid is None or uid == self.playing:
                self._stop_playback()
        self._publish()

    def _drain_commands(self):
        while True:
            try:
                cmd, uid = self.commands.get_nowait()
            except queue.Empty:
                return
            try:
                self._handle_command(cmd, uid)
            except Exception:
                log.exception("Command %s failed", cmd)

    def run(self):
        log.info("Player loop started")
        while self.running:
            self._drain_commands()
            uid = self.reader.read()
            if uid:
                self.missing = 0
                if uid != self.current:
                    self._card_placed(uid)
            elif self.current:
                self.missing += 1
                if self.missing >= MAX_MISSING_READINGS:
                    self._card_removed()

    def stop(self):
        self.running = False


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )
    dev = is_dev_mode()
    log.info("Starting RFID music box in %s mode", "dev" if dev else "pi")
    MUSIC_DIR.mkdir(exist_ok=True)

    store = Store(DATA_DIR)
    commands = queue.Queue()
    reader = make_reader(dev)
    player = make_player(dev)
    loop = PlayerLoop(reader, player, store, commands)

    app = create_app(store, commands, reader, MUSIC_DIR, dev)
    _, server = start_web(app, HOST, PORT)

    def on_signal(signum, frame):
        log.info("Signal %s received, shutting down", signum)
        loop.stop()

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)

    try:
        loop.run()
    finally:
        loop._stop_playback()
        player.close()
        reader.close()
        server.shutdown()
        log.info("Bye")


if __name__ == "__main__":
    main()
