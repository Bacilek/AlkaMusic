"""Everything that talks to yt-dlp / ffmpeg: setup, search, download and the job queue."""

import ctypes
import json
import logging
import os
import queue
import re
import shutil
import subprocess
import threading
import time
import urllib.parse
import urllib.request
import uuid
import zipfile
from logging.handlers import RotatingFileHandler
from pathlib import Path

from mutagen.id3 import ID3, TALB, TIT2, TPE1, ID3NoHeaderError

from . import naming, ranker
from .history import History

APP_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AlkaMusic"
BIN_DIR = APP_DIR / "bin"
TMP_DIR = APP_DIR / "tmp"
YTDLP = BIN_DIR / "yt-dlp.exe"
YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

APP_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    handlers=[RotatingFileHandler(APP_DIR / "log.txt", maxBytes=1_000_000, backupCount=1, encoding="utf-8")],
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("alkamusic")

WORKERS = 2
META = "@@ALKA@@"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# Crops the video thumbnail to a square, so it looks like an album cover in the phone's player.
SQUARE_COVER = (
    "ThumbnailsConvertor+ffmpeg_o:-c:v mjpeg -qmin 1 -qscale:v 1 "
    "-vf crop=\"'if(gt(ih,iw),iw,ih)':'if(gt(iw,ih),ih,iw)'\""
)


OUT_FOLDER = "Pisnicky"


def desktop_dir():
    """The user's desktop (respects a moved/OneDrive desktop)."""
    try:
        guid = (ctypes.c_byte * 16).from_buffer_copy(
            uuid.UUID("{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}").bytes_le  # FOLDERID_Desktop
        )
        buf = ctypes.c_wchar_p()
        ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(buf))
        base = Path(buf.value)
        ctypes.windll.ole32.CoTaskMemFree(buf)
    except (AttributeError, OSError, TypeError):
        base = Path.home() / "Desktop"
    return base


def songs_dir():
    return desktop_dir() / OUT_FOLDER


def parse_input(text):
    """Splits user input by ';' or new lines, drops empty items and duplicates."""
    seen, items = set(), []
    for part in re.split(r"[;\n\r]+", text):
        part = part.strip(" \t,")
        key = ranker.normalize(part)
        if key and key not in seen:
            seen.add(key)
            items.append(part)
    return items


