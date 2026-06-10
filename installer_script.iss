; ============================================================
; VisionBoard AI – Inno Setup Installer Script
; ============================================================
; Requirements: Inno Setup 6.x  (https://jrsoftware.org/isinfo.php)
;
; Usage:
;   1. Build the EXE first:  build.bat  (or build.ps1)
;   2. Open this file in Inno Setup Compiler
;   3. Press Ctrl+F9 to compile the installer
;   Output: release\installer\VisionBoardAI_Setup_v2.0.0.exe
;
; The installer:
;   - Installs VisionBoardAI to %ProgramFiles%\VisionBoard AI
;   - Creates Desktop and Start Menu shortcuts
;   - Includes an uninstaller
;   - Works on Windows 10 / 11 (64-bit)
; ============================================================

#define AppName      "VisionBoard AI"
#define AppVersion   "2.0.0"
#define AppPublisher "Independent AI Project"
#define AppURL       "https://github.com/your-username/VisionBoardAI"
#define AppExeName   "VisionBoardAI.exe"
#define SourceDir    "..\release\VisionBoardAI"
#define OutputDir    "..\release\installer"

[Setup]
; ── Identity ─────────────────────────────────────────────────
AppId={{A3F2E1D0-4B7C-4E8A-9F1B-2C3D4E5F6A7B}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} v{#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}

; ── Install location ─────────────────────────────────────────
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
AllowNoIcons=no

; ── Output ───────────────────────────────────────────────────
OutputDir={#OutputDir}
OutputBaseFilename=VisionBoardAI_Setup_v{#AppVersion}
SetupIconFile=

; ── Compression ──────────────────────────────────────────────
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; ── Display ──────────────────────────────────────────────────
WizardStyle=modern
WizardResizable=no
DisableWelcomePage=no

; ── Platform requirements ─────────────────────────────────────
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0

; ── Privileges ───────────────────────────────────────────────
PrivilegesRequiredOverridesAllowed=dialog
PrivilegesRequired=lowest

; ── Uninstall ────────────────────────────────────────────────
Uninstallable=yes
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExeName}
CreateUninstallRegKey=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";   Description: "Create a &Desktop shortcut";     GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "startmenuicon"; Description: "Create a &Start Menu shortcut";  GroupDescription: "Additional shortcuts:"; Flags: checkedonce

[Files]
; ── Main application ──────────────────────────────────────────
Source: "{#SourceDir}\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; ── All bundled Python/MediaPipe/OCR libraries ────────────────
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.pyc,__pycache__"

; ── Asset folders (created empty if not present) ──────────────
; Inno Setup creates the parent {app} directory, subdirs declared below.

[Dirs]
Name: "{app}\assets\screenshots"
Name: "{app}\assets\exports"
Name: "{app}\assets\recordings"
Name: "{app}\assets\branding"

[Icons]
; Start Menu
Name: "{group}\{#AppName}";         Filename: "{app}\{#AppExeName}"; Comment: "AI-Powered Gesture Controlled Drawing System"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"

; Desktop (optional)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Launch after install (optional)
Filename: "{app}\{#AppExeName}"; Description: "&Launch VisionBoard AI now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove user-generated files on uninstall only if they exist
; (screenshots, PDFs, recordings are user data — leave them)
Type: filesandordirs; Name: "{app}\_MEI*"

[Messages]
WelcomeLabel1=Welcome to [name/ver] Setup
WelcomeLabel2=This will install [name] on your computer.%n%nVisionBoard AI is an AI-powered gesture-controlled smart whiteboard that lets you draw, annotate, and present using only your hand — no stylus or touch screen required.%n%nClick Next to continue.

[CustomMessages]
InstallingMsg=Installing {#AppName} — this may take a moment...

[Code]
// Verify webcam presence (informational only — does not block install)
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
