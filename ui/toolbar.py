"""
VisionBoard AI – Toolbar
Professional dark-theme toolbar with active-state highlighting,
shape detection status, recording indicator, and OCR panel.
"""
import cv2
import numpy as np
from config import (
    TOOLBAR_H, BTN_W, TOOLBAR_BG, ACTIVE_BORDER, TEXT_COLOR,
    COLOR_PALETTE, TOOLS, CAM_WIDTH, BRAND_PRIMARY, BRAND_SUCCESS,
    BRAND_WARNING, APP_NAME,
)
from utils.helper_functions import draw_rounded_rect, text_center

_FONT = cv2.FONT_HERSHEY_SIMPLEX
_PAD  = 6
_SEP  = 10


class Toolbar:
    """
    Layout (left → right):
      [Brand label] | [Color swatches] | [Tool buttons] |
      [Size −][●][+] | [Undo][Redo][Clear][Save][PDF][Rec][OCR]
    """

    def __init__(self):
        self.color_rects:  list[tuple[int, int, int, int]] = []
        self.tool_rects:   list[tuple[int, int, int, int]] = []
        self.action_rects: dict[str, tuple[int, int, int, int]] = {}
        self._thickness_preview_rect: tuple[int, int, int, int] = (0, 0, 0, 0)
        self._build_layout()

    # ── Public ────────────────────────────────────────────────────────────────

    def draw(
        self,
        frame:          np.ndarray,
        active_color:   tuple[int, int, int],
        active_tool:    str,
        thickness:      int,
        fps:            float,
        is_recording:   bool         = False,
        rec_elapsed:    float        = 0.0,
        shape_result:   tuple | None = None,   # (name, confidence) or None
        ocr_text:       str          = "",
    ) -> np.ndarray:
        # Background
        cv2.rectangle(frame, (0, 0), (CAM_WIDTH, TOOLBAR_H), TOOLBAR_BG, -1)
        cv2.line(frame, (0, TOOLBAR_H), (CAM_WIDTH, TOOLBAR_H), (60, 60, 60), 1)

        self._draw_brand(frame)
        self._draw_colors(frame, active_color)
        self._draw_tools(frame, active_tool)
        self._draw_thickness(frame, thickness, active_color)
        self._draw_actions(frame, is_recording)
        self._draw_status_bar(frame, fps, is_recording, rec_elapsed, shape_result, ocr_text)
        return frame

    def hit_color(self, x: int, y: int) -> int | None:
        for i, (x1, y1, x2, y2) in enumerate(self.color_rects):
            if x1 <= x <= x2 and y1 <= y <= y2:
                return i
        return None

    def hit_tool(self, x: int, y: int) -> str | None:
        for i, (x1, y1, x2, y2) in enumerate(self.tool_rects):
            if x1 <= x <= x2 and y1 <= y <= y2:
                return TOOLS[i].lower()
        return None

    def hit_action(self, x: int, y: int) -> str | None:
        for name, (x1, y1, x2, y2) in self.action_rects.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                return name
        return None

    def in_toolbar(self, y: int) -> bool:
        return y < TOOLBAR_H

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self):
        btn_h = TOOLBAR_H - 2 * _PAD

        # Brand label space
        x = 112

        # Color swatches
        sw = btn_h
        for _ in COLOR_PALETTE:
            self.color_rects.append((x, _PAD, x + sw, _PAD + sw))
            x += sw + _PAD
        x += _SEP

        # Tool buttons
        for _ in TOOLS:
            self.tool_rects.append((x, _PAD, x + BTN_W, _PAD + btn_h))
            x += BTN_W + _PAD
        x += _SEP

        # Thickness −, preview circle, +
        bw = 34
        self.action_rects["thickness_down"] = (x, _PAD, x + bw, _PAD + btn_h)
        x += bw + _PAD
        self._thickness_preview_rect = (x, _PAD, x + bw, _PAD + btn_h)
        x += bw + _PAD
        self.action_rects["thickness_up"] = (x, _PAD, x + bw, _PAD + btn_h)
        x += bw + _SEP

        # Action buttons
        for key in ("undo", "redo", "clear", "save", "pdf", "record", "ocr"):
            self.action_rects[key] = (x, _PAD, x + BTN_W, _PAD + btn_h)
            x += BTN_W + _PAD

    # ── Renderers ─────────────────────────────────────────────────────────────

    def _draw_brand(self, frame):
        cv2.putText(frame, "VB", (8, 38), cv2.FONT_HERSHEY_DUPLEX,
                    1.1, BRAND_PRIMARY, 2, cv2.LINE_AA)
        cv2.putText(frame, "AI", (8, 62), _FONT, 0.45,
                    (160, 160, 180), 1, cv2.LINE_AA)

    def _draw_colors(self, frame, active_color):
        for (x1, y1, x2, y2), (_, bgr) in zip(self.color_rects, COLOR_PALETTE):
            draw_rounded_rect(frame, (x1, y1), (x2, y2), bgr, radius=5)
            if bgr == active_color:
                cv2.rectangle(frame, (x1 - 3, y1 - 3), (x2 + 3, y2 + 3),
                              ACTIVE_BORDER, 2)

    def _draw_tools(self, frame, active_tool):
        for (x1, y1, x2, y2), tool in zip(self.tool_rects, TOOLS):
            active = tool.lower() == active_tool
            bg     = (55, 55, 85) if active else (45, 45, 50)
            border = ACTIVE_BORDER if active else (70, 70, 75)
            draw_rounded_rect(frame, (x1, y1), (x2, y2), bg, radius=5)
            cv2.rectangle(frame, (x1, y1), (x2, y2), border, 1)
            text_center(frame, tool, (x1, y1, x2, y2), font_scale=0.36,
                        color=ACTIVE_BORDER if active else TEXT_COLOR)

    def _draw_thickness(self, frame, thickness, color):
        for key, label in (("thickness_down", "-"), ("thickness_up", "+")):
            x1, y1, x2, y2 = self.action_rects[key]
            draw_rounded_rect(frame, (x1, y1), (x2, y2), (45, 45, 50), radius=5)
            text_center(frame, label, (x1, y1, x2, y2), font_scale=0.7, color=TEXT_COLOR, thickness=2)

        px1, py1, px2, py2 = self._thickness_preview_rect
        draw_rounded_rect(frame, (px1, py1), (px2, py2), (35, 35, 40), radius=5)
        pcx, pcy = (px1 + px2) // 2, (py1 + py2) // 2
        r = max(2, min(thickness // 2, (py2 - py1) // 2 - 3))
        cv2.circle(frame, (pcx, pcy), r, color, -1, cv2.LINE_AA)

    def _draw_actions(self, frame, is_recording: bool):
        labels = {
            "undo": "Undo", "redo": "Redo", "clear": "Clear",
            "save": "Save", "pdf": "PDF",
            "record": "Stop" if is_recording else "Record",
            "ocr": "OCR",
        }
        for key, label in labels.items():
            x1, y1, x2, y2 = self.action_rects[key]
            # Record button pulses red when active
            if key == "record" and is_recording:
                bg     = (0, 0, 140)
                border = (0, 0, 220)
            else:
                bg     = (45, 45, 50)
                border = (70, 70, 75)
            draw_rounded_rect(frame, (x1, y1), (x2, y2), bg, radius=5)
            cv2.rectangle(frame, (x1, y1), (x2, y2), border, 1)
            text_center(frame, label, (x1, y1, x2, y2), font_scale=0.36, color=TEXT_COLOR)

    def _draw_status_bar(self, frame, fps, is_recording, rec_elapsed,
                          shape_result, ocr_text):
        # FPS — top-right
        cv2.putText(frame, f"FPS {fps:.0f}", (CAM_WIDTH - 90, 20),
                    _FONT, 0.45, BRAND_SUCCESS, 1, cv2.LINE_AA)

        # Recording timer — below FPS
        if is_recording:
            mins = int(rec_elapsed) // 60
            secs = int(rec_elapsed) % 60
            cv2.putText(frame, f"REC {mins:02d}:{secs:02d}", (CAM_WIDTH - 90, 40),
                        _FONT, 0.42, (0, 0, 220), 1, cv2.LINE_AA)

        # Shape detection result — bottom-left of toolbar
        if shape_result:
            name, conf = shape_result
            label = f"Shape: {name.capitalize()}  {conf*100:.0f}%"
            cv2.putText(frame, label, (8, TOOLBAR_H - 8),
                        _FONT, 0.42, BRAND_PRIMARY, 1, cv2.LINE_AA)

        # OCR result — bottom-center of toolbar
        if ocr_text:
            label = f"OCR: {ocr_text[:60]}"
            (tw, _), _ = cv2.getTextSize(label, _FONT, 0.42, 1)
            cv2.putText(frame, label, (CAM_WIDTH // 2 - tw // 2, TOOLBAR_H - 8),
                        _FONT, 0.42, BRAND_ACCENT if hasattr(frame, '__len__') else TEXT_COLOR,
                        1, cv2.LINE_AA)
