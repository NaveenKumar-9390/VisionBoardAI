"""
VisionBoard AI – Streamlit Web Application  v2.1
Transform Gestures into Ideas.

Fully touchless — all toolbar actions accessible via hand gestures.
Sidebar controls remain as an optional fallback.

Gesture interaction model:
  ☝  Index only          → Draw on canvas
  ✌  Index + Middle      → Selection mode
     └─ Hover fingertip over any toolbar button for ~1 s → fires action
  Hold gestures (debounced via GestureController):
     All 5 fingers        → Clear canvas
     4 fingers + thumb    → Undo
     Thumb + Pinky        → Save PNG download
     Index+Middle+Ring    → Brush size up
     Middle+Ring+Pinky    → Brush size down
"""
import io
import time
import logging

import av
import cv2
import numpy as np
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration

from config import (
    CAM_WIDTH, CAM_HEIGHT,
    COLOR_PALETTE, TOOLS,
    DEFAULT_BRUSH, DEFAULT_THICKNESS, MIN_THICKNESS, MAX_THICKNESS, THICKNESS_STEP,
    ERASER_THICKNESS, SHAPE_DETECT_ENABLED,
    GESTURE_OCR_TRIGGER,
)
from web.web_state import WebState
from web.pdf_bytes import export_pdf_bytes
from utils.drawing_utils import draw_stroke
from core.canvas import cv_add

