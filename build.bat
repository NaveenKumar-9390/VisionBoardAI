@echo off
setlocal EnableDelayedExpansion

:: ============================================================
:: VisionBoard AI – Windows Build Script
:: Run from the project root: build.bat
:: ============================================================

title VisionBoard AI – Build

echo.
echo  ==========================================================
echo   VisionBoard AI  ^|  Build Script  ^|  v2.0.0
echo   Transform Gestures into Ideas.
echo  ==========================================================
echo.

:: ── Step 1: Verify Python ────────────────────────────────────
echo [1/8] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found. Install Python 3.10+ and add to PATH.
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo        Found: %%v

:: ── Step 2: Verify PyInstaller ───────────────────────────────
echo [2/8] Checking PyInstaller...
python -m PyInstaller --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo        PyInstaller not found. Installing...
    pip install pyinstaller
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install PyInstaller.
        pause & exit /b 1
    )
)
for /f "tokens=*" %%v in ('python -m PyInstaller --version 2^>^&1') do echo        PyInstaller: %%v

:: ── Step 3: Verify all project dependencies ──────────────────
echo [3/8] Verifying project dependencies...
python -c "import cv2, mediapipe, numpy, reportlab, easyocr, pyautogui" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo        Some dependencies missing. Installing from requirements.txt...
    pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Dependency installation failed.
        pause & exit /b 1
    )
)
echo        All dependencies verified.

:: ── Step 4: Clean previous build artefacts ───────────────────
echo [4/8] Cleaning previous build artefacts...
if exist "build"       rmdir /s /q "build"
if exist "dist"        rmdir /s /q "dist"
echo        Clean complete.

:: ── Step 5: Ensure asset directories exist ───────────────────
echo [5/8] Preparing asset directories...
if not exist "assets\screenshots"  mkdir "assets\screenshots"
if not exist "assets\exports"      mkdir "assets\exports"
if not exist "assets\recordings"   mkdir "assets\recordings"
if not exist "assets\branding"     mkdir "assets\branding"
echo        Asset directories ready.

:: ── Step 6: Run PyInstaller ──────────────────────────────────
echo [6/8] Running PyInstaller...
echo        This may take 3–10 minutes on first run.
echo.
python -m PyInstaller VisionBoardAI.spec --clean --noconfirm
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] PyInstaller build failed. See output above.
    pause & exit /b 1
)
echo.
echo        Build complete: dist\VisionBoardAI\VisionBoardAI.exe

:: ── Step 7: Package release folder ──────────────────────────
echo [7/8] Packaging release folder...
if exist "release" rmdir /s /q "release"
mkdir "release"

:: Copy the built EXE and all bundled files
xcopy /E /I /Q "dist\VisionBoardAI" "release\VisionBoardAI" >nul

:: Copy top-level user-facing files into release root
copy "LICENSE"    "release\LICENSE"    >nul
copy "README.md"  "release\README.md"  >nul

:: Write version.txt
echo VisionBoard AI > "release\version.txt"
echo Version: 2.0.0 >> "release\version.txt"
echo Build date: %DATE% %TIME% >> "release\version.txt"
echo Platform: Windows x64 >> "release\version.txt"

:: Write README.txt (plain text for non-technical users)
(
echo VisionBoard AI – Gesture Controlled Drawing System
echo ==================================================
echo Transform Gestures into Ideas.
echo.
echo QUICK START
echo -----------
echo 1. Make sure your webcam is connected.
echo 2. Double-click VisionBoardAI\VisionBoardAI.exe to launch.
echo 3. Show your hand to the camera and start drawing!
echo.
echo KEYBOARD SHORTCUTS
echo ------------------
echo   Z        Undo
echo   Y        Redo
echo   S        Save PNG
echo   P        Export PDF
echo   R        Toggle Recording
echo   O        Run OCR
echo   C        Clear canvas
echo   F        Toggle Presentation mode
echo   ESC / Q  Quit
echo.
echo GESTURE CONTROLS
echo ----------------
echo   Index finger only          Draw
echo   Index + Middle fingers     Select / Toolbar
echo   All 5 fingers (hold)       Clear canvas
echo   4 fingers + thumb (hold)   Undo
echo   Thumb + Pinky (hold)       Save PNG
echo.
echo SAVED FILES
echo -----------
echo   PNG/JPG saves:  VisionBoardAI\assets\screenshots\
echo   PDF exports:    VisionBoardAI\assets\exports\
echo   Recordings:     VisionBoardAI\assets\recordings\
echo.
echo LICENSE: MIT ^(c^) 2024
) > "release\README.txt"

echo        Release folder ready: release\

:: ── Step 8: Verify executable exists ─────────────────────────
echo [8/8] Verifying build output...
if not exist "release\VisionBoardAI\VisionBoardAI.exe" (
    echo [ERROR] VisionBoardAI.exe not found in release folder.
    pause & exit /b 1
)
echo        VisionBoardAI.exe confirmed.

echo.
echo  ==========================================================
echo   BUILD SUCCESSFUL
echo  ==========================================================
echo   Executable:  release\VisionBoardAI\VisionBoardAI.exe
echo   Release:     release\
echo  ==========================================================
echo.
pause
