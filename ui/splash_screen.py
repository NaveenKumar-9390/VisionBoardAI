"""
VisionBoard AI – Splash Screen
Displays a branded startup screen for ~2.5 seconds.
"""
import cv2
import numpy as np
import time
from config import CAM_WIDTH, CAM_HEIGHT, APP_NAME, APP_TAGLINE, APP_VERSION, BRAND_PRIMARY

_FONT  = cv2.FONT_HERSHEY_SIMPLEX
_TITLE = cv2.FONT_HERSHEY_DUPLEX
_BG    = (42, 23, 15)         # brand dark navy


def show_splash(window_title: str, duration: float = 2.5):
    """Render branded splash and display for *duration* seconds."""
    frame = np.zeros((CAM_HEIGHT, CAM_WIDTH, 3), dtype=np.uint8)
    frame[:] = _BG

    # Horizontal accent line
    cy = CAM_HEIGHT // 2
    cv2.line(frame, (80, cy - 60), (CAM_WIDTH - 80, cy - 60), BRAND_PRIMARY, 1)
    cv2.line(frame, (80, cy + 80), (CAM_WIDTH - 80, cy + 80), BRAND_PRIMARY, 1)

    # App name
    (tw, th), _ = cv2.getTextSize(APP_NAME, _TITLE, 2.4, 3)
    cv2.putText(frame, APP_NAME,
                ((CAM_WIDTH - tw) // 2, cy),
                _TITLE, 2.4, BRAND_PRIMARY, 3, cv2.LINE_AA)

    # Tagline
    (tw2, _), _ = cv2.getTextSize(APP_TAGLINE, _FONT, 0.75, 1)
    cv2.putText(frame, APP_TAGLINE,
                ((CAM_WIDTH - tw2) // 2, cy + 44),
                _FONT, 0.75, (200, 200, 200), 1, cv2.LINE_AA)

    # Version
    ver_label = f"v{APP_VERSION}  ·  Computer Vision + AI"
    (tw3, _), _ = cv2.getTextSize(ver_label, _FONT, 0.45, 1)
    cv2.putText(frame, ver_label,
                ((CAM_WIDTH - tw3) // 2, cy + 72),
                _FONT, 0.45, (100, 100, 120), 1, cv2.LINE_AA)

    # Controls hint
    hint = "Press ESC/Q to quit  |  Z Undo  |  Y Redo  |  S Save  |  P PDF  |  R Record  |  O OCR"
    (tw4, _), _ = cv2.getTextSize(hint, _FONT, 0.38, 1)
    cv2.putText(frame, hint,
                ((CAM_WIDTH - tw4) // 2, CAM_HEIGHT - 24),
                _FONT, 0.38, (80, 80, 100), 1, cv2.LINE_AA)

    cv2.imshow(window_title, frame)
    deadline = time.time() + duration
    while time.time() < deadline:
        if cv2.waitKey(30) & 0xFF in (27, ord('q')):
            return False   # user quit during splash
    return True
