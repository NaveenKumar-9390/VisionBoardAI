"""
VisionBoard AI – Helper Functions
Shared small utilities used across modules.
"""
import math
import cv2
import numpy as np


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def dist(p1: tuple[int, int], p2: tuple[int, int]) -> float:
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def draw_rounded_rect(
    img: np.ndarray,
    pt1: tuple[int, int],
    pt2: tuple[int, int],
    color: tuple[int, int, int],
    radius: int = 8,
    thickness: int = -1,
):
    """Draw a filled or outlined rectangle with rounded corners."""
    x1, y1 = pt1
    x2, y2 = pt2
    r = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    if thickness == -1:   # filled
        cv2.rectangle(img, (x1 + r, y1), (x2 - r, y2), color, -1)
        cv2.rectangle(img, (x1, y1 + r), (x2, y2 - r), color, -1)
        for cx, cy in [(x1+r, y1+r), (x2-r, y1+r), (x1+r, y2-r), (x2-r, y2-r)]:
            cv2.circle(img, (cx, cy), r, color, -1)
    else:
        cv2.rectangle(img, (x1 + r, y1), (x2 - r, y2), color, thickness)
        cv2.rectangle(img, (x1, y1 + r), (x2, y2 - r), color, thickness)
        for cx, cy in [(x1+r, y1+r), (x2-r, y1+r), (x1+r, y2-r), (x2-r, y2-r)]:
            cv2.ellipse(img, (cx, cy), (r, r), 0, 0, 0, color, thickness)


def text_center(
    img: np.ndarray,
    text: str,
    rect: tuple[int, int, int, int],
    font_scale: float = 0.4,
    color: tuple = (220, 220, 220),
    thickness: int = 1,
):
    """Render *text* horizontally + vertically centered within *rect* (x1,y1,x2,y2)."""
    x1, y1, x2, y2 = rect
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), _ = cv2.getTextSize(text, font, font_scale, thickness)
    tx = x1 + (x2 - x1 - tw) // 2
    ty = y1 + (y2 - y1 + th) // 2
    cv2.putText(img, text, (tx, ty), font, font_scale, color, thickness, cv2.LINE_AA)
