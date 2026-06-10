# VisionBoard AI — Gesture Controlled Drawing System

> **Transform Gestures into Ideas.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-5C3EE8?logo=opencv)](https://opencv.org)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10+-FF6F00)](https://mediapipe.dev)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?logo=streamlit)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-22D3EE)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.1.0-10B981)]()
[![Live Demo](https://img.shields.io/badge/Live_Demo-Streamlit_Cloud-FF4B4B?logo=streamlit)](https://your-username-visionboardai.streamlit.app)

VisionBoard AI is an **AI-powered, fully touchless gesture-controlled smart whiteboard** available as both a desktop application and a live web app. Draw, annotate, and interact with a digital canvas using only your hand — no mouse, no stylus, no touch screen required.

---

## 🌐 Live Web Demo

> **[https://your-username-visionboardai.streamlit.app](https://your-username-visionboardai.streamlit.app)**

- Open in any browser — no installation needed
- Allow camera access when prompted
- Show your hand and start drawing

---

## Feature Overview

| Category | Features |
|---|---|
| **Drawing** | Pencil · Marker · Highlighter · Calligraphy · Eraser |
| **Colors** | 6-color palette with gesture selection |
| **Canvas** | Undo/Redo (30 steps) · Clear · Multi-layer composite |
| **Gestures** | Draw · Select · Undo · Clear · Save · Thickness · OCR |
| **Toolbar** | Fully touchless — hover to select any tool/color/action |
| **Shape AI** | Auto-detect & correct Circle · Rectangle · Square · Triangle · Line |
| **Export** | PNG download · Timestamped PDF with branded header |
| **OCR** | Handwriting → digital text via EasyOCR |
| **Recording** | Full session MP4 recording *(desktop only)* |
| **Presentation** | Swipe gesture slide control *(desktop only)* |
| **Performance** | EMA smoothing · dwell-time debouncing · 30-frame FPS |
| **UI** | Dark futuristic HUD · animated selection ring · progress indicator |

---

## Architecture

```
VisionBoardAI/
│
├── main.py                          # Desktop orchestration loop
├── app.py                           # Streamlit web application
├── config.py                        # All constants & paths (shared)
├── requirements.txt                 # Desktop dependencies
├── requirements_web.txt             # Web dependencies
├── packages.txt                     # Streamlit Cloud apt packages
│
├── core/                            # Shared by both versions (unmodified)
│   ├── hand_tracker.py              # MediaPipe + EMA landmark smoothing
│   ├── canvas.py                    # Drawing layer + undo/redo stack
│   ├── gesture_controller.py        # Debounced finger-pattern → action mapper
│   ├── file_manager.py              # PNG/JPG export & auto-save
│   ├── shape_detector.py            # Contour analysis → perfect shape correction
│   ├── pdf_exporter.py              # reportlab branded PDF export
│   ├── session_recorder.py          # cv2.VideoWriter MP4 session recording
│   ├── ocr_engine.py                # EasyOCR handwriting recognition
│   └── presentation_controller.py  # Swipe gesture → slide navigation
│
├── ui/                              # Desktop UI (unmodified)
│   ├── toolbar.py
│   ├── notifications.py
│   └── splash_screen.py
│
├── web/                             # Web-only layer
│   ├── web_state.py                 # Thread-safe session state
│   ├── gesture_toolbar.py           # Touchless in-video toolbar (NEW)
│   └── pdf_bytes.py                 # In-memory PDF for browser download
│
├── utils/                           # Shared utilities
│   ├── drawing_utils.py             # 5 brush style renderers
│   ├── performance_utils.py         # FPS counter, frame throttler
│   └── helper_functions.py
│
└── assets/
    ├── screenshots/
    ├── exports/
    ├── recordings/
    └── branding/
        ├── logo_concept.md
        └── branding_guide.md
```

---

## Installation

### Desktop Version
```bash
git clone https://github.com/<your-username>/VisionBoardAI.git
cd VisionBoardAI

python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
python main.py
```

### Web Version (local)
```bash
pip install -r requirements_web.txt
streamlit run app.py
# Opens at http://localhost:8501
```

---

## Gesture Reference

### Drawing Gestures
| Gesture | Action |
|---|---|
| ☝ Index finger only | **Draw** |
| ✌ Index + Middle | **Selection mode — aim at toolbar** |

### Touchless Toolbar (web + desktop)
In Selection mode, hover the fingertip over any toolbar button.
A circular progress ring fills over **~1 second**. When complete, the action fires.

### Hold Gestures *(~0.6 s)*
| Gesture | Action |
|---|---|
| 🖐 All 5 fingers | Clear canvas |
| 4 fingers + thumb | Undo |
| 🤙 Thumb + Pinky | Save PNG |
| Index + Middle + Ring | Brush size up |
| Middle + Ring + Pinky | Brush size down |
| Thumb + Ring + Pinky | Run OCR |

### Desktop-only Presentation Mode *(press `F`)*
| Gesture | Action |
|---|---|
| 🖐 Open palm | Start presentation |
| ✊ Closed fist | End presentation |
| Swipe right | Next slide |
| Swipe left | Previous slide |

---

## Keyboard Shortcuts *(desktop only)*

| Key | Action |
|---|---|
| `Z` | Undo |
| `Y` | Redo |
| `S` | Save PNG |
| `P` | Export PDF |
| `R` | Toggle recording |
| `O` | Run OCR |
| `C` | Clear |
| `F` | Presentation mode |
| `ESC` / `Q` | Quit |

---

## Configuration

All tunable parameters in `config.py`:

```python
SMOOTH_FACTOR           = 0.35   # EMA jitter reduction (0=raw, 1=frozen)
GESTURE_HOLD_FRAMES     = 18     # frames to hold gesture before firing
AUTOSAVE_INTERVAL_SEC   = 60     # desktop auto-save interval
MAX_UNDO_STEPS          = 30     # undo stack depth
SHAPE_CONFIDENCE_THRESH = 0.72   # shape auto-correction threshold
RECORDING_FPS           = 20     # MP4 output frame rate
```

Web toolbar dwell time is tunable in `web/gesture_toolbar.py`:
```python
HOVER_HOLD_FRAMES = 30   # ~1 s at 30 fps
```

---

## Tech Stack

| Library | Role |
|---|---|
| **Python 3.10+** | Core language |
| **OpenCV 4.8+** | Camera capture, drawing, HUD rendering |
| **MediaPipe 0.10+** | Real-time hand landmark detection (21 points) |
| **NumPy** | Canvas layer operations |
| **Streamlit 1.35+** | Web application framework |
| **streamlit-webrtc** | Real-time webcam stream in browser |
| **reportlab** | PDF generation with branded layout |
| **EasyOCR** | Deep-learning handwriting recognition |
| **pyautogui** | Keyboard simulation for slide control |

---

## Screenshots

> *Add screenshots to `assets/screenshots/` and update the paths below.*

| Feature | Screenshot |
|---|---|
| Desktop App | `assets/screenshots/desktop_app.png` |
| Web Version | `assets/screenshots/web_app.png` |
| Shape Detection | `assets/screenshots/shape_detection.png` |
| OCR Result | `assets/screenshots/ocr_result.png` |
| Gesture Toolbar | `assets/screenshots/gesture_toolbar.png` |

---

## Resume Content

### 2-Line Description
> Built **VisionBoard AI**, a production-quality gesture-controlled drawing system deployed as both a desktop application and a live web app — featuring real-time hand tracking, touchless toolbar interaction, AI shape correction, OCR, and PDF export across a fully modular Python architecture.

### Resume Bullet Points
- Engineered a real-time computer vision pipeline achieving stable 30 FPS hand landmark detection with exponential moving average jitter reduction, deployed on both a PyInstaller Windows executable and Streamlit Cloud
- Designed a fully touchless gesture toolbar rendered directly onto the video feed: dwell-time hover detection fires actions after ~1 s, enabling complete mouse-free control in the browser
- Implemented AI-powered shape detection using OpenCV contour analysis and approxPolyDP, auto-correcting freehand circles, rectangles, triangles, and lines with configurable confidence thresholds
- Built a thread-safe web architecture separating the streamlit-webrtc background thread from the Streamlit script thread via a locked state container, preventing race conditions in shared canvas and gesture state
- Integrated EasyOCR handwriting recognition, reportlab in-memory PDF export, and pyautogui presentation control — all with graceful fallback when optional dependencies are absent

### ATS Keywords
Python · OpenCV · MediaPipe · NumPy · Streamlit · streamlit-webrtc · WebRTC ·
Computer Vision · Hand Gesture Recognition · Real-Time Systems · Machine Learning ·
EasyOCR · OCR · reportlab · Modular Architecture · OOP · Image Processing · AI · Deep Learning ·
Threading · Concurrency · Cloud Deployment

---

## Future Enhancements

- [ ] Multi-hand collaborative drawing
- [ ] Virtual keyboard via fingertip spelling
- [ ] AWS S3 / Google Drive canvas sync
- [ ] Whiteboard replay / animation playback
- [ ] Custom gesture trainer (user-defined mappings)
- [ ] Voice command integration
- [ ] Real-time collaboration via WebSockets

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m "feat: add my feature"`
4. Push and open a Pull Request

---

## License

MIT © 2024 — See [LICENSE](LICENSE) for details.
