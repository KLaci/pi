# Programmable RFID Music Player — Plan

Turning the working PoC (RFID read → play local MP3) into a programmable toy where
parents can wire YouTube music (or their own files) to different cards.

## The single most important decision: download, don't stream

For an always-on **children's** toy, do **not** stream from YouTube at play time.
Streaming means: needs WiFi every time, buffering delays (kids tap and expect instant
sound), breaks when YouTube changes something, and risks serving ads/garbage.

> **When the parent programs a card, download the audio once via `yt-dlp` into a local
> MP3. Playback is then 100% local, instant, and works offline.**

The current code already plays local `music/{uid}.mp3` files — so this is already set up.
We just add the pipeline that fills that folder.

## Recommended architecture

Keep the Python app, add a small **local web app served from the Pi itself**.
No cloud, no accounts, no hosting bills. Parents connect from their phone on the home WiFi.

```
┌─────────────────────────────────────────────┐
│  Raspberry Pi Zero 2 W                       │
│                                              │
│  Player process (main.py, evolved)           │
│    • reads RC522, looks up UID → folder      │
│    • plays local files                       │
│                                              │
│  Web app (Flask)  ──►  http://musicbox.local │
│    • "Add card" → tap to learn UID           │
│    • paste YouTube URL / search              │
│    • yt-dlp downloads MP3 in background       │
│    • list / rename / re-record / delete cards│
│                                              │
│  Shared state:  cards.json  +  music/<uid>/  │
└─────────────────────────────────────────────┘
```

The two parts communicate through the **filesystem**: a `cards.json` mapping
`UID → {name, folder}`, and a `music/<uid>/` folder per card. The web app writes; the
player reads. No database needed, survives reboots.

## The "magic" UX flow for parents (tap-to-learn)

Parents never type a UID:

1. Open `http://musicbox.local` (bookmarked on their phone)
2. Tap **"Add a new card"**
3. Hold a blank RFID card on the reader → app shows *"Card detected ✓"*
4. Paste a YouTube link (or type a search → pick a result)
5. **Save** → it downloads in the background, mapping the card to that song

Then a card list to rename ("Anna's lullabies"), re-record, or delete. A card can map to a
**folder of several songs** (a playlist) just as easily as one.

To make tap-to-learn work, the player loop should always write the **last-seen UID** to a
small file (or expose it on a tiny HTTP endpoint) so the web app can read "what card is on
the reader right now."

## Concrete tech choices

| Concern        | Recommendation                               | Why                                                            |
|----------------|----------------------------------------------|---------------------------------------------------------------|
| Web framework  | **Flask**                                    | Simplest; already using Python                                |
| Download       | **`yt-dlp`** + `ffmpeg`                       | Current standard; `yt-dlp -x --audio-format mp3`              |
| Search-in-app  | `yt-dlp "ytsearch5:..."`                      | Lets parents search without leaving the app                  |
| Playback       | Keep **pygame** for now, or **mpv**/**MPD** later | mpv/MPD give gapless playback, queues, real volume control |
| Find the Pi    | **Avahi/mDNS** → `musicbox.local`            | Parents never hunt for an IP address                         |
| Run both       | **two systemd services**                     | Player + web app, both autostart, restart on crash           |

MPD is not needed on day one — the pygame setup is fine. Move to MPD/mpv only when
playlists, gapless, and proper volume/skip controls are wanted.

## Build on the PoC vs. adopt an existing project

**Recommendation: keep building our own** — there's a working base, it's a great learning
project, and the "paste a YouTube link → auto-download" flow is actually nicer than what
most existing projects do out of the box. But borrow ideas from:

- **[metachris/rfid-music-player](https://github.com/metachris/rfid-music-player)** —
  closest to the exact goal: Vue web UI to download YouTube songs and map them to tags.
  Worth reading for the design even though it's old/alpha.
- **[ehansis/nfcmusik](https://github.com/ehansis/nfcmusik)** — web interface to assign a
  song to each tag; clean and minimal.
- **[Phoniebox / RPi-Jukebox-RFID](https://github.com/MiczFlor/RPi-Jukebox-RFID)** — the
  mature, full-featured option (web app to assign cards, GPIO buttons, Spotify, web radio).
  The "batteries-included" path if DIY ever loses its appeal — but a big codebase and
  heavier on a Zero 2 W. Good to study its card-registration UX.
  ([phoniebox.de](https://phoniebox.de/index-en.html))

## Things to be aware of

- **Performance:** A Zero 2 W is fine for local MP3 playback + a tiny Flask app. Run the
  *download* as a background job so the web request returns instantly and the player never
  stutters. Pre-downloading (vs. streaming) is what keeps it smooth on this hardware.
- **Legal/ToS:** Downloading from YouTube violates its Terms of Service. For a personal,
  single-home DIY toy this is a common gray area, but worth knowing. Also let parents
  **upload their own MP3s** (audiobooks, music they own) — often the better source for kids.
- **Content safety:** Downloading a *specific* audio file (vs. live streaming) means no ads
  and no surprise "recommended" content — much safer for a child.

## Suggested next steps

1. Add a `cards.json` and refactor the player to look up `UID → folder` instead of the
   hardcoded `music/{uid}.mp3` path.
2. Make the player write the last-seen UID to a file (enables tap-to-learn).
3. Stand up a minimal Flask app with two pages: **card list** and **add card**
   (tap → paste URL → `yt-dlp` download).
4. Add Avahi so it's reachable at `musicbox.local`, and a systemd service for the web app.

## Sources

- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [metachris/rfid-music-player](https://github.com/metachris/rfid-music-player)
- [ehansis/nfcmusik](https://github.com/ehansis/nfcmusik)
- [Phoniebox / RPi-Jukebox-RFID](https://github.com/MiczFlor/RPi-Jukebox-RFID)
- [phoniebox.de](https://phoniebox.de/index-en.html)