def _fetch(url, target, on_progress=None):
    tmp = target.with_suffix(".part")
    with urllib.request.urlopen(url, timeout=60) as r, open(tmp, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while chunk := r.read(1 << 16):
            f.write(chunk)
            done += len(chunk)
            if on_progress and total:
                on_progress(done / total)
    tmp.replace(target)


def _run(args, timeout=120):
    return subprocess.run(
        [str(YTDLP), *args], capture_output=True, timeout=timeout, creationflags=NO_WINDOW
    )


class Job:
    WAITING, SEARCHING, DOWNLOADING, DONE, FAILED = "waiting", "searching", "downloading", "done", "failed"

    def __init__(self, query):
        self.query = query
        self.name = query
        self.state = Job.WAITING
        self.progress = 0.0
        self.note = ""
        self.uncertain = False


class Engine:
    def __init__(self):
        self.out_dir = songs_dir()
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_dir = BIN_DIR
        self.history = History(APP_DIR / "history.json")
        self.status = ""  # human readable setup status for the UI
        self.ready = threading.Event()
        self.setup_failed = False
        self._queue = queue.Queue()
        self._active = set()
        self._active_lock = threading.Lock()
        for _ in range(WORKERS):
            threading.Thread(target=self._worker, daemon=True).start()

    # ---------- setup ----------

    def start_setup(self):
        self.setup_failed = False
        threading.Thread(target=self._setup, daemon=True).start()

    def _setup(self):
        try:
            BIN_DIR.mkdir(parents=True, exist_ok=True)
            if YTDLP.exists():
                self.status = "Kontroluji aktualizace…"
                try:
                    _run(["-U"], timeout=90)
                except (OSError, subprocess.TimeoutExpired):
                    pass  # offline or blocked - the current version will do
            else:
                self.status = "Připravuji se (jen poprvé)…"
                _fetch(YTDLP_URL, YTDLP)
            self._ensure_ffmpeg()
            self.status = ""
            self.ready.set()
        except Exception:
            log.exception("Setup failed")
            self.status = "Nejde se připojit k internetu. Zkontroluj připojení a klikni na Stáhnout."
            self.setup_failed = True

    def _ensure_ffmpeg(self):
        if (BIN_DIR / "ffmpeg.exe").exists() and (BIN_DIR / "ffprobe.exe").exists():
            return
        system = shutil.which("ffmpeg")
        if system and shutil.which("ffprobe"):
            self.ffmpeg_dir = Path(system).parent
            return
        archive = BIN_DIR / "ffmpeg.zip"
        _fetch(FFMPEG_URL, archive, lambda p: setattr(self, "status", f"Připravuji se (jen poprvé)… {p:.0%}"))
        with zipfile.ZipFile(archive) as z:
            for member in z.namelist():
                if member.endswith(("/ffmpeg.exe", "/ffprobe.exe")):
                    (BIN_DIR / Path(member).name).write_bytes(z.read(member))
        archive.unlink()

    # ---------- jobs ----------

    def add(self, job):
        job.state, job.progress, job.note = Job.WAITING, 0.0, ""
        self._queue.put(job)

    def _worker(self):
        while True:
            job = self._queue.get()
            self.ready.wait()
            for attempt in range(2):  # YouTube sometimes fails randomly - one silent retry
                try:
                    self._process(job)
                    break
                except Exception:
                    log.exception("Job failed (attempt %d): %s", attempt + 1, job.query)
                    if attempt:
                        job.state, job.note = Job.FAILED, "Nepodařilo se stáhnout"
                    else:
                        time.sleep(3)

    def _process(self, job):
        job.state = Job.SEARCHING
        # YouTube Music "songs" handle typos best and only contain studio versions.
        top = ranker.best_song(job.query, self.search_music(job.query))
        if top:
            job.uncertain = False
            artist, title = "", top["title"]
        else:
            top, job.uncertain = ranker.best(job.query, self.search(job.query))
            if not top:
                job.state, job.note = Job.FAILED, "Nenalezeno"
                return
            artist, title = naming.artist_title(top["title"], top.get("channel") or top.get("uploader"))
        job.name = naming.display_name(artist, title)

        with self._active_lock:
            if top["id"] in self._active:
                job.state, job.note = Job.DONE, "už je v seznamu"
                return
            self._active.add(top["id"])
        try:
            if existing := self.history.get(top["id"]):
                job.name = Path(existing).stem
                job.state, job.note = Job.DONE, "už máš"
                return
            job.state = Job.DOWNLOADING
            path = self.download(
                top["id"], artist, title,
                on_progress=lambda p: setattr(job, "progress", p),
                on_name=lambda name: setattr(job, "name", name),
            )
            self.history.add(top["id"], path)
            job.progress, job.state = 1.0, Job.DONE
        finally:
            with self._active_lock:
                self._active.discard(top["id"])

    # ---------- yt-dlp ----------

    def search(self, query):
        return self._search_entries(f"ytsearch6:{query}")

    def search_music(self, query):
        url = f"https://music.youtube.com/search?q={urllib.parse.quote_plus(query)}#songs"
        try:
            return self._search_entries(url, "--playlist-end", "5")
        except (RuntimeError, ValueError):
            return []  # YouTube Music unavailable - the normal search still works

    @staticmethod
    def _search_entries(target, *extra):
        r = _run([target, "--flat-playlist", "-J", "--encoding", "utf-8", *extra])
        if r.returncode != 0:
            raise RuntimeError(r.stderr.decode("utf-8", "replace"))
        entries = json.loads(r.stdout.decode("utf-8")).get("entries") or []
        return [e for e in entries if e.get("id") and e.get("title")]

    def download(self, video_id, artist, title, on_progress, on_name):
        """Downloads one song as MP3. YouTube's own song metadata (artist/track/album)
        wins over the names guessed from the video title."""
        album = ""
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        args = [
            str(YTDLP), f"https://www.youtube.com/watch?v={video_id}",
            "-x", "--audio-format", "mp3", "--audio-quality", "0",
            "--embed-thumbnail", "--convert-thumbnails", "jpg", "--ppa", SQUARE_COVER,
            "--ffmpeg-location", str(self.ffmpeg_dir),
            "--no-playlist", "--newline", "--encoding", "utf-8", "--force-overwrites",
            "--no-simulate", "--print", f"before_dl:{META}%(artist|)s{META}%(track|)s{META}%(album|)s",
            "-o", str(TMP_DIR / "%(id)s.%(ext)s"),
        ]
        proc = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=NO_WINDOW
        )
        tail = []
        for raw in proc.stdout:
            line = raw.decode("utf-8", "replace")
            tail = (tail + [line])[-20:]
            if line.startswith(META):
                meta_artist, meta_track, album = (s.strip() for s in line.split(META)[1:4])
                if meta_track:
                    title = naming.clean_title(meta_track)
                    artist = meta_artist or artist
                    on_name(naming.display_name(artist, title))
            elif m := re.search(r"\[download\]\s+([\d.]+)%", line):
                on_progress(min(float(m.group(1)) / 100, 0.99))
        if proc.wait() != 0:
            raise RuntimeError("".join(tail))

        mp3 = TMP_DIR / f"{video_id}.mp3"
        self._tag(mp3, artist, title, album)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        base = naming.safe_filename(naming.display_name(artist, title))
        target, n = self.out_dir / f"{base}.mp3", 2
        while target.exists():
            target, n = self.out_dir / f"{base} ({n}).mp3", n + 1
        shutil.move(mp3, target)
        return target

    @staticmethod
    def _tag(mp3, artist, title, album):
        try:
            tags = ID3(mp3)
        except ID3NoHeaderError:
            tags = ID3()
        tags.setall("TIT2", [TIT2(encoding=3, text=title)])
        if artist:
            tags.setall("TPE1", [TPE1(encoding=3, text=artist)])
        if album:
            tags.setall("TALB", [TALB(encoding=3, text=album)])
        tags.save(mp3)
