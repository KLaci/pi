import json
import os
import re
import threading
from datetime import datetime
from pathlib import Path

UID_RE = re.compile(r"^\d{1,3}(,\d{1,3}){3,9}$")
MAX_EVENTS = 200


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def atomic_write_json(path: Path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def load_json(path: Path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


class Store:
    """Seen cards, recent events and live status. All methods are thread safe."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cards_path = self.data_dir / "cards.json"
        self.events_path = self.data_dir / "events.json"
        self.lock = threading.Lock()
        self.cards = load_json(self.cards_path, {})
        self.events = load_json(self.events_path, [])
        self.status = {"now_playing": None, "card_present": None, "source": None}

    def _save_cards(self):
        atomic_write_json(self.cards_path, self.cards)

    def _append_event(self, event):
        self.events.append(event)
        del self.events[:-MAX_EVENTS]
        atomic_write_json(self.events_path, self.events)

    def _card(self, uid):
        return self.cards.setdefault(uid, {
            "name": "",
            "first_seen": now_iso(),
            "last_seen": None,
            "taps": 0,
            "original_filename": None,
            "uploaded_at": None,
        })

    def note_tap(self, uid, action):
        with self.lock:
            card = self._card(uid)
            card["last_seen"] = now_iso()
            card["taps"] += 1
            self._save_cards()
            self._append_event({"ts": now_iso(), "type": "tap", "uid": uid, "action": action})

    def note_stop(self, uid):
        with self.lock:
            self._append_event({"ts": now_iso(), "type": "stop", "uid": uid})

    def note_event(self, type_, uid, **extra):
        with self.lock:
            self._append_event({"ts": now_iso(), "type": type_, "uid": uid, **extra})

    def note_upload(self, uid, original_filename):
        with self.lock:
            card = self._card(uid)
            card["original_filename"] = original_filename
            card["uploaded_at"] = now_iso()
            self._save_cards()
            self._append_event({"ts": now_iso(), "type": "upload", "uid": uid, "filename": original_filename})

    def note_remove(self, uid):
        with self.lock:
            card = self._card(uid)
            card["original_filename"] = None
            card["uploaded_at"] = None
            self._save_cards()
            self._append_event({"ts": now_iso(), "type": "remove", "uid": uid})

    def set_name(self, uid, name):
        with self.lock:
            self._card(uid)["name"] = name
            self._save_cards()
            self._append_event({"ts": now_iso(), "type": "rename", "uid": uid, "name": name})

    def set_status(self, now_playing=None, card_present=None, source=None):
        with self.lock:
            self.status = {"now_playing": now_playing, "card_present": card_present, "source": source}

    def has_card(self, uid):
        with self.lock:
            return uid in self.cards

    def snapshot(self, music_dir: Path):
        with self.lock:
            cards = []
            for uid, card in self.cards.items():
                entry = {"uid": uid, **card, "assigned": False, "file_size": None, "file_mtime": None}
                path = Path(music_dir) / f"{uid}.mp3"
                if path.is_file():
                    st = path.stat()
                    entry["assigned"] = True
                    entry["file_size"] = st.st_size
                    entry["file_mtime"] = datetime.fromtimestamp(st.st_mtime).astimezone().isoformat(timespec="seconds")
                cards.append(entry)
            cards.sort(key=lambda c: c["last_seen"] or "", reverse=True)
            return {
                "now": dict(self.status),
                "cards": cards,
                "events": list(reversed(self.events)),
            }
