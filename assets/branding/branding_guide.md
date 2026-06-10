# VisionBoard AI – Brand Guide

## Product Identity
**Name:** VisionBoard AI
**Tagline:** Transform Gestures into Ideas.
**Category:** AI-Powered Computer Vision Tool
**Tone:** Intelligent · Precise · Futuristic · Approachable

---

## Color Palette

| Role | Name | Hex | BGR (OpenCV) |
|---|---|---|---|
| Background | Space Navy | `#0F172A` | `(42, 23, 15)` |
| Primary | Cyber Cyan | `#06B6D4` | `(212, 182, 6)` |
| Secondary | Electric Blue | `#3B82F6` | `(246, 130, 59)` |
| Accent | Neon Aqua | `#22D3EE` | `(238, 211, 34)` |
| Success | Matrix Green | `#10B981` | `(145, 185, 16)` |
| Warning | Amber Alert | `#F59E0B` | `(11, 158, 245)` |
| Error | Alert Red | `#EF4444` | `(68, 68, 239)` |
| Text Primary | Ice White | `#E2E8F0` | `(224, 232, 226)` |
| Text Muted | Slate | `#64748B` | `(139, 116, 100)` |

---

## Typography

### Headings / UI Labels
- Font: **Exo 2** (Google Fonts)
- Weight: Bold (700)
- Case: Title Case for labels, UPPERCASE for status indicators

### Body / Descriptions
- Font: **Inter** (Google Fonts)
- Weight: Regular (400) / Medium (500)

### Code / Technical
- Font: **JetBrains Mono**
- Used in: config file references, version strings

### OpenCV Fallback (in-app rendering)
- `cv2.FONT_HERSHEY_DUPLEX` — titles, app name
- `cv2.FONT_HERSHEY_SIMPLEX` — all UI labels, notifications

---

## UI Theme

### Dark Futuristic AI Interface
- Base background: `#0F172A` (Space Navy)
- Surface / card: `#1E293B`
- Elevated surface: `#334155`
- Border: `#475569` inactive, `#06B6D4` active

### Button States
| State | Background | Border | Text |
|---|---|---|---|
| Default | `#1E293B` | `#475569` | `#E2E8F0` |
| Hover | `#334155` | `#06B6D4` | `#FFFFFF` |
| Active | `#0E4155` | `#06B6D4` | `#06B6D4` |
| Disabled | `#0F172A` | `#334155` | `#64748B` |

---

## Icon System

| Action | Symbol | Notes |
|---|---|---|
| Draw | ✏ | Pencil |
| Erase | ⌫ | Backspace |
| Undo | ↩ | Counterclockwise |
| Redo | ↪ | Clockwise |
| Save PNG | 💾 | Floppy disk |
| Export PDF | 📄 | Document |
| Record | ● | Solid red circle |
| Stop Record | ■ | Solid square |
| OCR | 🔤 | Text recognition |
| Clear | ✕ | Cross |
| Shape Detect | ⬡ | Hexagon |

---

## Notification Levels

| Level | Color | Usage |
|---|---|---|
| Info | Cyber Cyan `#06B6D4` | General actions, mode changes |
| Success | Matrix Green `#10B981` | Save, export, record saved |
| Warning | Amber Alert `#F59E0B` | Clear, destructive actions |
| Error | Alert Red `#EF4444` | Failed operations |

---

## Product Voice

**Do:**
- Use precise, confident language
- Prefer active voice: "Saved successfully" not "File has been saved"
- Use technical shorthand where space is limited: "OCR", "FPS", "REC"

**Don't:**
- Use casual slang
- Add excessive exclamation marks
- Use passive/vague status messages

---

## Design Language

The VisionBoard AI interface follows a **Neo-Terminal** aesthetic:
- Dark navy backgrounds evoking depth and focus
- Cyan/teal neon accents referencing sci-fi HUDs and ML visualisations
- Minimal UI chrome — the canvas is the hero
- Rounded-rect buttons (r=5px) for approachability within a technical context
- Thin (1px) borders, never box shadows (not available in OpenCV)
- Status information is *shown*, not *explained* — FPS, REC timer, shape name are self-evident