logging.basicConfig(level=logging.WARNING)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VisionBoard AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Brand CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background:#0F172A; }
  [data-testid="stSidebar"]          { background:#1E293B; }
  [data-testid="stSidebar"] *        { color:#E2E8F0 !important; }
  h1,h2,h3                           { color:#06B6D4 !important; }
  .stButton>button {
      background:#1E293B; color:#E2E8F0;
      border:1px solid #475569; border-radius:6px;
  }
  .stButton>button:hover { border-color:#06B6D4; color:#06B6D4; }
  .notif {
      background:#0E2233; border-left:3px solid #06B6D4;
      padding:7px 14px; border-radius:5px;
      color:#E2E8F0; font-size:0.84rem; margin:4px 0;
  }
  .stat-card {
      background:#1E293B; border:1px solid #334155;
      border-radius:8px; padding:12px 16px; margin:4px 0;
  }
</style>
""", unsafe_allow_html=True)

# ── Session state bootstrap ───────────────────────────────────────────────────
if "vb_state" not in st.session_state:
    st.session_state.vb_state = WebState()
if "ocr_reader" not in st.session_state:
    st.session_state.ocr_reader = None
if "ocr_result" not in st.session_state:
    st.session_state.ocr_result = ""
if "png_ready" not in st.session_state:
    st.session_state.png_ready = None   # bytes of last saved PNG

state: WebState = st.session_state.vb_state

# ── WebRTC config ─────────────────────────────────────────────────────────────
_RTC_CONFIG = RTCConfiguration(
    iceServers=[
        {"urls": ["stun:stun.l.google.com:19302"]},
        {"urls": ["stun:stun1.l.google.com:19302"]},
    ]
)

# ── Video frame callback ──────────────────────────────────────────────────────
# Runs in a background daemon thread — every frame of the webcam stream.

def _video_callback(frame: av.VideoFrame) -> av.VideoFrame:
    img = frame.to_ndarray(format="bgr24")
    img = cv2.flip(img, 1)
    if img.shape[1] != CAM_WIDTH or img.shape[0] != CAM_HEIGHT:
        img = cv2.resize(img, (CAM_WIDTH, CAM_HEIGHT))

    # ── Hand tracking ─────────────────────────────────────────────────────────
    img     = state.tracker.process(img, draw=True)
    lm_list = state.tracker.get_landmarks(img)
    fingers = state.tracker.fingers_up(lm_list) if lm_list else []

    # ── Debounced hold-gestures ───────────────────────────────────────────────
    gesture, activated = state.gestures.update(fingers)

    with state._lock:
        state.gesture_label = gesture

        if activated:
            if gesture == "undo":
                state.canvas.undo()
                state.notification = "↩  Gesture: Undo"
            elif gesture == "clear":
                state.canvas.clear()
                state.notification = "✕  Gesture: Clear"
            elif gesture == "save":
                # Store PNG bytes so sidebar can offer download on next rerun
                _, buf = cv2.imencode(".png", state.canvas.layer)
                st.session_state.png_ready = buf.tobytes()
                state.notification = "💾  Gesture: PNG ready — download in sidebar"
            elif gesture == "thickness_up":
                state.thickness = min(state.thickness + THICKNESS_STEP, MAX_THICKNESS)
                state.notification = f"📏  Size: {state.thickness}"
            elif gesture == "thickness_down":
                state.thickness = max(state.thickness - THICKNESS_STEP, MIN_THICKNESS)
                state.notification = f"📏  Size: {state.thickness}"

        # OCR gesture trigger
        if activated and fingers == GESTURE_OCR_TRIGGER:
            state.ocr_requested = True
            state.notification  = "🔤  OCR triggered…"

    # ── Fingertip coordinates ─────────────────────────────────────────────────
    ix, iy = (lm_list[8][1], lm_list[8][2]) if lm_list else (0, 0)

    # ── Gesture toolbar (runs in video thread, fully self-contained) ──────────
    if lm_list:
        action = state.toolbar.process(img, ix, iy, gesture, state)
        if action:
            _apply_toolbar_action(action, state)
    else:
        # No hand — reset toolbar hover state
        state.toolbar.hover_target = None
        state.toolbar.hover_frames = 0
        # Draw toolbar without interaction
        state.toolbar._draw_toolbar(img, state)

    # ── Drawing ───────────────────────────────────────────────────────────────
    if lm_list:
        # Cursor dot
        cv2.circle(img, (ix, iy), 9, state.color, cv2.FILLED)
        cv2.circle(img, (ix, iy), 11, (255, 255, 255), 1)

        in_toolbar_zone = iy < state.toolbar._rects.get(
            "thickness_preview", (0, 0, 0, 100)
        )[3] + 6   # anything above toolbar bottom

        if gesture == "draw" and not (iy < (state.toolbar._rects.get(
                "undo", (0, 0, 0, 96))[3] + 4)):
            with state._lock:
                if not state.in_stroke:
                    state.canvas.begin_stroke()
                    state.in_stroke    = True
                    state.shape_result = None
                thickness = ERASER_THICKNESS if state.tool == "eraser" else state.thickness
                if state.prev_pt is not None:
                    draw_stroke(state.canvas.layer, state.prev_pt, (ix, iy),
                                state.color, thickness, state.tool)
                state.prev_pt = (ix, iy)
        else:
            with state._lock:
                if state.in_stroke:
                    state.in_stroke = False
                    if SHAPE_DETECT_ENABLED and state.tool != "eraser":
                        name, conf = state.shapes.detect_and_correct(
                            state.canvas.layer, state.color, state.thickness)
                        state.shape_result = (name, conf) if name else None
                state.prev_pt = None
    else:
        with state._lock:
            if state.in_stroke:
                state.in_stroke = False
                if SHAPE_DETECT_ENABLED and state.tool != "eraser":
                    name, conf = state.shapes.detect_and_correct(
                        state.canvas.layer, state.color, state.thickness)
                    state.shape_result = (name, conf) if name else None
            state.prev_pt = None

    # ── Compose output ────────────────────────────────────────────────────────
    with state._lock:
        output = cv_add(img, state.canvas.layer)
        _draw_canvas_hud(output, state)

    state.set_last_frame(output)
    return av.VideoFrame.from_ndarray(output, format="bgr24")


def _apply_toolbar_action(action: str, state: WebState):
    """Translate a toolbar button key into a state mutation."""
    if action.startswith("color_"):
        idx = int(action.split("_")[1])
        name, bgr = COLOR_PALETTE[idx]
        state.set_color(bgr, name)

    elif action.startswith("tool_"):
        tool = action.split("_")[1]
        state.set_tool(tool)

    elif action == "thickness_up":
        state.bump_thickness(+1)

    elif action == "thickness_down":
        state.bump_thickness(-1)

    elif action == "undo":
        state.undo()

    elif action == "redo":
        state.redo()

    elif action == "clear":
        state.clear()

    elif action == "save":
        with state._lock:
            _, buf = cv2.imencode(".png", state.canvas.layer)
            st.session_state.png_ready = buf.tobytes()
        state.notification = "💾  PNG ready — download in sidebar"

    elif action == "ocr":
        state.request_ocr()


def _draw_canvas_hud(frame: np.ndarray, state: WebState):
    """Overlay status info below the toolbar onto the composite frame."""
    h = frame.shape[0]

    # Shape detection result — bottom-left
    if state.shape_result:
        name, conf = state.shape_result
        cv2.putText(frame, f"Shape: {name.capitalize()}  {conf*100:.0f}%",
                    (12, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.52,
                    (212, 182, 6), 1, cv2.LINE_AA)

    # Notification — bottom-right
    if state.notification:
        (tw, _), _ = cv2.getTextSize(
            state.notification, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
        cv2.putText(frame, state.notification,
                    (CAM_WIDTH - tw - 12, h - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (238, 211, 34), 1, cv2.LINE_AA)


# ── OCR runner (called from main Streamlit thread) ────────────────────────────

def _run_ocr():
    canvas_snap = state.get_canvas_snapshot()
    try:
        import easyocr
        if st.session_state.ocr_reader is None:
            with st.spinner("Loading OCR model (first run ~30 s)…"):
                from config import OCR_LANGUAGES
                st.session_state.ocr_reader = easyocr.Reader(
                    OCR_LANGUAGES, gpu=False, verbose=False)
        reader   = st.session_state.ocr_reader
        gray     = cv2.cvtColor(canvas_snap, cv2.COLOR_BGR2GRAY)
        inverted = cv2.bitwise_not(gray)
        from config import OCR_MIN_CONF
        results  = reader.readtext(inverted)
        lines    = [t for (_, t, c) in results if c >= OCR_MIN_CONF]
        st.session_state.ocr_result = " ".join(lines).strip() or "(no text detected)"
        state.notification = "🔤  OCR complete"
    except ImportError:
        st.session_state.ocr_result = "easyocr not installed"


# ── Sidebar ───────────────────────────────────────────────────────────────────

def _sidebar():
    with st.sidebar:
        st.markdown("# ✦ VisionBoard AI")
        st.caption("Transform Gestures into Ideas.")

        # Live gesture status badge
        with state._lock:
            gl = state.gesture_label
            sr = state.shape_result
            notif = state.notification
        _mode_colors = {
            "draw":   ("#10B981", "DRAW"),
            "select": ("#06B6D4", "SELECT"),
        }
        mc, ml = _mode_colors.get(gl, ("#64748B", gl.upper() if gl else "IDLE"))
        st.markdown(
            f'<div class="stat-card">'
            f'<span style="color:{mc};font-weight:700">{ml}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if notif:
            st.markdown(f'<div class="notif">{notif}</div>',
                        unsafe_allow_html=True)

        st.divider()

        # ── Color palette ─────────────────────────────────────────────────────
        st.markdown("### 🎨 Color")
        cols = st.columns(3)
        for i, (name, bgr) in enumerate(COLOR_PALETTE):
            r, g, b = bgr[2], bgr[1], bgr[0]
            if cols[i % 3].button(
                name, key=f"col_{i}", use_container_width=True,
                help=f"#{r:02x}{g:02x}{b:02x}"
            ):
                state.set_color(bgr, name)
                st.rerun()

        st.divider()

        # ── Tool selection ────────────────────────────────────────────────────
        st.markdown("### 🖌️ Tool")
        with state._lock:
            cur_tool = state.tool
        try:
            idx = next(i for i, t in enumerate(TOOLS) if t.lower() == cur_tool)
        except StopIteration:
            idx = 1
        choice = st.radio("tool", TOOLS, index=idx,
                          label_visibility="collapsed", key="tool_radio")
        if choice.lower() != cur_tool:
            state.set_tool(choice.lower())
            st.rerun()

        st.divider()

        # ── Brush size ────────────────────────────────────────────────────────
        st.markdown("### 📏 Brush Size")
        with state._lock:
            cur_sz = state.thickness
        new_sz = st.slider("sz", MIN_THICKNESS, MAX_THICKNESS,
                           cur_sz, THICKNESS_STEP,
                           label_visibility="collapsed", key="sz_slider")
        if new_sz != cur_sz:
            state.set_thickness(new_sz)

        st.divider()

        # ── Canvas actions ────────────────────────────────────────────────────
        st.markdown("### ⚡ Actions")
        c1, c2 = st.columns(2)
        if c1.button("↩ Undo",  key="btn_undo",  use_container_width=True):
            state.undo(); st.rerun()
        if c2.button("↪ Redo",  key="btn_redo",  use_container_width=True):
            state.redo(); st.rerun()
        if st.button("✕ Clear Canvas", key="btn_clear", use_container_width=True):
            state.clear(); st.rerun()

        st.divider()

        # ── Export ────────────────────────────────────────────────────────────
        st.markdown("### 💾 Export")
        snap = state.get_canvas_snapshot()
        _, png_buf = cv2.imencode(".png", snap)
        st.download_button(
            "⬇ Download PNG",
            data=png_buf.tobytes(),
            file_name=f"VisionBoardAI_{time.strftime('%Y%m%d_%H%M%S')}.png",
            mime="image/png",
            use_container_width=True,
            key="dl_png",
        )
        # Gesture-triggered save
        if st.session_state.png_ready:
            st.download_button(
                "⬇ Gesture Save (ready!)",
                data=st.session_state.png_ready,
                file_name=f"VisionBoardAI_gesture_{time.strftime('%Y%m%d_%H%M%S')}.png",
                mime="image/png",
                use_container_width=True,
                key="dl_gesture_png",
            )

        pdf_b = export_pdf_bytes(snap)
        if pdf_b:
            st.download_button(
                "⬇ Download PDF",
                data=pdf_b,
                file_name=f"VisionBoardAI_{time.strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="dl_pdf",
            )
        else:
            st.caption("PDF — install reportlab")

        st.divider()

        # ── OCR ───────────────────────────────────────────────────────────────
        st.markdown("### 🔤 OCR")

        # Check for gesture-triggered OCR request
        if state.consume_ocr_request():
            _run_ocr()
            st.rerun()

        if st.button("Run OCR", key="btn_ocr", use_container_width=True):
            _run_ocr()

        if st.session_state.ocr_result:
            st.text_area("Result", st.session_state.ocr_result,
                         height=72, key="ocr_out")

        st.divider()

        # ── Gesture guide ─────────────────────────────────────────────────────
        with st.expander("✋ Gesture Guide"):
            st.markdown("""
**Toolbar** *(Selection mode + hover 1 s)*
Point with Index + Middle, aim at any button

**Hold gestures** *(~0.6 s)*
| Gesture | Action |
|---|---|
| 🖐 All 5 fingers | Clear |
| 4 fingers + thumb | Undo |
| 🤙 Thumb + Pinky | Save |
| Index+Middle+Ring | Size ↑ |
| Middle+Ring+Pinky | Size ↓ |
| Thumb+Ring+Pinky | OCR |
""")

        # ── Active settings summary ───────────────────────────────────────────
        with state._lock:
            t, c, sz = state.tool, state.color, state.thickness
        r, g, b = c[2], c[1], c[0]
        st.markdown(
            f'<div class="stat-card" style="font-size:0.78rem">'
            f'Tool: <b>{t}</b> &nbsp;|&nbsp; '
            f'Size: <b>{sz}</b> &nbsp;|&nbsp; '
            f'Color: <span style="color:#{r:02x}{g:02x}{b:02x}">■</span>'
            f' <code>#{r:02x}{g:02x}{b:02x}</code>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── Main layout ───────────────────────────────────────────────────────────────

def main():
    _sidebar()

    st.markdown(
        "<h1 style='margin-bottom:2px'>✦ VisionBoard AI</h1>"
        "<p style='color:#64748B;margin:0 0 12px 0'>"
        "Transform Gestures into Ideas. &nbsp;·&nbsp; "
        "<a href='https://github.com/your-username/VisionBoardAI' "
        "style='color:#06B6D4'>GitHub</a></p>",
        unsafe_allow_html=True,
    )

    # Shape result banner
    with state._lock:
        sr = state.shape_result
    if sr:
        name, conf = sr
        st.info(f"🔷 Shape: **{name.capitalize()}** — {conf*100:.0f}% confidence")

    # WebRTC streamer
    ctx = webrtc_streamer(
        key="visionboard",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=_RTC_CONFIG,
        video_frame_callback=_video_callback,
        media_stream_constraints={
            "video": {
                "width":     {"ideal": CAM_WIDTH},
                "height":    {"ideal": CAM_HEIGHT},
                "frameRate": {"ideal": 30},
            },
            "audio": False,
        },
        async_processing=True,
    )

    if not ctx.state.playing:
        st.markdown("""
        <div style="background:#1E293B;border:1px dashed #475569;
                    border-radius:10px;padding:36px;text-align:center;">
            <h3 style="color:#06B6D4;margin:0 0 8px">📷 Click START to begin</h3>
            <p style="color:#64748B;margin:0">
            Allow camera access when prompted.<br>
            Show your hand — the toolbar appears at the top of the video.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Canvas snapshot + info
    st.markdown("---")
    col_canvas, col_info = st.columns([3, 1])

    with col_canvas:
        st.markdown("**Canvas snapshot** *(static — updates after each stroke)*")
        snap = state.get_canvas_snapshot()
        if snap.any():
            st.image(cv2.cvtColor(snap, cv2.COLOR_BGR2RGB),
                     use_container_width=True)
        else:
            st.caption("Canvas empty — start drawing!")

    with col_info:
        st.markdown("**How to use**")
        st.markdown("""
1. Click **START**
2. Allow camera access
3. ☝ **Index finger** → Draw
4. ✌ **Index + Middle** → Hover toolbar
5. Hold hover **~1 s** → Action fires
6. Download PNG/PDF from sidebar
        """)
        if st.session_state.ocr_result:
            st.markdown("**OCR Result**")
            st.code(st.session_state.ocr_result)


if __name__ == "__main__":
    main()
