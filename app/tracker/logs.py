import os
import re
from datetime import datetime
from pathlib import Path

CHAT_LOG_RE = re.compile(r"^chat(?:[_-].*)?\.log$", re.IGNORECASE)
STABLE_PARTIAL_POLLS = 2


def auto_log_candidates():
    candidates = []
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA")
        roam = os.environ.get("APPDATA")
        if local:
            candidates.extend([
                Path(local) / "Programs" / "PokeMMO" / "logs",
                Path(local) / "Programs" / "PokeMMO" / "log",
                Path(local) / "PokeMMO" / "logs",
                Path(local) / "PokeMMO" / "log",
            ])
        if roam:
            candidates.extend([
                Path(roam) / "PokeMMO" / "logs",
                Path(roam) / "PokeMMO" / "log",
            ])
    candidates.extend([Path.cwd() / "logs", Path.cwd() / "log"])
    return [path for path in candidates if path.exists() and path.is_dir()]


class ChatLiveTailer:
    def __init__(self, folder: Path, engine, on_status=None):
        self.folder = Path(folder)
        self.engine = engine
        self.on_status = on_status or (lambda _status: None)
        self.current_path = None
        self.file = None
        self.position = 0
        # PokeMMO can expose the newest record at EOF before a trailing newline is
        # visible to the reader. Keep that record pending until it is stable across
        # polls; then process it without advancing the committed file position.
        # When the newline arrives later, the same record is consumed without being
        # emitted twice. This preserves normal partial-write safety while avoiding a
        # live payout/victory sitting invisible until another log message is written.
        self._pending_partial = None
        # Explicit historical replay can temporarily pause live parsing so the
        # same TrackerEngine context is never interleaved with two log streams.
        # The file position is retained and normal polling catches up afterwards.
        self.paused = False

    @staticmethod
    def is_chat_log(path: Path):
        return path.is_file() and CHAT_LOG_RE.match(path.name) is not None

    def newest_log(self):
        try:
            files = [path for path in self.folder.iterdir() if self.is_chat_log(path)]
        except OSError:
            return None
        if not files:
            return None
        return max(files, key=lambda path: path.stat().st_mtime)

    def _clear_pending_partial(self):
        self._pending_partial = None

    def _observe_partial(self, offset, text):
        pending = self._pending_partial
        if pending and pending["offset"] == offset and pending["text"] == text:
            pending["stable_polls"] += 1
        else:
            pending = {
                "offset": offset,
                "text": text,
                "stable_polls": 1,
                "processed": False,
            }
            self._pending_partial = pending

        if pending["stable_polls"] >= STABLE_PARTIAL_POLLS and not pending["processed"]:
            self.engine.process_line(text)
            pending["processed"] = True

    def switch_to(self, path: Path):
        self.close()
        self.current_path = path
        self.file = path.open("r", encoding="utf-8", errors="replace")
        self.file.seek(0, os.SEEK_END)
        self.position = self.file.tell()
        self._clear_pending_partial()
        self.on_status(f"● Live — {path.name}")
        # Curated lifecycle entry for the dashboard Detector. This is deliberately
        # filename-only so the user's local path is never exposed in the activity log.
        self.engine.emit(datetime.now(), f"Now watching log: {path.name}", "info")

    def poll(self):
        if self.paused:
            return
        if not self.folder.exists():
            self.on_status("Log folder unavailable")
            return
        path = self.newest_log()
        if not path:
            self.on_status("No chat_*.log file found")
            return
        if path != self.current_path or self.file is None:
            self.switch_to(path)
            return
        try:
            size = path.stat().st_size
        except OSError:
            return
        if size < self.position:
            self.file.seek(0)
            self.position = 0
            self._clear_pending_partial()
        self.file.seek(self.position)
        while True:
            before = self.file.tell()
            line = self.file.readline()
            if not line:
                break
            after = self.file.tell()
            if not line.endswith(("\n", "\r")):
                self._observe_partial(before, line)
                # Do not commit the read position yet. The writer may still append
                # bytes to this logical record. A stable record can be processed for
                # live responsiveness while remaining anchored here until terminated.
                self.file.seek(before)
                break

            pending = self._pending_partial
            already_processed = bool(
                pending
                and pending.get("processed")
                and pending.get("offset") == before
                and line.rstrip("\r\n") == pending.get("text", "").rstrip("\r\n")
            )
            self.position = after
            self._clear_pending_partial()
            if not already_processed:
                self.engine.process_line(line)

    def close(self):
        if self.file:
            try:
                self.file.close()
            except Exception:
                pass
        self.file = None
        self._clear_pending_partial()
