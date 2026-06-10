# VisionBoard AI — Deployment Guide

> From local dev to a live public URL at `https://visionboard-ai.streamlit.app`

---

## Quick Start (Local)

```bash
pip install -r requirements_web.txt
streamlit run app.py
```
Opens at `http://localhost:8501`

---

## Deploy to Streamlit Cloud (Recommended — Free)

### Step 1 — Prepare GitHub repository

```bash
# Initialise git (skip if already done)
git init
git add .
git commit -m "feat: VisionBoard AI v2.1 — touchless web version"

# Create repo on GitHub (github.com → New repository → VisionBoardAI)
git remote add origin https://github.com/<your-username>/VisionBoardAI.git
git push -u origin main
```

Repository structure Streamlit Cloud expects:
```
VisionBoardAI/           ← root of GitHub repo
├── app.py               ← entry point (set this in Cloud dashboard)
├── requirements_web.txt ← dependencies (set this in Cloud dashboard)
├── packages.txt         ← apt system packages (auto-detected by Cloud)
├── .streamlit/
│   └── config.toml      ← theme + server settings
└── ...
```

### Step 2 — Create Streamlit Cloud account

Go to **https://share.streamlit.io** → Sign in with GitHub

### Step 3 — Deploy

1. Click **New app**
2. **Repository**: `your-username/VisionBoardAI`
3. **Branch**: `main`
4. **Main file path**: `app.py`
5. Expand **Advanced settings**:
   - **Python version**: `3.11`
   - **Python packages file**: `requirements_web.txt`
6. Click **Deploy!**

Build takes ~3–5 minutes on first deploy.

### Step 4 — Your public URL

Streamlit Cloud assigns:
```
https://<your-username>-visionboardai.streamlit.app
```
or (if you choose a custom app name):
```
https://visionboard-ai.streamlit.app
```

Share this URL — no installation required for users.

---

## Custom URL on Streamlit Cloud

### Option A — Choose a cleaner subdomain during deploy

In the "App URL" field on the deploy screen, type:
```
visionboard-ai
```
Your URL becomes:
```
https://visionboard-ai.streamlit.app
```

> Note: The subdomain must be unique across all Streamlit Cloud apps.

### Option B — Custom domain (e.g. visionboardai.com)

Streamlit Cloud Community (free) does **not** support custom domains.
Custom domains require **Streamlit Cloud Teams** or self-hosting.

**Self-hosted custom domain (Docker + Nginx + domain registrar):**

1. Register domain at Namecheap, Cloudflare, or GoDaddy
2. Point DNS A record to your server IP
3. Run the Docker container (see Docker section below)
4. Add Nginx reverse proxy + Let's Encrypt SSL:

```nginx
# /etc/nginx/sites-available/visionboardai
server {
    listen 80;
    server_name visionboardai.com www.visionboardai.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name visionboardai.com www.visionboardai.com;

    ssl_certificate     /etc/letsencrypt/live/visionboardai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/visionboardai.com/privkey.pem;

    location / {
        proxy_pass         http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host $host;
        proxy_read_timeout 86400;
    }
}
```

```bash
sudo certbot --nginx -d visionboardai.com -d www.visionboardai.com
sudo nginx -t && sudo systemctl reload nginx
```

Access at: `https://visionboardai.com`

**Cloudflare Tunnel** (zero-config custom domain, free):
```bash
cloudflared tunnel --url http://localhost:8501
# Cloudflare provides a public URL like: https://random.trycloudflare.com
# With paid Cloudflare, add your own domain and point it to the tunnel
```

---

## Deploy with Docker (Full Features)

Use this for self-hosted deployment with OCR enabled.

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install web dependencies + optional OCR
RUN pip install --no-cache-dir -r requirements_web.txt

# Uncomment for EasyOCR (adds ~2 GB, enable on servers with enough RAM):
# RUN pip install --no-cache-dir easyocr torch torchvision

EXPOSE 8501

