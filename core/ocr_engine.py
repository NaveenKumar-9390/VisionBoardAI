"""
VisionBoard AI – OCR Engine
Converts handwritten content on the canvas to digital text using EasyOCR.
"""
import cv2
import logging
import os
import time
import numpy as np
from config import OCR_LANGUAGES, OCR_MIN_CONF, SAVE_DIR

log = logging.getLogger(__name__)

try:
    import easyocr
    _reader = easyocr.Reader(OCR_LANGUAGES, gpu=False, verbose=False)
    _EASYOCR = True
except ImportError:
    _EASYOCR = False
    log.warning("easyocr not installed — OCR disabled. Run: pip install easyocr")


class OCREngine:

    def __init__(self):
        self._last_result: str = ""

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def last_result(self) -> str:
        return self._last_result

    def run(self, canvas_layer: np.ndarray) -> str:
        """
        Run OCR on the current canvas layer.
        Returns recognised text string (may be empty).
        """
        if not _EASYOCR:
            return "[EasyOCR not installed]"

        # Convert to grayscale, invert (white text on black → black on white)
        gray    = cv2.cvtColor(canvas_layer, cv2.COLOR_BGR2GRAY)
        inverted = cv2.bitwise_not(gray)

        results = _reader.readtext(inverted)
        lines   = [text for (_, text, conf) in results if conf >= OCR_MIN_CONF]
        self._last_result = " ".join(lines).strip() if lines else ""

        if self._last_result:
            self._save_text(self._last_result)
            log.info("OCR result: %s", self._last_result)
        else:
            log.info("OCR: no text detected above confidence threshold.")

        return self._last_result

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _save_text(text: str):
        ts   = time.strftime("%Y%m%d_%H%M%S")
        path = os.path.join(SAVE_DIR, f"ocr_result_{ts}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        log.info("OCR text saved: %s", path)
