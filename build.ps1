# ============================================================
# VisionBoard AI – PowerShell Build Script
# Usage: Right-click → Run with PowerShell
#        OR: pwsh -ExecutionPolicy Bypass -File build.ps1
# ============================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$APP_NAME    = "VisionBoard AI"
$APP_VERSION = "2.0.0"
$ROOT        = $PSScriptRoot

function Write-Header {
    Write-Host ""
    Write-Host " ==========================================================" -ForegroundColor Cyan
    Write-Host "  $APP_NAME  |  Build Script  |  v$APP_VERSION" -ForegroundColor Cyan
    Write-Host "  Transform Gestures into Ideas." -ForegroundColor DarkCyan
    Write-Host " ==========================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step([string]$step, [string]$msg) {
    Write-Host "[$step] $msg" -ForegroundColor Yellow
}

function Write-OK([string]$msg) {
    Write-Host "       $msg" -ForegroundColor Green
}

function Write-Fail([string]$msg) {
    Write-Host "[ERROR] $msg" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# ── Header ────────────────────────────────────────────────────
Write-Header
Set-Location $ROOT

# ── Step 1: Python ────────────────────────────────────────────
Write-Step "1/8" "Checking Python installation..."
try {
    $pyVer = python --version 2>&1
    Write-OK "Found: $pyVer"
} catch {
    Write-Fail "Python not found. Install Python 3.10+ and add it to PATH."
}

# ── Step 2: PyInstaller ───────────────────────────────────────
Write-Step "2/8" "Checking PyInstaller..."
$piVer = python -m PyInstaller --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-OK "PyInstaller missing. Installing..."
    pip install pyinstaller
    if ($LASTEXITCODE -ne 0) { Write-Fail "Failed to install PyInstaller." }
}
Write-OK "PyInstaller: $piVer"

# ── Step 3: Dependencies ──────────────────────────────────────
Write-Step "3/8" "Verifying project dependencies..."
python -c "import cv2, mediapipe, numpy, reportlab, easyocr, pyautogui" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-OK "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { Write-Fail "Dependency installation failed." }
}
Write-OK "All dependencies verified."

# ── Step 4: Clean ─────────────────────────────────────────────
Write-Step "4/8" "Cleaning previous build artefacts..."
foreach ($dir in @("build", "dist")) {
    if (Test-Path $dir) { Remove-Item $dir -Recurse -Force }
}
Write-OK "Clean complete."

# ── Step 5: Asset directories ─────────────────────────────────
Write-Step "5/8" "Preparing asset directories..."
foreach ($sub in @("screenshots","exports","recordings","branding")) {
    $p = Join-Path "assets" $sub
    if (-not (Test-Path $p)) { New-Item -ItemType Directory -Path $p | Out-Null }
}
Write-OK "Asset directories ready."

# ── Step 6: PyInstaller build ─────────────────────────────────
Write-Step "6/8" "Running PyInstaller (may take several minutes)..."
python -m PyInstaller VisionBoardAI.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) { Write-Fail "PyInstaller build failed. Review output above." }
Write-OK "Build complete: dist\VisionBoardAI\VisionBoardAI.exe"

# ── Step 7: Package release ───────────────────────────────────
Write-Step "7/8" "Packaging release folder..."
if (Test-Path "release") { Remove-Item "release" -Recurse -Force }
New-Item -ItemType Directory -Path "release" | Out-Null

# Copy dist output
Copy-Item -Path "dist\VisionBoardAI" -Destination "release\VisionBoardAI" -Recurse

# Copy docs
foreach ($f in @("LICENSE","README.md")) {
    if (Test-Path $f) { Copy-Item $f "release\" }
}

# version.txt
@"
VisionBoard AI
Version:    $APP_VERSION
Build date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Platform:   Windows x64
"@ | Set-Content "release\version.txt"

# README.txt (plain text)
@"
VisionBoard AI – Gesture Controlled Drawing System
==================================================
Transform Gestures into Ideas.

QUICK START
-----------
1. Connect your webcam.
2. Double-click VisionBoardAI\VisionBoardAI.exe to launch.
3. Show your hand to the camera and start drawing!

KEYBOARD SHORTCUTS
------------------
  Z        Undo
  Y        Redo
  S        Save PNG
  P        Export PDF
  R        Toggle Recording
  O        Run OCR
  C        Clear canvas
  F        Toggle Presentation mode
  ESC / Q  Quit

GESTURE CONTROLS
----------------
  Index finger only          Draw
  Index + Middle fingers     Select / Toolbar interaction
  All 5 fingers (hold)       Clear canvas
  4 fingers + thumb (hold)   Undo
  Thumb + Pinky (hold)       Save PNG
  Index+Middle+Ring (hold)   Increase brush size
  Middle+Ring+Pinky (hold)   Decrease brush size
  Thumb+Index+Pinky (hold)   Toggle recording
  Thumb+Ring+Pinky (hold)    Run OCR

SAVED FILES
-----------
  Screenshots: VisionBoardAI\assets\screenshots\
  PDF exports: VisionBoardAI\assets\exports\
  Recordings:  VisionBoardAI\assets\recordings\

LICENSE: MIT (c) 2024
"@ | Set-Content "release\README.txt"

Write-OK "Release folder ready: release\"

# ── Step 8: Verify ────────────────────────────────────────────
Write-Step "8/8" "Verifying build output..."
$exePath = "release\VisionBoardAI\VisionBoardAI.exe"
if (-not (Test-Path $exePath)) {
    Write-Fail "VisionBoardAI.exe not found in release folder."
}
$exeSize = [math]::Round((Get-Item $exePath).Length / 1MB, 1)
Write-OK "VisionBoardAI.exe confirmed ($exeSize MB)"

# ── Summary ───────────────────────────────────────────────────
Write-Host ""
Write-Host " ==========================================================" -ForegroundColor Cyan
Write-Host "  BUILD SUCCESSFUL" -ForegroundColor Green
Write-Host " ==========================================================" -ForegroundColor Cyan
Write-Host "  Executable:  $exePath" -ForegroundColor White
Write-Host "  Release dir: release\" -ForegroundColor White
Write-Host " ==========================================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"
