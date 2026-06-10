"""Handles PNG/JPG export, timestamped saves, and auto-save."""
import cv2
import logging
import os
import time
import numpy as np
from config import SAVE_DIR, AUTOSAVE_INTERVAL_SEC

log = logging.getLogger(__name__)


class FileManager:
    def __init__(self):
        self._last_autosave = time.time()

    # ── Public API ────────────────────────────────────────────────────────────

    def save_png(self, canvas: np.ndarray) -> str:
        path = self._timestamped_path("png")
        cv2.imwrite(path, canvas)
        log.info("Saved PNG: %s", path)
        return path

    def save_jpg(self, canvas: np.ndarray) -> str:
        path = self._timestamped_path("jpg")
        cv2.imwrite(path, canvas, [cv2.IMWRITE_JPEG_QUALITY, 95])
        log.info("Saved JPG: %s", path)
        return path

    def save_composite(self, frame: np.ndarray) -> str:
        """Save full camera + drawing composite as screenshot."""
        path = self._timestamped_path("png", prefix="screenshot")
        cv2.imwrite(path, frame)
        log.info("Screenshot: %s", path)
        return path

    def tick_autosave(self, canvas: np.ndarray) -> bool:
        """Call every frame. Returns True if autosave was triggered."""
        if time.time() - self._last_autosave >= AUTOSAVE_INTERVAL_SEC:
            # Only save if canvas has any content
            if canvas.any():
                path = os.path.join(SAVE_DIR, "autosave.png")
                cv2.imwrite(path, canvas)
                log.info("Auto-saved: %s", path)
            self._last_autosave = time.time()
            return True
        return False

    # ── Internal ─────────────────────────────────────────────────────────────

    @staticmethod
    def _timestamped_path(ext: str, prefix: str = "drawing") -> str:
        ts   = time.strftime("%Y%m%d_%H%M%S")
        name = f"{prefix}_{ts}.{ext}"
        return os.path.join(SAVE_DIR, name)
