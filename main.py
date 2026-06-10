"""
VisionBoard AI – Gesture Controlled Drawing System
Transform Gestures into Ideas.

Keyboard:  ESC/Q Quit | Z Undo | Y Redo | S Save PNG | P PDF
           C Clear | R Record toggle | O OCR | F Presentation mode
"""
import logging
import cv2

from config import (
    CAM_WIDTH, CAM_HEIGHT, TOOLBAR_H,
    COLOR_PALETTE, DEFAULT_COLOR, DEFAULT_BRUSH, DEFAULT_THICKNESS,
    ERASER_THICKNESS, MIN_THICKNESS, MAX_THICKNESS, THICKNESS_STEP,
    SHAPE_DETECT_ENABLED, WINDOW_TITLE,
    GESTURE_RECORD_TOGGLE, GESTURE_OCR_TRIGGER,
)
from core.hand_tracker          import HandTracker
from core.canvas                import Canvas, cv_add
from core.gesture_controller    import GestureController
from core.file_manager          import FileManager
from core.shape_detector        import ShapeDetector
from core.pdf_exporter          import PDFExporter
from core.session_recorder      import SessionRecorder
from core.ocr_engine            import OCREngine
from core.presentation_controller import PresentationController
from ui.toolbar                 import Toolbar
from ui.notifications           import NotificationManager, NotificationLevel
from ui.splash_screen           import show_splash
from utils.drawing_utils        import draw_stroke
from utils.performance_utils    import FPSCounter, FrameThrottler

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s: %(message)s")
log = logging.getLogger("visionboard")


# ── Application State ─────────────────────────────────────────────────────────

