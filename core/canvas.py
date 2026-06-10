"""Canvas with undo/redo stack and multi-layer support."""
import copy
import numpy as np
from config import MAX_UNDO_STEPS


class Canvas:
    def __init__(self, width: int, height: int):
        self.w, self.h = width, height
        self._bg   = np.zeros((height, width, 3), dtype=np.uint8)   # background layer
        self._draw = np.zeros((height, width, 3), dtype=np.uint8)   # drawing layer
        self._undo_stack: list[np.ndarray] = []
        self._redo_stack: list[np.ndarray] = []

    # ── Layer access ─────────────────────────────────────────────────────────

    @property
    def drawing(self) -> np.ndarray:
        return self._draw

    def composite(self, camera_frame: np.ndarray) -> np.ndarray:
        """Blend camera frame + drawing layer and return result."""
        return cv_add(camera_frame, self._draw)

    # ── Stroke lifecycle ─────────────────────────────────────────────────────

    def begin_stroke(self):
        """Call before starting a new stroke to snapshot for undo."""
        self._push_undo(self._draw.copy())
        self._redo_stack.clear()

    def undo(self):
        if self._undo_stack:
            self._redo_stack.append(self._draw.copy())
            self._draw = self._undo_stack.pop()

    def redo(self):
        if self._redo_stack:
            self._undo_stack.append(self._draw.copy())
            self._draw = self._redo_stack.pop()

    def clear(self):
        self._push_undo(self._draw.copy())
        self._redo_stack.clear()
        self._draw = np.zeros((self.h, self.w, 3), dtype=np.uint8)

    # ── Drawing primitives ────────────────────────────────────────────────────

    @property
    def layer(self) -> np.ndarray:
        """Direct access to drawing layer for cv2 operations."""
        return self._draw

    # ── Internal ─────────────────────────────────────────────────────────────

    def _push_undo(self, state: np.ndarray):
        self._undo_stack.append(state)
        if len(self._undo_stack) > MAX_UNDO_STEPS:
            self._undo_stack.pop(0)


def cv_add(frame: np.ndarray, overlay: np.ndarray) -> np.ndarray:
    """Add overlay onto frame; overlay black pixels are transparent."""
    mask = overlay.any(axis=2)
    out  = frame.copy()
    out[mask] = overlay[mask]
    return out
