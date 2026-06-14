"""
Folder watcher using Watchdog.
Emits new/modified/deleted events that the indexing pipeline handles.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Callable, Optional

from app.ocr.processor import SUPPORTED_EXTENSIONS

logger = logging.getLogger(__name__)

EVT_CREATED  = "created"
EVT_MODIFIED = "modified"
EVT_DELETED  = "deleted"

FileEventCallback = Callable[[str, str], None]   # (event_type, file_path)


def _is_image(path: str) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS


def _make_handler(callback: FileEventCallback):
    """
    Build a Watchdog FileSystemEventHandler subclass at call-time
    so the import is fully lazy and class creation only happens once
    watchdog is confirmed available.
    """
    try:
        from watchdog.events import FileSystemEventHandler

        class _Handler(FileSystemEventHandler):
            def on_created(self, event):
                if not event.is_directory and _is_image(event.src_path):
                    callback(EVT_CREATED, event.src_path)

            def on_modified(self, event):
                if not event.is_directory and _is_image(event.src_path):
                    callback(EVT_MODIFIED, event.src_path)

            def on_deleted(self, event):
                if not event.is_directory and _is_image(event.src_path):
                    callback(EVT_DELETED, event.src_path)

            def on_moved(self, event):
                if not event.is_directory:
                    if _is_image(event.src_path):
                        callback(EVT_DELETED, event.src_path)
                    if _is_image(event.dest_path):
                        callback(EVT_CREATED, event.dest_path)

        return _Handler()
    except ImportError:
        return None


class FolderMonitor:
    """
    Manages Watchdog observers for a set of folders.
    Call watch(path) to start monitoring a folder.
    """

    def __init__(self, callback: FileEventCallback) -> None:
        self._callback = callback
        self._observers: dict[str, object] = {}   # path → Observer
        self._lock = threading.Lock()
        self._available: Optional[bool] = None

    @property
    def available(self) -> bool:
        if self._available is None:
            try:
                import watchdog  # type: ignore  # noqa: F401
                self._available = True
            except ImportError:
                logger.warning("watchdog not installed — folder monitoring disabled.")
                self._available = False
        return self._available

    def watch(self, folder: str) -> bool:
        if not self.available:
            return False
        folder = str(Path(folder).resolve())
        with self._lock:
            if folder in self._observers:
                return True
            try:
                from watchdog.observers import Observer

                handler = _make_handler(self._callback)
                if handler is None:
                    return False
                observer = Observer()
                observer.schedule(handler, folder, recursive=True)
                observer.start()
                self._observers[folder] = observer
                logger.info("Watching folder: %s", folder)
                return True
            except Exception as exc:
                logger.error("Failed to watch %s: %s", folder, exc)
                return False

    def unwatch(self, folder: str) -> None:
        folder = str(Path(folder).resolve())
        with self._lock:
            observer = self._observers.pop(folder, None)
            if observer:
                try:
                    observer.stop()
                    observer.join(timeout=3)
                except Exception:
                    pass
                logger.info("Stopped watching: %s", folder)

    def stop_all(self) -> None:
        with self._lock:
            for observer in self._observers.values():
                try:
                    observer.stop()
                    observer.join(timeout=3)
                except Exception:
                    pass
            self._observers.clear()
            logger.info("All folder watchers stopped.")

    @property
    def watched_folders(self) -> list[str]:
        with self._lock:
            return list(self._observers.keys())