HEALTHCHECK CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=true"]
```

```bash
docker build -t visionboard-ai .
docker run -d -p 8501:8501 --name visionboard visionboard-ai
```

### Push to Docker Hub
```bash
docker tag visionboard-ai your-dockerhub/visionboard-ai:latest
docker push your-dockerhub/visionboard-ai:latest
```

### Deploy to AWS EC2 / GCP / Azure
```bash
# SSH into your VM
docker pull your-dockerhub/visionboard-ai:latest
docker run -d -p 80:8501 --restart=always visionboard-ai
```

---

## GitHub Portfolio Setup

Recommended repository settings for maximum visibility:

### Repository description (GitHub About section)
```
AI-powered gesture-controlled whiteboard — draw, correct shapes, export PDF, and run OCR 
using only your hand. Live demo: https://visionboard-ai.streamlit.app
```

### Topics (add to GitHub repo)
```
python opencv mediapipe computer-vision hand-tracking gesture-recognition
ai ocr streamlit webrtc drawing whiteboard real-time machine-learning
```

### GitHub Pages (optional landing page)
Create `docs/index.html` or use the README as the landing page.
Enable GitHub Pages: Settings → Pages → Deploy from branch `main` / `docs`.

### Recommended .github structure
```
.github/
├── workflows/
│   └── build.yml          # CI: lint + test on push
└── ISSUE_TEMPLATE/
    └── bug_report.md
```

---

## Deployment Checklist

Before publishing the URL:

### Code
- [ ] `app.py` entry point works locally with `streamlit run app.py`
- [ ] `requirements_web.txt` uses `opencv-python-headless` (not `opencv-python`)
- [ ] `packages.txt` includes `libgl1-mesa-glx` and `libglib2.0-0`
- [ ] `.streamlit/config.toml` has correct theme settings
- [ ] No hardcoded local paths in any web module
- [ ] `web/web_state.py` thread lock covers all shared state writes

### Features
- [ ] Webcam opens in Chrome/Firefox/Edge (HTTPS required, `localhost` OK for dev)
- [ ] Hand tracking detects landmarks in reasonable lighting
- [ ] Draw mode (index finger) draws on canvas
- [ ] Selection mode (index + middle) activates toolbar hover
- [ ] Dwell-time ring animates and fires action after ~1 s
- [ ] All 6 color swatches change draw color
- [ ] All 5 tools work (Pencil, Marker, Highlight, Calligraphy, Eraser)
- [ ] Thickness + / − buttons work via hover
- [ ] Undo and Redo work via hover and sidebar
- [ ] Clear works via hover, hold gesture, and sidebar
- [ ] Download PNG produces a valid image file
- [ ] Download PDF produces a valid PDF (if reportlab installed)
- [ ] Shape detection badge appears after drawing a circle/rectangle
- [ ] OCR button runs without crashing (shows "not installed" gracefully if absent)
- [ ] Hold gestures fire correctly (undo, clear, save, size up/down, OCR)
- [ ] Sidebar controls work as mouse fallback

### Deployment
- [ ] GitHub repository is public
- [ ] Streamlit Cloud app deploys without build errors
- [ ] Live URL is accessible from a phone/tablet (WebRTC works over HTTPS)
- [ ] Camera permission prompt appears on first visit

---

## WebRTC Notes

| Scenario | Works? |
|---|---|
| `localhost` (same machine) | ✅ Always |
| Local network (different device) | ✅ With STUN |
| Behind corporate NAT/firewall | ⚠️ May need TURN |
| Streamlit Cloud (HTTPS) | ✅ STUN is sufficient |
| Mobile browser (Chrome/Safari) | ✅ HTTPS required |

### Adding a TURN server for restricted networks
```python
# In app.py, replace _RTC_CONFIG:
_RTC_CONFIG = RTCConfiguration(iceServers=[
    {"urls": ["stun:stun.l.google.com:19302"]},
    {
        "urls":       ["turn:your-turn-server.com:3478"],
        "username":   "your-username",
        "credential": "your-credential",
    },
])
```
Free TURN options: `metered.ca` (free tier), `Twilio`.

---

## File Reference

| File | Role |
|---|---|
| `app.py` | Streamlit web app entry point |
| `web/gesture_toolbar.py` | Touchless in-video toolbar with dwell-time hover |
| `web/web_state.py` | Thread-safe session state |
| `web/pdf_bytes.py` | In-memory PDF for browser download |
| `requirements_web.txt` | Web dependencies |
| `packages.txt` | Streamlit Cloud apt packages |
| `.streamlit/config.toml` | Theme + server config |
| `DEPLOY.md` | This document |
