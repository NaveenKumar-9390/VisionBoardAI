"""Hand tracking wrapper with landmark smoothing and jitter reduction."""
import cv2
import mediapipe as mp
import numpy as np
from config import MAX_HANDS, DETECTION_CON, TRACKING_CON, SMOOTH_FACTOR


class HandTracker:
    TIP_IDS = [4, 8, 12, 16, 20]

    def __init__(self):
        self._mp_hands = mp.solutions.hands
        self._mp_draw  = mp.solutions.drawing_utils
        self._hands    = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=MAX_HANDS,
            min_detection_confidence=DETECTION_CON,
            min_tracking_confidence=TRACKING_CON,
        )
        self._results  = None
        # exponential moving average smoothing per landmark
        self._smooth: dict[int, np.ndarray] = {}

    # ── Public API ────────────────────────────────────────────────────────────

    def process(self, img: np.ndarray, draw: bool = True) -> np.ndarray:
        """Detect hands in *img* (BGR). Returns annotated image."""
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self._results = self._hands.process(rgb)
        if draw and self._results.multi_hand_landmarks:
            for lms in self._results.multi_hand_landmarks:
                self._mp_draw.draw_landmarks(
                    img, lms, self._mp_hands.HAND_CONNECTIONS,
                    self._mp_draw.DrawingSpec(color=(0, 255, 255), thickness=1, circle_radius=2),
                    self._mp_draw.DrawingSpec(color=(255, 255, 0), thickness=1),
                )
        return img

    def get_landmarks(self, img: np.ndarray, hand_no: int = 0) -> list[list[int]]:
        """Return smoothed landmark list [[id, x, y], ...] or []."""
        if not self._results or not self._results.multi_hand_landmarks:
            self._smooth.clear()
            return []
        if hand_no >= len(self._results.multi_hand_landmarks):
            return []

        h, w = img.shape[:2]
        lm_list: list[list[int]] = []
        for lm_id, lm in enumerate(self._results.multi_hand_landmarks[hand_no].landmark):
            raw = np.array([lm.x * w, lm.y * h])
            if lm_id in self._smooth:
                smoothed = self._smooth[lm_id] * SMOOTH_FACTOR + raw * (1 - SMOOTH_FACTOR)
            else:
                smoothed = raw
            self._smooth[lm_id] = smoothed
            lm_list.append([lm_id, int(smoothed[0]), int(smoothed[1])])
        return lm_list

    def fingers_up(self, lm_list: list[list[int]]) -> list[int]:
        """Return [thumb, index, middle, ring, pinky] as 0/1."""
        if len(lm_list) < 21:
            return []
        fingers = []
        # Thumb: compare x-axis
        fingers.append(1 if lm_list[self.TIP_IDS[0]][1] > lm_list[self.TIP_IDS[0] - 1][1] else 0)
        # Other fingers: compare y-axis
        for i in range(1, 5):
            tip = self.TIP_IDS[i]
            fingers.append(1 if lm_list[tip][2] < lm_list[tip - 2][2] else 0)
        return fingers
