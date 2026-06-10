"""
VisionBoard AI – Performance Utilities
FPS counter, adaptive frame processing, and memory-efficient helpers.
"""
import time
import collections
import cv2
import numpy as np


class FPSCounter:
    """Rolling-average FPS using a fixed-size deque."""

    def __init__(self, window: int = 30):
        self._times: collections.deque[float] = collections.deque(maxlen=window)

    def tick(self) -> float:
        self._times.append(time.time())
        if len(self._times) < 2:
            return 0.0
        return (len(self._times) - 1) / (self._times[-1] - self._times[0])


class FrameThrottler:
    """
    Skips processing-heavy operations when FPS drops below a threshold.
    Hand-tracking is always run; shape detection and OCR can be gated.
    """

    def __init__(self, min_fps: float = 18.0, skip_heavy_below: float = 22.0):
        self._min_fps    = min_fps
        self._skip_below = skip_heavy_below

    def should_run_heavy(self, fps: float) -> bool:
        """Return True when FPS is healthy enough to run heavy ops."""
        return fps >= self._skip_below or fps == 0.0


def resize_for_inference(frame: np.ndarray, max_w: int = 640) -> tuple[np.ndarray, float]:
    """
    Downscale *frame* for faster MediaPipe inference.
    Returns (resized_frame, scale_factor).
    """
    h, w = frame.shape[:2]
    if w <= max_w:
        return frame, 1.0
    scale = max_w / w
    resized = cv2.resize(frame, (max_w, int(h * scale)), interpolation=cv2.INTER_LINEAR)
    return resized, scale
