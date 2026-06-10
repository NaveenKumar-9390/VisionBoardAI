# VisionBoard AI – PyInstaller Spec File
# -----------------------------------------------------------------------
# Build command:  pyinstaller VisionBoardAI.spec
# -----------------------------------------------------------------------
# This spec file bundles the entire VisionBoard AI application into a
# single-folder distribution containing VisionBoardAI.exe.
#
# Strategy: onedir (not onefile) — faster startup, easier to update assets.
# -----------------------------------------------------------------------

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None

# ── Resolve project root ──────────────────────────────────────────────────────
ROOT = os.path.abspath(os.path.dirname(SPEC))   # noqa: F821 (SPEC is injected by PyInstaller)

# ── Data files to bundle ──────────────────────────────────────────────────────
# Tuple format: (source_path, dest_folder_inside_bundle)
added_datas = [
    # Project asset folders — keep directory structure intact
    (os.path.join(ROOT, 'assets', 'branding'),    'assets/branding'),
    (os.path.join(ROOT, 'assets', 'screenshots'), 'assets/screenshots'),
    (os.path.join(ROOT, 'assets', 'exports'),     'assets/exports'),
    (os.path.join(ROOT, 'assets', 'recordings'),  'assets/recordings'),
]

# MediaPipe data files (model weights, etc.)
try:
    added_datas += collect_data_files('mediapipe')
except Exception:
    pass

# EasyOCR data files
try:
    added_datas += collect_data_files('easyocr')
except Exception:
    pass

# reportlab fonts & data
try:
    added_datas += collect_data_files('reportlab')
except Exception:
    pass

# matplotlib data files (required by mediapipe drawing internals)
try:
    added_datas += collect_data_files('matplotlib')
except Exception:
    pass

# ── Binaries (native .dll / .so) ──────────────────────────────────────────────
added_binaries = []
try:
    added_binaries += collect_dynamic_libs('cv2')
except Exception:
    pass
try:
    added_binaries += collect_dynamic_libs('mediapipe')
except Exception:
    pass

# ── Hidden imports ────────────────────────────────────────────────────────────
# PyInstaller cannot auto-detect dynamic imports, lazy loaders, or
# packages that use importlib internally. List them all explicitly.
hidden_imports = [

    # ── OpenCV ────────────────────────────────────────────────────────────────
    'cv2',

    # ── MediaPipe ─────────────────────────────────────────────────────────────
    'mediapipe',
    'mediapipe.python',
    'mediapipe.python.solutions',
    'mediapipe.python.solutions.hands',
    'mediapipe.python.solutions.drawing_utils',
    'mediapipe.python.solutions.drawing_styles',
    'mediapipe.tasks',
    'mediapipe.tasks.python',
    'mediapipe.tasks.python.vision',

    # ── NumPy ─────────────────────────────────────────────────────────────────
    'numpy',
    'numpy.core._multiarray_umath',
    'numpy.core._multiarray_tests',

    # ── matplotlib (required by mediapipe drawing internals) ──────────────────
    'matplotlib',
    'matplotlib.pyplot',
    'matplotlib.backends',
    'matplotlib.backends.backend_agg',
    'matplotlib.figure',
    'matplotlib.patches',
    'matplotlib.colors',
    'matplotlib.cm',
    'matplotlib.font_manager',
    'matplotlib._cm',
    'matplotlib._cm_listed',

    # ── EasyOCR ───────────────────────────────────────────────────────────────
    'easyocr',
    'easyocr.easyocr',
    'easyocr.utils',
    'easyocr.config',
    'easyocr.detection',
    'easyocr.recognition',
    'easyocr.model.vgg_model',
    'easyocr.model.modules',

    # ── PyTorch (required by EasyOCR) ─────────────────────────────────────────
    'torch',
    'torch.nn',
    'torch.nn.functional',
    'torch.utils',
    'torch.utils.data',
    'torchvision',
    'torchvision.transforms',

    # ── reportlab ────────────────────────────────────────────────────────────
    'reportlab',
    'reportlab.pdfgen',
    'reportlab.pdfgen.canvas',
    'reportlab.lib',
    'reportlab.lib.pagesizes',
    'reportlab.lib.units',
    'reportlab.lib.colors',
    'reportlab.lib.utils',
    'reportlab.platypus',
    'reportlab.graphics',
    'reportlab.rl_config',
    'reportlab.pdfbase',
    'reportlab.pdfbase.pdfmetrics',
    'reportlab.pdfbase._fontdata',
    'reportlab.pdfbase.ttfonts',

    # ── pyautogui ────────────────────────────────────────────────────────────
    'pyautogui',
    'pyscreeze',
    'pymsgbox',
    'pygetwindow',
    'mouseinfo',

    # ── PIL / Pillow (pyautogui dependency) ───────────────────────────────────
    'PIL',
    'PIL.Image',
    'PIL.ImageGrab',

    # ── Standard library hidden imports ───────────────────────────────────────
    'logging.handlers',
    'email',
    'email.mime',
    'email.mime.text',
    'collections.abc',
    'importlib.metadata',
    'importlib.resources',
    'pkg_resources',
    'pkg_resources.extern',

    # ── Platform-specific (Windows UI automation for pyautogui) ───────────────
    'win32api',
    'win32con',
    'win32gui',
    'ctypes',
    'ctypes.wintypes',
]

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    ['main.py'],                        # entry point
    pathex=[ROOT],                      # project root on sys.path
    binaries=added_binaries,
    datas=added_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Only exclude packages that are genuinely unused AND have no
        # transitive dependency from mediapipe, easyocr, or torch.
        # matplotlib is REQUIRED by mediapipe internals — do NOT exclude it.
        'IPython',
        'jupyter',
        'notebook',
        'wx',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'gi',
        'gtk',
        'sphinx',
        'docutils',
        'xmlrunner',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ── PYZ archive ───────────────────────────────────────────────────────────────
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)   # noqa: F821

# ── EXE ───────────────────────────────────────────────────────────────────────
exe = EXE(                              # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,              # onedir mode — binaries in _MEIPASS
    name='VisionBoardAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                           # compress with UPX if available
    console=False,                      # no console window on launch
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Application metadata (Windows version resource)
    version='version_info.txt',         # generated by build.bat
)

# ── COLLECT (onedir bundle) ───────────────────────────────────────────────────
coll = COLLECT(                         # noqa: F821
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VisionBoardAI',               # output folder: dist/VisionBoardAI/
)