class AppState:
    __slots__ = (
        "color", "tool", "thickness",
        "prev_pt", "in_stroke",
        "shape_result", "ocr_text",
        "presentation_mode",
    )

    def __init__(self):
        self.color             = DEFAULT_COLOR
        self.tool              = DEFAULT_BRUSH
        self.thickness         = DEFAULT_THICKNESS
        self.prev_pt           = None
        self.in_stroke         = False
        self.shape_result      = None    # (name, conf) or None
        self.ocr_text          = ""
        self.presentation_mode = False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # ── Camera ────────────────────────────────────────────────────────────────
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)   # reduce latency

    ok, _ = cap.read()
    if not ok:
        log.error("Cannot open camera.")
        return

    # ── Module initialisation ─────────────────────────────────────────────────
    tracker       = HandTracker()
    canvas        = Canvas(CAM_WIDTH, CAM_HEIGHT)
    gestures      = GestureController()
    files         = FileManager()
    shapes        = ShapeDetector()
    pdf           = PDFExporter()
    recorder      = SessionRecorder()
    ocr           = OCREngine()
    presenter     = PresentationController()
    toolbar       = Toolbar()
    notifs        = NotificationManager()
    fps_counter   = FPSCounter()
    throttler     = FrameThrottler()
    state         = AppState()

    # ── Splash screen ─────────────────────────────────────────────────────────
    if not show_splash(WINDOW_TITLE):
        cap.release()
        return

    # ── Main loop ─────────────────────────────────────────────────────────────
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)

        fps = fps_counter.tick()

        # ── Hand detection ────────────────────────────────────────────────────
        frame   = tracker.process(frame, draw=True)
        lm_list = tracker.get_landmarks(frame)
        fingers = tracker.fingers_up(lm_list) if lm_list else []

        # ── Gesture classification ────────────────────────────────────────────
        gesture, activated = gestures.update(fingers)
        _handle_gesture_actions(gesture, activated, fingers, state, canvas,
                                 files, recorder, ocr, notifs)

        # ── Presentation controller ───────────────────────────────────────────
        if state.presentation_mode and lm_list:
            pres_action = presenter.update(lm_list, fingers)
            if pres_action == "next":
                notifs.push("▶ Next Slide", NotificationLevel.INFO)
            elif pres_action == "prev":
                notifs.push("◀ Previous Slide", NotificationLevel.INFO)
            elif pres_action == "end":
                state.presentation_mode = False
                notifs.push("Presentation mode ended", NotificationLevel.WARNING)

        # ── Drawing & selection ───────────────────────────────────────────────
        if lm_list:
            ix, iy = lm_list[8][1], lm_list[8][2]

            # Cursor
            cv2.circle(frame, (ix, iy), 9, state.color, cv2.FILLED)
            cv2.circle(frame, (ix, iy), 11, (255, 255, 255), 1)

            if gesture == "select" and toolbar.in_toolbar(iy):
                _handle_toolbar_click(ix, iy, state, canvas, files, pdf,
                                      recorder, ocr, toolbar, notifs)
                _end_stroke(state, canvas, shapes, fps, throttler)

            elif gesture == "draw" and not toolbar.in_toolbar(iy):
                _handle_draw(ix, iy, state, canvas)

            else:
                _end_stroke(state, canvas, shapes, fps, throttler)
        else:
            _end_stroke(state, canvas, shapes, fps, throttler)

        # ── Auto-save ─────────────────────────────────────────────────────────
        files.tick_autosave(canvas.layer)

        # ── Compose output ────────────────────────────────────────────────────
        output = cv_add(frame, canvas.layer)
        toolbar.draw(
            output,
            active_color  = state.color,
            active_tool   = state.tool,
            thickness     = state.thickness,
            fps           = fps,
            is_recording  = recorder.is_recording,
            rec_elapsed   = recorder.elapsed,
            shape_result  = state.shape_result,
            ocr_text      = state.ocr_text,
        )
        notifs.draw(output)

        # ── Recording ─────────────────────────────────────────────────────────
        recorder.draw_indicator(output)
        recorder.write(output)

        cv2.imshow(WINDOW_TITLE, output)

        # ── Keyboard shortcuts ────────────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord('q')):
            break
        elif key == ord('z'):
            canvas.undo();  notifs.push("Undo", NotificationLevel.INFO)
        elif key == ord('y'):
            canvas.redo();  notifs.push("Redo", NotificationLevel.INFO)
        elif key == ord('s'):
            files.save_png(canvas.layer); notifs.push("Saved as PNG ✓", NotificationLevel.SUCCESS)
        elif key == ord('c'):
            canvas.clear(); notifs.push("Canvas cleared", NotificationLevel.WARNING)
        elif key == ord('p'):
            _do_pdf(pdf, canvas, notifs)
        elif key == ord('r'):
            _toggle_recording(recorder, notifs)
        elif key == ord('o'):
            _do_ocr(ocr, canvas, state, notifs)
        elif key == ord('f'):
            state.presentation_mode = not state.presentation_mode
            notifs.push(
                "Presentation mode ON — swipe to navigate" if state.presentation_mode
                else "Presentation mode OFF",
                NotificationLevel.INFO,
            )

    # ── Cleanup ───────────────────────────────────────────────────────────────
    if recorder.is_recording:
        recorder.stop()
    cap.release()
    cv2.destroyAllWindows()


# ── Action Handlers ───────────────────────────────────────────────────────────

def _handle_draw(ix: int, iy: int, state: AppState, canvas: Canvas):
    if not state.in_stroke:
        canvas.begin_stroke()
        state.in_stroke  = True
        state.shape_result = None   # clear previous shape badge

    thickness = ERASER_THICKNESS if state.tool == "eraser" else state.thickness
    if state.prev_pt is not None:
        draw_stroke(canvas.layer, state.prev_pt, (ix, iy),
                    state.color, thickness, state.tool)
    state.prev_pt = (ix, iy)


def _end_stroke(
    state: AppState, canvas: Canvas,
    shapes: ShapeDetector, fps: float, throttler: FrameThrottler,
):
    if state.in_stroke:
        state.in_stroke = False
        if SHAPE_DETECT_ENABLED and throttler.should_run_heavy(fps) and state.tool != "eraser":
            name, conf = shapes.detect_and_correct(canvas.layer, state.color, state.thickness)
            state.shape_result = (name, conf) if name else None
    state.prev_pt = None


