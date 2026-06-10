"""
VisionBoard AI – Gesture Controlled Drawing System
Central configuration — all tunable constants live here.
"""
import os

_BASE = os.path.dirname(__file__)

# ── Product Identity ──────────────────────────────────────────────────────────
APP_NAME    = "VisionBoard AI"
APP_TAGLINE = "Transform Gestures into Ideas."
APP_VERSION = "2.0.0"
WINDOW_TITLE = f"{APP_NAME}  ·  {APP_TAGLINE}"

# ── Camera ────────────────────────────────────────────────────────────────────
CAM_WIDTH  = 1280
CAM_HEIGHT = 720

# ── Hand Tracking ─────────────────────────────────────────────────────────────
MAX_HANDS     = 1
DETECTION_CON = 0.75
TRACKING_CON  = 0.75
SMOOTH_FACTOR = 0.35   # EMA weight for previous position (0 = raw, 1 = frozen)

# ── Drawing Defaults ──────────────────────────────────────────────────────────
DEFAULT_COLOR     = (212, 182, 6)    # BGR cyan-ish brand primary
DEFAULT_BRUSH     = "marker"
DEFAULT_THICKNESS = 8
ERASER_THICKNESS  = 60
MIN_THICKNESS     = 2
MAX_THICKNESS     = 40
THICKNESS_STEP    = 2

# ── Undo / Redo ───────────────────────────────────────────────────────────────
MAX_UNDO_STEPS = 30

# ── Brand Colors (BGR) ────────────────────────────────────────────────────────
BRAND_PRIMARY   = (212, 182, 6)    # #06B6D4 → BGR
BRAND_SECONDARY = (246, 130, 59)   # #3B82F6
BRAND_ACCENT    = (238, 211, 34)   # #22D3EE
BRAND_SUCCESS   = (145, 185, 16)   # #10B981
BRAND_WARNING   = (11, 158, 245)   # #F59E0B
BRAND_BG        = (42, 23, 15)     # #0F172A

# ── Toolbar ───────────────────────────────────────────────────────────────────
TOOLBAR_H     = 96
BTN_W         = 76
TOOLBAR_BG    = (42, 23, 15)       # dark navy background
ACTIVE_BORDER = BRAND_PRIMARY
TEXT_COLOR    = (220, 220, 220)

# Color palette (label, BGR)
COLOR_PALETTE = [
    ("Red",    (50,  50,  220)),
    ("Green",  (50,  200, 50)),
    ("Blue",   (220, 80,  50)),
    ("Yellow", (0,   210, 230)),
    ("White",  (240, 240, 240)),
    ("Purple", (200, 50,  180)),
]

# Tool buttons
TOOLS = ["Pencil", "Marker", "Highlight", "Calligraphy", "Eraser"]

# ── Gesture Patterns [thumb, index, middle, ring, pinky] ──────────────────────
GESTURE_DRAW           = [0, 1, 0, 0, 0]
GESTURE_SELECT         = [0, 1, 1, 0, 0]
GESTURE_UNDO           = [1, 1, 1, 1, 0]
GESTURE_CLEAR          = [1, 1, 1, 1, 1]
GESTURE_SAVE           = [1, 0, 0, 0, 1]   # shaka
GESTURE_THICKNESS_UP   = [0, 1, 1, 1, 0]
GESTURE_THICKNESS_DOWN = [0, 0, 1, 1, 1]
GESTURE_RECORD_TOGGLE  = [1, 1, 0, 0, 1]   # thumb + index + pinky
GESTURE_OCR_TRIGGER    = [1, 0, 0, 1, 1]   # thumb + ring + pinky

GESTURE_HOLD_FRAMES = 18   # ~0.6 s at 30 fps

# Swipe detection (presentation controller)
SWIPE_THRESHOLD_PX   = 120   # min horizontal displacement to count as swipe
SWIPE_MIN_FRAMES     = 4     # min consecutive frames moving in same direction
SWIPE_COOLDOWN_FRAMES = 30   # frames between swipe actions

# ── Shape Detection ───────────────────────────────────────────────────────────
SHAPE_DETECT_ENABLED   = True
SHAPE_MIN_AREA         = 1500      # ignore tiny contours
SHAPE_CONFIDENCE_THRESH = 0.72     # minimum confidence to auto-correct shape
SHAPE_APPROX_EPSILON   = 0.04     # cv2.approxPolyDP epsilon factor

# ── OCR ───────────────────────────────────────────────────────────────────────
OCR_ENABLED    = True
OCR_LANGUAGES  = ["en"]
OCR_MIN_CONF   = 0.4

# ── Session Recording ─────────────────────────────────────────────────────────
RECORDING_FPS    = 20
RECORDING_FOURCC = "mp4v"

# ── Auto-save ─────────────────────────────────────────────────────────────────
AUTOSAVE_INTERVAL_SEC = 60

# ── Paths ─────────────────────────────────────────────────────────────────────
SAVE_DIR       = os.path.join(_BASE, "assets", "screenshots")
EXPORT_DIR     = os.path.join(_BASE, "assets", "exports")
RECORDING_DIR  = os.path.join(_BASE, "assets", "recordings")
BRANDING_DIR   = os.path.join(_BASE, "assets", "branding")

for _d in (SAVE_DIR, EXPORT_DIR, RECORDING_DIR, BRANDING_DIR):
    os.makedirs(_d, exist_ok=True)
