"""
VisionBoard AI – Session Recorder
Records the live composite frame stream to MP4.
"""
import cv2
import logging
import os
import time
import numpy as np
from config import RECORDING_DIR, RECORDING_FPS, RECORDING_FOURCC, CAM_WIDTH, CAM_HEIGHT, APP_NAME

log = logging.getLogger(__name__)


class SessionRecorder:

    def __init__(self):
        self._writer:     cv2.VideoWriter | None = None
        self._start_time: float | None           = None
        self._path:       str                    = ""

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def is_recording(self) -> bool:
        return self._writer is not None

    @property
    def elapsed(self) -> float:
        """Seconds since recording started."""
        return time.time() - self._start_time if self._start_time else 0.0

    def start(self) -> str:
        """Start a new recording. Returns file path."""
        if self.is_recording:
            return self._path
        ts         = time.strftime("%Y%m%d_%H%M%S")
        self._path = os.path.join(RECORDING_DIR, f"VisionBoardAI_Session_{ts}.mp4")
        fourcc     = cv2.VideoWriter_fourcc(*RECORDING_FOURCC)
        self._writer     = cv2.VideoWriter(self._path, fourcc, RECORDING_FPS,
                                           (CAM_WIDTH, CAM_HEIGHT))
        self._start_time = time.time()
        log.info("Recording started: %s", self._path)
        return self._path

    def stop(self) -> str:
        """Stop recording and flush to disk. Returns file path."""
        path = self._path
        if self._writer:
            self._writer.release()
            self._writer     = None
            self._start_time = None
            log.info("Recording saved: %s", path)
        return path

    def write(self, frame: np.ndarray):
        """Write a single frame. Call every loop iteration while recording."""
        if self._writer:
            self._writer.write(frame)

    def draw_indicator(self, frame: np.ndarray):
        """Overlay a recording badge (red dot + timer) onto *frame* in-place."""
        if not self.is_recording:
            return
        elapsed = self.elapsed
        mins    = int(elapsed) // 60
        secs    = int(elapsed) % 60
        label   = f"REC  {mins:02d}:{secs:02d}"
        # Pulsing red dot
        radius  = 7 + (int(elapsed * 2) % 2)   # alternates 7/8 for blink effect
        cv2.circle(frame, (CAM_WIDTH - 160, 22), radius, (0, 0, 220), cv2.FILLED)
        cv2.putText(frame, label, (CAM_WIDTH - 148, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 220), 1, cv2.LINE_AA)
