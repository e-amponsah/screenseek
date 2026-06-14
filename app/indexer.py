"""
Indexing pipeline — orchestrates OCR, thumbnail generation, and database writes.
Runs in a background thread pool so the UI stays responsive.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional

from app.database.manager import DatabaseManager, _hash_file
from app.ocr.engine import OCREngine
from app.ocr.processor import SUPPORTED_EXTENSIONS, is_supported_image
from app.thumbnails.generator import ThumbnailGenerator
from app.watcher.monitor import EVT_CREATED, EVT_DELETED, EVT_MODIFIED, FolderMonitor

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int, str], None]   # (current, total, filename)
StatusCallback   = Callable[[str], None]


class IndexingPipeline:
    """
    Single entry-point for all indexing operations.

    Usage:
        pipeline = IndexingPipeline(db, ocr, thumbs)
        pipeline.index_folders(folders, progress_cb)
    """

    WORKER_THREADS = max(1, (os.cpu_count() or 2) - 1)

    def __init__(
        self,
        db: DatabaseManager,
        ocr: OCREngine,
        thumbnails: ThumbnailGenerator,
        monitor: Optional[FolderMonitor] = None,
    ) -> None:
        self._db = db
        self._ocr = ocr
        self._thumbs = thumbnails
        self._monitor = monitor
        self._cancel_event = threading.Event()
        self._running_lock = threading.Lock()
        self._is_running = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def index_folders(
        self,
        folders: list[str],
        progress_cb: Optional[ProgressCallback] = None,
        status_cb: Optional[StatusCallback] = None,
        force_reindex: bool = False,
    ) -> dict:
        """
        Scan all folders, OCR any new/changed images, update DB.
        Returns a summary dict.
        """
        with self._running_lock:
            if self._is_running:
                return {"error": "Indexing already in progress"}
            self._is_running = True
            self._cancel_event.clear()

        summary = {"indexed": 0, "skipped": 0, "failed": 0, "deleted": 0}
        try:
            images = self._collect_images(folders)
            total = len(images)
            _status(status_cb, f"Found {total} images across {len(folders)} folder(s).")

            deleted = self._purge_missing(folders)
            summary["deleted"] = deleted

            with ThreadPoolExecutor(max_workers=self.WORKER_THREADS) as pool:
                futures = {
                    pool.submit(self._process_image, img, force_reindex): img
                    for img in images
                }
                done = 0
                for future in as_completed(futures):
                    if self._cancel_event.is_set():
                        pool.shutdown(wait=False, cancel_futures=True)
                        break
                    img = futures[future]
                    done += 1
                    try:
                        result = future.result()
                        summary[result] = summary.get(result, 0) + 1
                    except Exception as exc:
                        logger.error("Unhandled indexing error for %s: %s", img, exc)
                        summary["failed"] += 1
                    if progress_cb:
                        progress_cb(done, total, Path(img).name)
        finally:
            self._is_running = False

        _status(
            status_cb,
            f"Done — {summary['indexed']} indexed, "
            f"{summary['skipped']} skipped, "
            f"{summary['failed']} failed, "
            f"{summary['deleted']} deleted.",
        )
        return summary

    def index_single(self, file_path: str) -> str:
        """Index a single image. Returns 'indexed' | 'skipped' | 'failed'."""
        return self._process_image(file_path, force_reindex=True)

    def cancel(self) -> None:
        self._cancel_event.set()

    @property
    def is_running(self) -> bool:
        return self._is_running

    # ------------------------------------------------------------------
    # Watcher integration
    # ------------------------------------------------------------------

    def start_monitoring(self, folders: list[str]) -> None:
        if not self._monitor:
            return
        for folder in folders:
            self._monitor.watch(folder)

    def stop_monitoring(self) -> None:
        if self._monitor:
            self._monitor.stop_all()

    def on_file_event(self, event_type: str, file_path: str) -> None:
        """Called by FolderMonitor on file system events."""
        if event_type == EVT_DELETED:
            self._db.delete_screenshot(file_path)
            logger.info("Removed from index: %s", file_path)
        elif event_type in (EVT_CREATED, EVT_MODIFIED):
            threading.Thread(
                target=self._process_image,
                args=(file_path, True),
                daemon=True,
            ).start()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _collect_images(self, folders: list[str]) -> list[str]:
        images = []
        for folder in folders:
            root = Path(folder)
            if not root.exists():
                continue
            for ext in SUPPORTED_EXTENSIONS:
                images.extend(str(p) for p in root.rglob(f"*{ext}"))
                images.extend(str(p) for p in root.rglob(f"*{ext.upper()}"))
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique = []
        for img in images:
            if img not in seen:
                seen.add(img)
                unique.append(img)
        return unique

    def _process_image(self, file_path: str, force_reindex: bool = False) -> str:
        """Returns 'indexed' | 'skipped' | 'failed'."""
        path = Path(file_path)
        if not path.exists() or not is_supported_image(path):
            return "skipped"

        try:
            # Skip if unchanged (same hash)
            if not force_reindex:
                stored_hash = self._db.file_hash_for(file_path)
                if stored_hash and stored_hash == _hash_file(path):
                    return "skipped"

            ocr_result = self._ocr.extract(path)
            thumb_path = self._thumbs.generate(path) or ""

            self._db.upsert_screenshot(
                file_path=file_path,
                ocr_text=ocr_result.text,
                ocr_confidence=ocr_result.confidence,
                language=ocr_result.language,
                engine_used=ocr_result.engine_used,
                thumbnail_path=thumb_path,
            )
            logger.debug("Indexed: %s (%d words)", path.name, ocr_result.word_count)
            return "indexed"
        except Exception as exc:
            logger.error("Failed to index %s: %s", path.name, exc)
            return "failed"

    def _purge_missing(self, folders: list[str]) -> int:
        """Remove DB entries whose files no longer exist on disk."""
        count = 0
        all_records = self._db.get_all_screenshots()
        folder_set = {str(Path(f).resolve()) for f in folders}
        for rec in all_records:
            rec_folder = str(Path(rec.folder).resolve())
            if rec_folder not in folder_set:
                continue
            if not Path(rec.file_path).exists():
                self._db.delete_screenshot(rec.file_path)
                count += 1
        return count


def _status(cb: Optional[StatusCallback], msg: str) -> None:
    logger.info(msg)
    if cb:
        cb(msg)
