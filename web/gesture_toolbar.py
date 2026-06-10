"""
VisionBoard AI – Gesture Toolbar (Web)
Renders a fully interactive toolbar onto the live video frame.
All interaction is touchless: enter Selection Mode (index + middle fingers),
hover the fingertip over a button for HOVER_HOLD_FRAMES consecutive frames,
and the action fires automatically.

Completely self-contained — called once per frame from the webrtc callback.
No Streamlit imports; no thread concerns beyond what WebState already handles.
"""
import math
import cv2
import numpy as np
from config import (
    COLOR_PALETTE, TOOLS, TOOLBAR_H, BTN_W,
    TOOLBAR_BG, ACTIVE_BORDER, TEXT_COLOR,
    MIN_THICKNESS, MAX_THICKNESS, THICKNESS_STEP,
    BRAND_PRIMARY, BRAND_SUCCESS, BRAND_WARNING, BRAND_ACCENT,
    CAM_WIDTH,
)

# ── Hover parameters ──────────────────────────────────────────────────────────
HOVER_HOLD_FRAMES = 30   # ~1 s at 30 fps before action fires
_FONT = cv2.FONT_HERSHEY_SIMPLEX


class GestureToolbar:
    """
    Manages button layout, hit-testing, dwell-time progress, and visual feedback.
    One instance per session, stored inside WebState.
    """

    def __init__(self):
        # Dwell-time tracking
        self.hover_target: str | None = None   # button key currently being hovered
        self.hover_frames: int        = 0      # consecutive frames over same button

        # Pre-computed button rects  {key: (x1, y1, x2, y2)}
        self._rects: dict[str, tuple[int, int, int, int]] = {}
        self._build_layout()

    # ── Public API ────────────────────────────────────────────────────────────

    def process(
        self,
        frame:    np.ndarray,
        ix: int,
        iy: int,
        gesture:  str,
        state,                  # WebState — imported at call-site to avoid circular import
    ) -> str | None:
        """
        Call every frame when a hand is detected.
        - Draws the toolbar onto *frame* in-place.
        - If gesture == "select" and fingertip is inside toolbar zone:
            tracks dwell time and fires action when threshold reached.
        - Returns the action key that just fired, or None.
        """
        self._draw_toolbar(frame, state)

        # Only process toolbar interaction in select mode
        if gesture != "select" or iy >= TOOLBAR_H:
            # Fingertip left the toolbar — reset dwell
            self.hover_target = None
            self.hover_frames = 0
            return None

        hit = self._hit_test(ix, iy)
        if hit is None:
            self.hover_target = None
            self.hover_frames = 0
            return None

        # Same button as last frame → accumulate dwell
        if hit == self.hover_target:
            self.hover_frames += 1
        else:
            self.hover_target = hit
            self.hover_frames = 1

        # Draw hover progress ring around fingertip
        self._draw_hover_feedback(frame, ix, iy, hit, self.hover_frames)

        # Fire when dwell threshold reached
        if self.hover_frames >= HOVER_HOLD_FRAMES:
            self.hover_target = None
            self.hover_frames = 0
            return hit

        return None

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self):
        pad = 6
        sep = 10
        sw  = TOOLBAR_H - 2 * pad    # swatch / button height
        x   = 108                    # leave space for brand label

        # Color swatches
        for i, (name, _) in enumerate(COLOR_PALETTE):
            self._rects[f"color_{i}"] = (x, pad, x + sw, pad + sw)
            x += sw + pad
        x += sep

        # Tool buttons
        for tool in TOOLS:
            self._rects[f"tool_{tool.lower()}"] = (x, pad, x + BTN_W, pad + sw)
            x += BTN_W + pad
        x += sep

        # Thickness −, +
        bw = 34
        self._rects["thickness_down"] = (x, pad, x + bw, pad + sw)
        x += bw + pad
        self._rects["thickness_preview"] = (x, pad, x + bw, pad + sw)   # non-interactive
        x += bw + pad
        self._rects["thickness_up"] = (x, pad, x + bw, pad + sw)
        x += bw + sep

        # Action buttons
        for key in ("undo", "redo", "clear", "save", "ocr"):
            self._rects[key] = (x, pad, x + BTN_W, pad + sw)
            x += BTN_W + pad

    # ── Hit test ──────────────────────────────────────────────────────────────

    def _hit_test(self, x: int, y: int) -> str | None:
        for key, (x1, y1, x2, y2) in self._rects.items():
            if key == "thickness_preview":
                continue
            if x1 <= x <= x2 and y1 <= y <= y2:
                return key
        return None

    # ── Toolbar rendering ─────────────────────────────────────────────────────

    def _draw_toolbar(self, frame: np.ndarray, state):
        # Background bar
        cv2.rectangle(frame, (0, 0), (CAM_WIDTH, TOOLBAR_H), TOOLBAR_BG, -1)
        cv2.line(frame, (0, TOOLBAR_H), (CAM_WIDTH, TOOLBAR_H), (60, 60, 60), 1)

        # Brand mark
        cv2.putText(frame, "VB", (8, 38), cv2.FONT_HERSHEY_DUPLEX,
                    1.05, BRAND_PRIMARY, 2, cv2.LINE_AA)
        cv2.putText(frame, "AI", (8, 58), _FONT, 0.4,
                    (160, 160, 180), 1, cv2.LINE_AA)

        self._draw_colors(frame, state.color)
        self._draw_tools(frame, state.tool)
        self._draw_thickness_controls(frame, state.thickness, state.color)
        self._draw_action_buttons(frame)
        self._draw_mode_indicator(frame, state.gesture_label)

    def _draw_colors(self, frame, active_color):
        for i, (name, bgr) in enumerate(COLOR_PALETTE):
            x1, y1, x2, y2 = self._rects[f"color_{i}"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), bgr, -1)
            is_active = (bgr == active_color)
            border = ACTIVE_BORDER if is_active else (80, 80, 80)
            bw = 2 if is_active else 1
            cv2.rectangle(frame, (x1 - bw, y1 - bw), (x2 + bw, y2 + bw), border, bw)
            # Highlight glow for active
            if is_active:
                _draw_glow_rect(frame, x1, y1, x2, y2, ACTIVE_BORDER)

    def _draw_tools(self, frame, active_tool):
        for tool in TOOLS:
            x1, y1, x2, y2 = self._rects[f"tool_{tool.lower()}"]
            active = tool.lower() == active_tool
            bg = (55, 55, 85) if active else (45, 45, 50)
            cv2.rectangle(frame, (x1, y1), (x2, y2), bg, -1)
            border = ACTIVE_BORDER if active else (70, 70, 75)
            cv2.rectangle(frame, (x1, y1), (x2, y2), border, 1)
            if active:
                _draw_glow_rect(frame, x1, y1, x2, y2, ACTIVE_BORDER)
            col = ACTIVE_BORDER if active else TEXT_COLOR
            _text_center(frame, tool, x1, y1, x2, y2, 0.36, col)

    def _draw_thickness_controls(self, frame, thickness, color):
        for key, label in (("thickness_down", "-"), ("thickness_up", "+")):
            x1, y1, x2, y2 = self._rects[key]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (45, 45, 50), -1)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (70, 70, 75), 1)
            _text_center(frame, label, x1, y1, x2, y2, 0.7, TEXT_COLOR, thickness=2)

        px1, py1, px2, py2 = self._rects["thickness_preview"]
        cv2.rectangle(frame, (px1, py1), (px2, py2), (35, 35, 40), -1)
        cv2.rectangle(frame, (px1, py1), (px2, py2), (70, 70, 75), 1)
        cx, cy = (px1 + px2) // 2, (py1 + py2) // 2
        r = max(2, min(thickness // 2, (py2 - py1) // 2 - 3))
        cv2.circle(frame, (cx, cy), r, color, -1, cv2.LINE_AA)

    def _draw_action_buttons(self, frame):
        labels = {"undo": "Undo", "redo": "Redo", "clear": "Clear",
                  "save": "Save", "ocr": "OCR"}
        for key, label in labels.items():
            x1, y1, x2, y2 = self._rects[key]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (45, 45, 50), -1)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (70, 70, 75), 1)
            _text_center(frame, label, x1, y1, x2, y2, 0.36, TEXT_COLOR)

    def _draw_mode_indicator(self, frame, gesture_label):
        # Right side: mode pill
        mode_map = {
            "draw":   ("DRAW",   BRAND_SUCCESS),
            "select": ("SELECT", BRAND_PRIMARY),
            "idle":   ("IDLE",   (80, 80, 100)),
        }
        label, color = mode_map.get(gesture_label, ("", (80, 80, 100)))
        if label:
            (tw, th), _ = cv2.getTextSize(label, _FONT, 0.42, 1)
            rx = CAM_WIDTH - tw - 20
            ry = 8
            cv2.rectangle(frame, (rx - 6, ry), (rx + tw + 6, ry + th + 10),
                          (30, 30, 40), -1)
            cv2.rectangle(frame, (rx - 6, ry), (rx + tw + 6, ry + th + 10),
                          color, 1)
            cv2.putText(frame, label, (rx, ry + th + 4),
                        _FONT, 0.42, color, 1, cv2.LINE_AA)

    # ── Hover feedback ────────────────────────────────────────────────────────

    def _draw_hover_feedback(
        self, frame: np.ndarray,
        ix: int, iy: int,
        target: str, frames: int,
    ):
        progress = min(frames / HOVER_HOLD_FRAMES, 1.0)

        # Arc progress ring around fingertip
        axes = (18, 18)
        angle_end = int(360 * progress)
        cv2.ellipse(frame, (ix, iy), axes, -90, 0, angle_end,
                    BRAND_PRIMARY, 2, cv2.LINE_AA)
        cv2.ellipse(frame, (ix, iy), axes, -90, angle_end, 360,
                    (60, 60, 80), 1, cv2.LINE_AA)

        # Percentage text inside ring
        pct = f"{int(progress * 100)}%"
        (tw, _), _ = cv2.getTextSize(pct, _FONT, 0.35, 1)
        cv2.putText(frame, pct, (ix - tw // 2, iy + 4),
                    _FONT, 0.35, (220, 220, 220), 1, cv2.LINE_AA)

        # Highlight the hovered button
        if target in self._rects:
            x1, y1, x2, y2 = self._rects[target]
            alpha = 0.25 + 0.25 * progress
            overlay = frame.copy()
            cv2.rectangle(overlay, (x1, y1), (x2, y2), BRAND_PRIMARY, -1)
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
            cv2.rectangle(frame, (x1, y1), (x2, y2), BRAND_PRIMARY, 1)

        # Label at top of toolbar showing what's being hovered
        human = _button_label(target)
        status = f"Hovering: {human}  {int(progress*100)}%"
        (sw, _), _ = cv2.getTextSize(status, _FONT, 0.45, 1)
        sx = CAM_WIDTH // 2 - sw // 2
        cv2.putText(frame, status, (sx, TOOLBAR_H + 22),
                    _FONT, 0.45, BRAND_ACCENT, 1, cv2.LINE_AA)


# ── Helper renderers ──────────────────────────────────────────────────────────

def _draw_glow_rect(frame, x1, y1, x2, y2, color, layers=2):
    """Subtle neon glow by drawing thin expanding rectangles with low alpha."""
    overlay = frame.copy()
    for d in range(1, layers + 1):
        cv2.rectangle(overlay,
                      (x1 - d, y1 - d), (x2 + d, y2 + d),
                      color, 1)
    cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)


def _text_center(frame, text, x1, y1, x2, y2,
                  scale=0.38, color=TEXT_COLOR, thickness=1):
    font = _FONT
    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    tx = x1 + (x2 - x1 - tw) // 2
    ty = y1 + (y2 - y1 + th) // 2
    cv2.putText(frame, text, (tx, ty), font, scale, color, thickness, cv2.LINE_AA)


def _button_label(key: str) -> str:
    if key.startswith("color_"):
        idx = int(key.split("_")[1])
        return COLOR_PALETTE[idx][0]
    if key.startswith("tool_"):
        return key.split("_")[1].capitalize()
    return key.replace("_", " ").capitalize()
