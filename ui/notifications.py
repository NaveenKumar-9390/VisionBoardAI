"""
VisionBoard AI – Notification System
Displays stacked, fading status notifications on the canvas.
"""
import time
import cv2
import numpy as np
from config import CAM_WIDTH, TOOLBAR_H, BRAND_PRIMARY, BRAND_SUCCESS, BRAND_WARNING

_FONT     = cv2.FONT_HERSHEY_SIMPLEX
_DURATION = 2.2    # seconds a notification is fully visible before fade
_FADE     = 0.6    # fade-out duration in seconds
_MAX      = 4      # max simultaneous notifications


class NotificationLevel:
    INFO    = BRAND_PRIMARY    # cyan
    SUCCESS = BRAND_SUCCESS    # green
    WARNING = BRAND_WARNING    # amber


class Notification:
    __slots__ = ("text", "color", "created")

    def __init__(self, text: str, color: tuple):
        self.text    = text
        self.color   = color
        self.created = time.time()

    @property
    def alpha(self) -> float:
        age = time.time() - self.created
        if age < _DURATION:
            return 1.0
        fade_progress = (age - _DURATION) / _FADE
        return max(0.0, 1.0 - fade_progress)

    @property
    def expired(self) -> bool:
        return time.time() - self.created > _DURATION + _FADE


class NotificationManager:

    def __init__(self):
        self._queue: list[Notification] = []

    def push(self, text: str, level: tuple = NotificationLevel.INFO):
        self._queue = [n for n in self._queue if not n.expired]
        if len(self._queue) >= _MAX:
            self._queue.pop(0)
        self._queue.append(Notification(text, level))

    def draw(self, frame: np.ndarray):
        self._queue = [n for n in self._queue if not n.expired]
        y_base = TOOLBAR_H + 36
        for i, notif in enumerate(reversed(self._queue)):
            alpha = notif.alpha
            if alpha <= 0:
                continue
            y = y_base + i * 34
            label = notif.text
            (tw, th), _ = cv2.getTextSize(label, _FONT, 0.58, 1)
            x = CAM_WIDTH // 2 - tw // 2

            # Semi-transparent pill background
            overlay = frame.copy()
            cv2.rectangle(overlay, (x - 10, y - th - 6), (x + tw + 10, y + 8),
                          (20, 20, 30), cv2.FILLED)
            cv2.addWeighted(overlay, alpha * 0.75, frame, 1 - alpha * 0.75, 0, frame)

            # Text — apply alpha by blending toward background
            color = tuple(int(c * alpha) for c in notif.color)
            cv2.putText(frame, label, (x, y), _FONT, 0.58, color, 1, cv2.LINE_AA)
