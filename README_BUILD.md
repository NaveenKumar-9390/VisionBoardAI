# VisionBoard AI — Build & Packaging Guide

> Complete instructions for packaging VisionBoard AI into a standalone Windows executable.

---

## Prerequisites

| Tool | Version | Download |
|---|---|---|
| Python | 3.10+ | https://python.org |
| pip | latest | bundled with Python |
| PyInstaller | 6.x | `pip install pyinstaller` |
| Inno Setup *(optional)* | 6.x | https://jrsoftware.org/isinfo.php |
| UPX *(optional, smaller EXE)* | 4.x | https://upx.github.io |

### Install all project dependencies first
```bash
pip install -r requirements.txt
pip install pyinstaller
```

---

## Quick Build (Recommended)

### Option A — Batch script (double-click)
```
build.bat
```

### Option B — PowerShell
```powershell
pwsh -ExecutionPolicy Bypass -File build.ps1
```

Both scripts perform all 8 steps automatically:
1. Verify Python
2. Verify PyInstaller
3. Verify all dependencies
4. Clean previous build artefacts
5. Prepare asset directories
6. Run PyInstaller
7. Package the `release/` folder
8. Verify the EXE exists

---

## Manual Build Steps

If you prefer to run PyInstaller directly:

```bash
# Clean old builds
rmdir /s /q build dist

# Build
pyinstaller VisionBoardAI.spec --clean --noconfirm

# Output is at:
#   dist\VisionBoardAI\VisionBoardAI.exe
```

---

## Output Structure

After a successful build:

```
dist/
└── VisionBoardAI/              ← the complete application folder
    ├── VisionBoardAI.exe       ← main executable
    ├── _internal/              ← Python runtime + all libraries
    ├── assets/
    │   ├── screenshots/
    │   ├── exports/
    │   ├── recordings/
    │   └── branding/
    └── ...

release/
├── VisionBoardAI/              ← copy of dist/VisionBoardAI/
├── README.txt                  ← end-user instructions
├── README.md                   ← developer documentation
├── LICENSE
└── version.txt
```

---

## Creating the Installer (Inno Setup)

1. Build the EXE first using `build.bat`
2. Install Inno Setup 6 from https://jrsoftware.org/isinfo.php
3. Open `installer_script.iss` in the Inno Setup Compiler
4. Press `Ctrl+F9` to compile
5. Output: `release\installer\VisionBoardAI_Setup_v2.0.0.exe`

The installer will:
- Install to `%ProgramFiles%\VisionBoard AI`
- Create a Start Menu shortcut
- Offer an optional Desktop shortcut
- Include a full uninstaller

---

## PyInstaller Spec Notes

`VisionBoardAI.spec` handles these packaging challenges:

| Challenge | Solution |
|---|---|
| MediaPipe model files | `collect_data_files('mediapipe')` |
| EasyOCR model weights | `collect_data_files('easyocr')` |
| reportlab fonts | `collect_data_files('reportlab')` |
| matplotlib required by MediaPipe | Kept in build + added to `hiddenimports` + `collect_data_files('matplotlib')` |
| PyTorch (EasyOCR dep) | Listed in `hiddenimports` |
| pyautogui Windows APIs | `win32api`, `win32gui` in hidden imports |
| Asset directories | Explicit `datas` tuples in spec |
| EXE metadata | `version_info.txt` (Windows version resource) |

---

## Build Optimization

### Reduce executable size

1. Install UPX and add to PATH — PyInstaller will use it automatically (`upx=True` in spec)
2. The spec excludes only genuinely unused UI frameworks: `IPython`, `jupyter`, `Qt*`, `wx`, `gtk`. `matplotlib`, `scipy`, and `pandas` are intentionally kept — `matplotlib` is a transitive dependency of MediaPipe and must not be excluded.
3. Use a clean virtual environment to avoid bundling dev dependencies:
   ```bash
   python -m venv venv_build
   venv_build\Scripts\activate
   pip install -r requirements.txt pyinstaller
   pyinstaller VisionBoardAI.spec --clean --noconfirm
   ```

### Typical build sizes

| Component | Approx size |
|---|---|
| Python runtime | ~15 MB |
| OpenCV | ~40 MB |
| MediaPipe | ~50 MB |
| EasyOCR + PyTorch | ~500–800 MB |
| reportlab | ~5 MB |
| Total (with UPX) | ~600–900 MB |

