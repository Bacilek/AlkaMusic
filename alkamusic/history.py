"""Remembers which songs were already downloaded, so nothing is downloaded twice."""

import json
import threading
from pathlib import Path


class History:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        try:
            self._data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self._data = {}

    def get(self, video_id):
        """Returns the saved file path if the song was downloaded and still exists."""
        with self._lock:
            file = self._data.get(video_id)
        return file if file and Path(file).exists() else None

    def add(self, video_id, file):
        with self._lock:
            self._data[video_id] = str(file)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=1), encoding="utf-8")
