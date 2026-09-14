import logging
import os
import tempfile
import threading
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.serving import make_server

from store import UID_RE

log = logging.getLogger("web")

MAX_UPLOAD = 50 * 1024 * 1024
MAX_NAME = 60


def looks_like_mp3(head: bytes):
    # ID3 tag or a raw MPEG audio frame sync
    return head.startswith(b"ID3") or (len(head) >= 2 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0)


def create_app(store, commands, reader, music_dir, dev):
    music_dir = Path(music_dir)
    static_dir = Path(__file__).resolve().parent / "static"
    app = Flask(__name__, static_folder=str(static_dir), static_url_path="")
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    def error(msg, code):
        return jsonify({"error": msg}), code

    def mp3_path(uid):
        return music_dir / f"{uid}.mp3"

    def check_uid(uid):
        if not UID_RE.match(uid):
            return error("Invalid card id", 400)
        if not store.has_card(uid):
            return error("Unknown card, tap it on the reader first", 404)
        return None

    def card_entry(uid):
        return next((c for c in store.snapshot(music_dir)["cards"] if c["uid"] == uid), None)

    @app.get("/")
    def index():
        return send_from_directory(static_dir, "index.html")

    @app.get("/api/state")
    def state():
        return jsonify({"mode": "dev" if dev else "pi", **store.snapshot(music_dir)})

    @app.get("/api/cards/<uid>/file")
    def get_file(uid):
        if not UID_RE.match(uid):
            return error("Invalid card id", 400)
        return send_from_directory(music_dir, f"{uid}.mp3", mimetype="audio/mpeg")

    @app.post("/api/cards/<uid>/file")
    def upload_file(uid):
        err = check_uid(uid)
        if err:
            return err
        f = request.files.get("file")
        if f is None or not f.filename:
            return error("No file uploaded", 400)
        if not f.filename.lower().endswith(".mp3"):
            return error("Only .mp3 files are accepted", 400)
        head = f.stream.read(4)
        f.stream.seek(0)
        if not looks_like_mp3(head):
            return error("File does not look like an mp3", 400)
        tmp = tempfile.NamedTemporaryFile(dir=music_dir, suffix=".part", delete=False)
        try:
            f.save(tmp)
            tmp.close()
            os.chmod(tmp.name, 0o644)  # NamedTemporaryFile defaults to 0600
            os.replace(tmp.name, mp3_path(uid))
        except Exception:
            tmp.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
            raise
        store.note_upload(uid, f.filename)
        commands.put(("reload", uid))
        log.info("Uploaded %s for %s", f.filename, uid)
        return jsonify(card_entry(uid))

    @app.delete("/api/cards/<uid>/file")
    def delete_file(uid):
        err = check_uid(uid)
        if err:
            return err
        path = mp3_path(uid)
        if not path.is_file():
            return error("Card has no file", 404)
        path.unlink()
        store.note_remove(uid)
        commands.put(("stop", uid))
        return jsonify(card_entry(uid))

    @app.post("/api/cards/<uid>/name")
    def set_name(uid):
        err = check_uid(uid)
        if err:
            return err
        name = (request.get_json(silent=True) or {}).get("name", "")
        if not isinstance(name, str):
            return error("Name must be text", 400)
        store.set_name(uid, name.strip()[:MAX_NAME])
        return jsonify(card_entry(uid))

    @app.post("/api/cards/<uid>/play")
    def play(uid):
        err = check_uid(uid)
        if err:
            return err
        if not mp3_path(uid).is_file():
            return error("Card has no file", 409)
        commands.put(("play", uid))
        store.note_event("test_play", uid)
        return jsonify({"ok": True})

    @app.post("/api/stop")
    def stop():
        commands.put(("stop", None))
        return jsonify({"ok": True})

    if dev:
        @app.post("/api/dev/tap")
        def dev_tap():
            body = request.get_json(silent=True) or {}
            uid = str(body.get("uid", "")).strip()
            if not UID_RE.match(uid):
                return error("Invalid card id", 400)
            reader.set(uid, float(body.get("hold", 4)))
            return jsonify({"ok": True})

        @app.post("/api/dev/release")
        def dev_release():
            reader.release()
            return jsonify({"ok": True})

    return app


def start_web(app, host, port):
    server = make_server(host, port, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, name="web", daemon=True)
    thread.start()
    log.info("Dashboard listening on http://%s:%s", host, port)
    return thread, server
