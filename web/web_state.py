"""
VisionBoard AI – Web State
Thread-safe container for all mutable drawing state shared between
the streamlit-webrtc background thread and the Streamlit main thread.
"""
import threading
import numpy as np
from config import (
    CAM_WIDTH, CAM_HEIGHT, DEFAULT_COLOR, DEFAULT_BRUSH,
    DEFAULT_THICKNESS, MAX_UNDO_STEPS, MIN_THICKNESS, MAX_THICKNESS, THICKNESS_STEP,
)
from core.canvas import Canvas
from core.gesture_controller import GestureController
from core.hand_tracker import HandTracker
from core.shape_detector import ShapeDetector


class WebState:
    """
    Holds all runtime state for one browser session.
    Instantiate once and store in st.session_state.
    """

    def __init__(self):
        self._lock = threading.Lock()

        # ── Core modules ──────────────────────────────────────────────────────
        self.tracker  = HandTracker()
        self.gestures = GestureController()
        self.canvas   = Canvas(CAM_WIDTH, CAM_HEIGHT)
        self.shapes   = ShapeDetector()

        # Gesture toolbar — imported lazily to avoid import-time side effects
        from web.gesture_toolbar import GestureToolbar
        self.toolbar  = GestureToolbar()

        # ── Drawing state ─────────────────────────────────────────────────────
        self.color     = DEFAULT_COLOR
        self.tool      = DEFAULT_BRUSH
        self.thickness = DEFAULT_THICKNESS
        self.prev_pt:   tuple[int, int] | None = None
        self.in_stroke: bool = False

        # ── UI feedback state ─────────────────────────────────────────────────
        self.gesture_label: str         = ""
        self.shape_result:  tuple | None = None
        self.ocr_text:      str          = ""
        self.notification:  str          = ""

        # Flag set by webrtc thread when OCR gesture fires — read by main thread
        self.ocr_requested: bool = False

        # ── Last composite frame ──────────────────────────────────────────────
        self._last_frame: np.ndarray = np.zeros(
            (CAM_HEIGHT, CAM_WIDTH, 3), dtype=np.uint8
        )

    # ── Thread-safe accessors ─────────────────────────────────────────────────

    def get_canvas_snapshot(self) -> np.ndarray:
        with self._lock:
            return self.canvas.layer.copy()

    def set_last_frame(self, frame: np.ndarray):
        with self._lock:
            self._last_frame = frame.copy()

    def get_last_frame(self) -> np.ndarray:
        with self._lock:
            return self._last_frame.copy()

    # ── Actions (callable from both threads) ──────────────────────────────────

    def undo(self):
        with self._lock:
            self.canvas.undo()
            self.notification = "↩  Undo"

    def redo(self):
        with self._lock:
            self.canvas.redo()
            self.notification = "↪  Redo"

    def clear(self):
        with self._lock:
            self.canvas.clear()
            self.notification = "✕  Canvas cleared"

    def set_color(self, bgr: tuple, name: str = ""):
        with self._lock:
            self.color = bgr
            if self.tool == "eraser":
                self.tool = DEFAULT_BRUSH
            self.notification = f"🎨  Color: {name}" if name else ""

    def set_tool(self, tool: str):
        with self._lock:
            self.tool = tool
            self.notification = f"🖌  Tool: {tool.capitalize()}"

    def set_thickness(self, value: int):
        with self._lock:
            self.thickness = max(MIN_THICKNESS, min(MAX_THICKNESS, value))
            self.notification = f"📏  Size: {self.thickness}"

    def bump_thickness(self, direction: int):
        """direction: +1 to increase, -1 to decrease."""
        with self._lock:
            self.thickness = max(
                MIN_THICKNESS,
                min(MAX_THICKNESS, self.thickness + direction * THICKNESS_STEP),
            )
            self.notification = f"📏  Size: {self.thickness}"

    def request_ocr(self):
        with self._lock:
            self.ocr_requested = True
            self.notification  = "🔤  OCR triggered…"

    def consume_ocr_request(self) -> bool:
        """Returns True and clears the flag if an OCR request is pending."""
        with self._lock:
            if self.ocr_requested:
                self.ocr_requested = False
                return True
            return False
