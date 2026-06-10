"""Brush rendering utilities: pencil, marker, highlighter, calligraphy, eraser."""
import cv2
import numpy as np


def draw_stroke(
    layer:     np.ndarray,
    pt1:       tuple[int, int],
    pt2:       tuple[int, int],
    color:     tuple[int, int, int],
    thickness: int,
    brush:     str,
):
    """Dispatch to the correct brush renderer."""
    if brush == "eraser":
        _eraser(layer, pt1, pt2, thickness)
    elif brush == "pencil":
        _pencil(layer, pt1, pt2, color, thickness)
    elif brush == "highlighter":
        _highlighter(layer, pt1, pt2, color, thickness)
    elif brush == "calligraphy":
        _calligraphy(layer, pt1, pt2, color, thickness)
    else:  # marker (default)
        _marker(layer, pt1, pt2, color, thickness)


# ── Brush implementations ─────────────────────────────────────────────────────

def _marker(layer, pt1, pt2, color, t):
    cv2.line(layer, pt1, pt2, color, t, cv2.LINE_AA)


def _pencil(layer, pt1, pt2, color, t):
    """Thin, slightly noisy stroke to mimic pencil."""
    thin = max(1, t // 3)
    # Add subtle texture via small offsets
    for dx, dy in [(0, 0), (1, 0), (0, 1)]:
        p1 = (pt1[0] + dx, pt1[1] + dy)
        p2 = (pt2[0] + dx, pt2[1] + dy)
        alpha_color = tuple(max(0, c - 40) for c in color)
        cv2.line(layer, p1, p2, alpha_color, thin, cv2.LINE_AA)
    cv2.line(layer, pt1, pt2, color, thin, cv2.LINE_AA)


def _highlighter(layer, pt1, pt2, color, t):
    """Semi-transparent wide stroke. Simulated with a blended rectangle."""
    overlay = layer.copy()
    thick = max(t * 3, 20)
    cv2.line(overlay, pt1, pt2, color, thick, cv2.LINE_AA)
    cv2.addWeighted(overlay, 0.35, layer, 0.65, 0, layer)


def _calligraphy(layer, pt1, pt2, color, t):
    """Angled flat nib: draws two offset thin lines."""
    offset = max(1, t // 2)
    for d in range(-offset, offset + 1, max(1, offset)):
        p1 = (pt1[0] + d, pt1[1] - d)
        p2 = (pt2[0] + d, pt2[1] - d)
        cv2.line(layer, p1, p2, color, max(1, t // 3), cv2.LINE_AA)


def _eraser(layer, pt1, pt2, t):
    cv2.line(layer, pt1, pt2, (0, 0, 0), t, cv2.LINE_AA)