> EasyOCR bundles PyTorch, which is large. This is expected and unavoidable.
> The OCR model (~100 MB) is downloaded on first run.

---

## Troubleshooting

### "Failed to execute script main"
The EXE launched but Python raised an exception at startup.
- Run from CMD to see the error: `dist\VisionBoardAI\VisionBoardAI.exe`
- Or temporarily set `console=True` in the spec to show the console window

### "Cannot open camera"
- Ensure a webcam is connected before launching
- Check Windows Camera Privacy settings (Settings → Privacy → Camera)
- Try changing `cv2.VideoCapture(0)` index to `1` if using an external webcam

### "ImportError: No module named X"
Add the missing module to `hiddenimports` in `VisionBoardAI.spec` and rebuild.

### MediaPipe model not found
MediaPipe downloads models at runtime. Ensure internet access on first launch,
or pre-download by running `python main.py` once before packaging.

### EasyOCR model download on first launch
EasyOCR downloads ~100 MB on first use. This is normal.
To pre-bundle the model, run `python main.py` and trigger OCR once (press `O`),
then rebuild — the downloaded model will be in `%USERPROFILE%\.EasyOCR\`.

### UPX not found warning
UPX is optional. If not installed, PyInstaller skips compression but still builds
a working executable. Install from https://upx.github.io and add to PATH.

### Antivirus false positive
PyInstaller executables are sometimes flagged by antivirus software.
This is a known false positive. Options:
- Whitelist the EXE in your antivirus
- Sign the EXE with a code-signing certificate (see below)

---

## Code Signing (Optional, Production)

To eliminate antivirus warnings for distribution:

```powershell
# Using signtool.exe (Windows SDK)
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /f certificate.pfx /p password dist\VisionBoardAI\VisionBoardAI.exe
```

For open-source projects, free signing options include:
- GitHub Actions with Azure Trusted Signing
- SignPath.io (free for open source)

---

## CI/CD Build (GitHub Actions)

Create `.github/workflows/build.yml`:

```yaml
name: Build Windows EXE

on:
  push:
    tags: ['v*']

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt pyinstaller
      - name: Build
        run: pyinstaller VisionBoardAI.spec --clean --noconfirm
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: VisionBoardAI-Windows
          path: dist/VisionBoardAI/
```

---

## Validation Checklist

Before releasing, verify each feature works in the built EXE:

- [ ] Splash screen displays on launch
- [ ] Webcam opens and shows live feed
- [ ] Hand tracking detects and tracks hand landmarks
- [ ] Draw mode (index finger) draws on canvas
- [ ] Selection mode (index + middle) interacts with toolbar
- [ ] All 6 color swatches work
- [ ] All 5 brush tools work (Pencil, Marker, Highlight, Calligraphy, Eraser)
- [ ] Brush size +/− buttons work
- [ ] Undo (Z) and Redo (Y) work
- [ ] Save PNG (S) creates file in `assets/screenshots/`
- [ ] PDF export (P) creates file in `assets/exports/`
- [ ] Session recording (R) creates MP4 in `assets/recordings/`
- [ ] OCR (O) processes canvas and displays result
- [ ] Shape detection auto-corrects drawn shapes
- [ ] Presentation mode (F) activates
- [ ] Gesture: Undo (4 fingers + thumb, hold)
- [ ] Gesture: Clear (all 5 fingers, hold)
- [ ] Gesture: Save (thumb + pinky, hold)
- [ ] Auto-save triggers after 60 seconds
- [ ] FPS counter displays in toolbar
- [ ] Notifications appear and fade
- [ ] ESC/Q quits cleanly

---

## Distribution

### Portable (no installer)
Zip the entire `release\VisionBoardAI\` folder and distribute.
Users extract and double-click `VisionBoardAI.exe`. No installation required.

### Installer
Run Inno Setup on `installer_script.iss` to produce:
`release\installer\VisionBoardAI_Setup_v2.0.0.exe`

Share this single file — it handles installation, shortcuts, and uninstall.

---

## File Reference

| File | Purpose |
|---|---|
| `VisionBoardAI.spec` | PyInstaller build configuration |
| `version_info.txt` | Windows EXE metadata (Properties → Details) |
| `build.bat` | One-click build (Batch) |
| `build.ps1` | One-click build (PowerShell) |
| `installer_script.iss` | Inno Setup installer definition |
| `release/README.txt` | End-user instructions |
| `release/version.txt` | Build metadata |
| `README_BUILD.md` | This document |
