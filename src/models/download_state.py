import threading


class _DownloadState:
    def __init__(self):
        self._lock = threading.Lock()
        self.active = False
        self.label = ""
        self.downloaded = 0
        self.total = 0
        self.completed = 0

    def start(self, label: str):
        with self._lock:
            self.active = True
            self.label = label
            self.downloaded = 0
            self.total = 0

    def update(self, downloaded: int, total: int):
        with self._lock:
            self.downloaded = downloaded
            self.total = total

    def finish(self):
        with self._lock:
            self.active = False
            self.completed += 1

    def snapshot(self) -> dict:
        with self._lock:
            pct = (self.downloaded / self.total * 100) if self.total > 0 else 0
            return {
                "active": self.active,
                "label": self.label,
                "pct": pct,
                "completed": self.completed,
            }


download_state = _DownloadState()