def _handle_toolbar_click(ix, iy, state, canvas, files, pdf, recorder, ocr, toolbar, notifs):
    ci = toolbar.hit_color(ix, iy)
    if ci is not None:
        state.color = COLOR_PALETTE[ci][1]
        if state.tool == "eraser":
            state.tool = DEFAULT_BRUSH
        notifs.push(f"Color: {COLOR_PALETTE[ci][0]}", NotificationLevel.INFO)
        return

    tool = toolbar.hit_tool(ix, iy)
    if tool is not None:
        state.tool = tool
        notifs.push(f"Tool: {tool.capitalize()}", NotificationLevel.INFO)
        return

    action = toolbar.hit_action(ix, iy)
    if action == "undo":
        canvas.undo();     notifs.push("Undo", NotificationLevel.INFO)
    elif action == "redo":
        canvas.redo();     notifs.push("Redo", NotificationLevel.INFO)
    elif action == "clear":
        canvas.clear();    notifs.push("Canvas cleared", NotificationLevel.WARNING)
    elif action == "save":
        files.save_png(canvas.layer)
        notifs.push("Saved as PNG ✓", NotificationLevel.SUCCESS)
    elif action == "pdf":
        _do_pdf(pdf, canvas, notifs)
    elif action == "record":
        _toggle_recording(recorder, notifs)
    elif action == "ocr":
        _do_ocr(ocr, canvas, state, notifs)
    elif action == "thickness_up":
        state.thickness = min(state.thickness + THICKNESS_STEP, MAX_THICKNESS)
        notifs.push(f"Brush size: {state.thickness}", NotificationLevel.INFO)
    elif action == "thickness_down":
        state.thickness = max(state.thickness - THICKNESS_STEP, MIN_THICKNESS)
        notifs.push(f"Brush size: {state.thickness}", NotificationLevel.INFO)


def _handle_gesture_actions(gesture, activated, fingers,
                              state, canvas, files, recorder, ocr, notifs):
    if activated:
        if gesture == "undo":
            canvas.undo();    notifs.push("✦ Gesture: Undo", NotificationLevel.INFO)
        elif gesture == "clear":
            canvas.clear();   notifs.push("✦ Gesture: Clear", NotificationLevel.WARNING)
        elif gesture == "save":
            files.save_png(canvas.layer)
            notifs.push("✦ Gesture: Saved!", NotificationLevel.SUCCESS)
        elif gesture == "thickness_up":
            state.thickness = min(state.thickness + THICKNESS_STEP, MAX_THICKNESS)
            notifs.push(f"✦ Size: {state.thickness}", NotificationLevel.INFO)
        elif gesture == "thickness_down":
            state.thickness = max(state.thickness - THICKNESS_STEP, MIN_THICKNESS)
            notifs.push(f"✦ Size: {state.thickness}", NotificationLevel.INFO)

    # One-shot gestures checked directly from raw fingers (not debounced gesture name)
    if activated and fingers == GESTURE_RECORD_TOGGLE:
        _toggle_recording(recorder, notifs)
    elif activated and fingers == GESTURE_OCR_TRIGGER:
        _do_ocr(ocr, canvas, state, notifs)


def _do_pdf(pdf, canvas, notifs):
    path = pdf.export(canvas.layer)
    if path:
        notifs.push("PDF exported ✓", NotificationLevel.SUCCESS)
    else:
        notifs.push("PDF failed — install reportlab", NotificationLevel.WARNING)


def _toggle_recording(recorder, notifs):
    if recorder.is_recording:
        recorder.stop()
        notifs.push("Recording saved ✓", NotificationLevel.SUCCESS)
    else:
        recorder.start()
        notifs.push("Recording started ●", NotificationLevel.WARNING)


def _do_ocr(ocr, canvas, state, notifs):
    notifs.push("Running OCR…", NotificationLevel.INFO)
    text = ocr.run(canvas.layer)
    state.ocr_text = text
    if text:
        notifs.push(f"OCR: {text[:50]}", NotificationLevel.SUCCESS)
    else:
        notifs.push("OCR: no text detected", NotificationLevel.WARNING)


if __name__ == "__main__":
    main()
