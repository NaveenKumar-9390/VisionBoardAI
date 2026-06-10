"""Maps finger patterns to application actions with hold-frame debouncing."""
from config import (
    GESTURE_DRAW, GESTURE_SELECT, GESTURE_UNDO, GESTURE_CLEAR,
    GESTURE_SAVE, GESTURE_THICKNESS_UP, GESTURE_THICKNESS_DOWN,
    GESTURE_HOLD_FRAMES,
)


class GestureController:
    """
    Returns a stable action only after the gesture is held for
    GESTURE_HOLD_FRAMES consecutive frames, preventing false triggers.
    """

    GESTURE_MAP = {
        "draw":           GESTURE_DRAW,
        "select":         GESTURE_SELECT,
        "undo":           GESTURE_UNDO,
        "clear":          GESTURE_CLEAR,
        "save":           GESTURE_SAVE,
        "thickness_up":   GESTURE_THICKNESS_UP,
        "thickness_down": GESTURE_THICKNESS_DOWN,
    }

    def __init__(self):
        self._current_gesture = None
        self._hold_count      = 0
        self._fired           = False   # ensures one-shot for latch actions

    def update(self, fingers: list[int]) -> tuple[str, bool]:
        """
        Call every frame with the current finger state.
        Returns (gesture_name, just_activated).
        - gesture_name  : string key or "idle"
        - just_activated: True only on the frame the gesture first locks in
        """
        if not fingers:
            self._reset()
            return "idle", False

        matched = next(
            (name for name, pattern in self.GESTURE_MAP.items() if fingers == pattern),
            "idle",
        )

        if matched == self._current_gesture:
            self._hold_count += 1
        else:
            self._current_gesture = matched
            self._hold_count      = 1
            self._fired           = False

        if self._hold_count >= GESTURE_HOLD_FRAMES and not self._fired:
            # latch one-shot gestures so they don't repeat every frame
            if matched in ("undo", "clear", "save", "thickness_up", "thickness_down"):
                self._fired = True
            return matched, True

        return matched, False

    def _reset(self):
        self._current_gesture = None
        self._hold_count      = 0
        self._fired           = False
