"""
VisionBoard AI – Shape Detector
Analyses a completed stroke contour and auto-corrects it into a perfect shape.
"""
import cv2
import math
import numpy as np
from config import SHAPE_MIN_AREA, SHAPE_CONFIDENCE_THRESH, SHAPE_APPROX_EPSILON


class ShapeDetector:
    """
    Workflow:
      1. Extract contours from the drawn stroke layer.
      2. Run approxPolyDP to simplify vertices.
      3. Classify by vertex count + geometry ratios.
      4. If confidence >= threshold, replace rough shape with perfect one.
    """

    SHAPES = ("circle", "rectangle", "square", "triangle", "line")

    # ── Public API ────────────────────────────────────────────────────────────

    def detect_and_correct(
        self,
        layer: np.ndarray,
        color: tuple[int, int, int],
        thickness: int,
    ) -> tuple[str, float] | tuple[None, None]:
        """
        Scan *layer* for a recognisable shape.
        If found with sufficient confidence, overwrite the rough stroke
        with a perfect shape drawn in *color* at *thickness*.
        Returns (shape_name, confidence) or (None, None).
        """
        gray    = cv2.cvtColor(layer, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, None

        contour = max(contours, key=cv2.contourArea)
        area    = cv2.contourArea(contour)
        if area < SHAPE_MIN_AREA:
            return None, None

        peri    = cv2.arcLength(contour, True)
        approx  = cv2.approxPolyDP(contour, SHAPE_APPROX_EPSILON * peri, True)
        verts   = len(approx)
        x, y, w, h = cv2.boundingRect(approx)

        shape, confidence = self._classify(contour, approx, verts, area, peri, w, h)

        if shape is not None and confidence >= SHAPE_CONFIDENCE_THRESH:
            self._erase_and_redraw(layer, contour, shape, approx, color, thickness, x, y, w, h)
            return shape, round(confidence, 2)

        return None, None

    # ── Classification ────────────────────────────────────────────────────────

    def _classify(self, contour, approx, verts, area, peri, w, h):
        if verts == 2 or (verts <= 4 and self._is_line(approx)):
            return "line", self._line_confidence(approx)

        circularity = (4 * math.pi * area) / (peri ** 2) if peri > 0 else 0
        if circularity > 0.75:
            return "circle", min(circularity, 1.0)

        if verts == 3:
            return "triangle", self._triangle_confidence(approx, area)

        if verts == 4:
            aspect = w / h if h > 0 else 1
            is_square = 0.85 <= aspect <= 1.15
            # Check how rectangular the approx is
            rect_conf = self._rect_confidence(approx, w, h)
            if is_square:
                return "square", rect_conf
            return "rectangle", rect_conf

        return None, 0.0

    # ── Confidence scorers ────────────────────────────────────────────────────

    @staticmethod
    def _line_confidence(approx) -> float:
        pts = approx.reshape(-1, 2).astype(float)
        if len(pts) < 2:
            return 0.0
        d = np.linalg.norm(pts[-1] - pts[0])
        span = sum(np.linalg.norm(pts[i+1] - pts[i]) for i in range(len(pts)-1))
        return min(d / span, 1.0) if span > 0 else 0.0

    @staticmethod
    def _is_line(approx) -> bool:
        pts = approx.reshape(-1, 2).astype(float)
        d   = np.linalg.norm(pts[-1] - pts[0])
        span = sum(np.linalg.norm(pts[i+1] - pts[i]) for i in range(len(pts)-1))
        return (d / span > 0.88) if span > 0 else False

    @staticmethod
    def _triangle_confidence(approx, area) -> float:
        pts   = approx.reshape(-1, 2).astype(float)
        sides = [np.linalg.norm(pts[(i+1)%3] - pts[i]) for i in range(3)]
        ratio = min(sides) / max(sides) if max(sides) > 0 else 0
        return 0.6 + 0.4 * ratio

    @staticmethod
    def _rect_confidence(approx, w, h) -> float:
        pts    = approx.reshape(-1, 2).astype(float)
        angles = []
        for i in range(4):
            a = pts[(i-1) % 4] - pts[i]
            b = pts[(i+1) % 4] - pts[i]
            cos_a = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-6)
            angles.append(abs(math.degrees(math.acos(np.clip(cos_a, -1, 1))) - 90))
        avg_dev = sum(angles) / 4
        return max(0.0, 1.0 - avg_dev / 45)

    # ── Redraw ────────────────────────────────────────────────────────────────

    @staticmethod
    def _erase_and_redraw(layer, contour, shape, approx, color, thickness, x, y, w, h):
        # Erase the rough stroke in the bounding area
        mask = np.zeros(layer.shape[:2], dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, 255, cv2.FILLED)
        kernel = np.ones((20, 20), np.uint8)
        mask   = cv2.dilate(mask, kernel)
        layer[mask > 0] = 0

        # Draw perfect shape
        pad = thickness + 4
        if shape == "circle":
            cx, cy = x + w // 2, y + h // 2
            r      = (w + h) // 4
            cv2.circle(layer, (cx, cy), r, color, thickness, cv2.LINE_AA)

        elif shape in ("rectangle", "square"):
            cv2.rectangle(layer, (x + pad, y + pad), (x + w - pad, y + h - pad),
                          color, thickness, cv2.LINE_AA)

        elif shape == "triangle":
            pts = approx.reshape(-1, 2)
            cv2.polylines(layer, [pts], True, color, thickness, cv2.LINE_AA)

        elif shape == "line":
            pts = approx.reshape(-1, 2)
            cv2.line(layer, tuple(pts[0]), tuple(pts[-1]), color, thickness, cv2.LINE_AA)
