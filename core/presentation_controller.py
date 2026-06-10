"""
VisionBoard AI – Presentation Controller
Detects left/right swipe gestures from hand palm position to control slide navigation.
Uses pyautogui to send arrow key presses.
"""
import logging
from collections import deque
from config import SWIPE_THRESHOLD_PX, SWIPE_MIN_FRAMES, SWIPE_COOLDOWN_FRAMES

log = logging.getLogger(__name__)

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    _PYAUTOGUI = True
except ImportError:
    _PYAUTOGUI = False
    log.warning("pyautogui not installed — presentation control disabled. Run: pip install pyautogui")

# Gesture finger patterns [thumb, index, middle, ring, pinky]
_OPEN_PALM  = [1, 1, 1, 1, 1]
_CLOSED_FIST = [0, 0, 0, 0, 0]


class PresentationController:

    def __init__(self):
        self._palm_x_history: deque[int] = deque(maxlen=12)
        self._cooldown   = 0
        self._active     = False   # presentation mode on/off
        self._last_action = ""

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def last_action(self) -> str:
        return self._last_action

    def update(self, lm_list: list, fingers: list[int]) -> str | None:
        """
        Call every frame. Returns action string or None.
        Actions: "start", "end", "next", "prev"
        """
        if not lm_list or not fingers:
            return None

        # Toggle presentation mode
        if fingers == _OPEN_PALM and not self._active:
            self._active     = True
            self._last_action = "start"
            log.info("Presentation mode started.")
            return "start"

        if fingers == _CLOSED_FIST and self._active:
            self._active     = False
            self._last_action = "end"
            log.info("Presentation mode ended.")
            return "end"

        if not self._active:
            return None

        # Track palm (landmark 0) x position
        palm_x = lm_list[0][1]
        self._palm_x_history.append(palm_x)

        if self._cooldown > 0:
            self._cooldown -= 1
            return None

        return self._detect_swipe()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _detect_swipe(self) -> str | None:
        if len(self._palm_x_history) < SWIPE_MIN_FRAMES + 1:
            return None

        xs     = list(self._palm_x_history)
        delta  = xs[-1] - xs[-SWIPE_MIN_FRAMES]
        moving = all(
            (xs[i+1] - xs[i]) * (1 if delta > 0 else -1) > 0
            for i in range(len(xs) - SWIPE_MIN_FRAMES, len(xs) - 1)
        )

        if not moving or abs(delta) < SWIPE_THRESHOLD_PX:
            return None

        self._cooldown = SWIPE_COOLDOWN_FRAMES
        self._palm_x_history.clear()

        if delta > 0:   # hand moved right → next slide
            if _PYAUTOGUI:
                pyautogui.press("right")
            self._last_action = "next"
            log.info("Swipe → Next slide")
            return "next"
        else:           # hand moved left → previous slide
            if _PYAUTOGUI:
                pyautogui.press("left")
            self._last_action = "prev"
            log.info("Swipe ← Previous slide")
            return "prev"
