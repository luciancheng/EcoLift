# EcoLift

## Automatic Smart Spotting and Assisted Rep System

### Group 17 — IBEHS 5P06 Capstone 2025-2026

---

## Architecture

```
┌─────────────────────┐          ┌──────────────────────┐
│   Raspberry Pi      │          │   Laptop Dashboard   │
│                     │          │                      │
│  main.py            │ WebRTC   │   React + Vite       │
│  ├─ Vision (thread) │ ──────▶  │   ├─ Live video      │
│  ├─ Failure Detect  │          │   ├─ Telemetry       │
│  ├─ Socket.IO srv   │ ◀─────▶  │   ├─ Charts          │
|  └─ Servo PWM       | Socket.IO|   └─ HSV controls    |
│                     │          │                      │
└────────┬────────────┘          └──────────────────────┘
         │ Tailscale VPN (100.x.x.x)
```

- **Video streaming** — WebRTC (via `aiortc`)
- **Telemetry & commands** — Socket.IO (via `python-socketio` / `socket.io-client`)
- **Networking** — Tailscale for zero-config connectivity across networks
- **Hoist output** — Discrete U (up) / D (down) / N (neutral) commands

---

## Quick Start

### 1. Install Tailscale (one-time, both machines)

```bash
# macOS
brew install tailscale

# Raspberry Pi
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Note each machine's Tailscale IP (`tailscale ip -4`).

### 2. Raspberry Pi Setup

```bash
cd pi/

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# On Raspberry Pi you may also need system packages:
#   sudo apt install python3-picamera2 libavdevice-dev libavfilter-dev \
#                    libopus-dev libvpx-dev pkg-config

# Run (on Raspberry Pi with Pi camera)
python main.py --device pi

# Run (on laptop webcam — for development)
python main.py --device laptop
```

The signaling server starts on port **8765** by default (change with `--port`).

### 3. Dashboard Setup (Laptop)

```bash
cd dashboard/

# Install dependencies
npm install

# Configure Pi address — edit .env
#   For local dev (Pi code on same machine):  VITE_PI_HOST=localhost
#   For remote Pi via Tailscale:              VITE_PI_HOST=100.x.x.x
cp ../.env.example .env
# Edit .env with your Pi's Tailscale IP

# Start dev server
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## Development on Laptop Only (No Pi)

For development without a Raspberry Pi:

```bash
# Terminal 1 — run the backend with laptop webcam
cd pi/
python main.py --device laptop

# Terminal 2 — run the dashboard
cd dashboard/
# .env should have VITE_PI_HOST=localhost
npm run dev
```

---

## Project Structure

```
EcoLift/
├── pi/                          # Python backend (runs on Pi or laptop)
│   ├── main.py                  # Single entry point — starts all tasks
│   ├── shared_state.py          # Thread-safe shared state
│   ├── tracker.py               # OpenCV HSV colour tracking (thread)
│   ├── failure_detector.py      # Failure detection algorithm (async)
│   ├── signaling.py             # Socket.IO server + WebRTC signaling (async)
│   ├── streaming.py             # WebRTC video track
│   └── requirements.txt
│
├── dashboard/                   # React dashboard (runs on laptop)
│   ├── src/
│   │   ├── App.tsx              # Main layout
│   │   ├── components/          # UI components
│   │   ├── hooks/               # useSocket, useWebRTC
│   │   └── types.ts
│   ├── .env                     # VITE_PI_HOST / VITE_PI_PORT
│   └── package.json
│
├── motion_tracking/             # Legacy standalone tracker
├── controller/                  # Legacy standalone controller
├── .env.example
└── README.md
```

---

## Dashboard Features

| Feature | How |
|---|---|
| **Live video** | WebRTC stream from Pi camera |
| **HSV pick** | Click on video feed to auto-select tracking colour |
| **Manual HSV** | Type H/S/V bounds and click Apply |
| **Recalibrate** | Reset tracking origin to current position |
| **Telemetry** | Real-time velocity, assistance level (dx/dy toggleable via Debug) |
| **Hoist indicator** | U (up) / D (down) / N (neutral) in the status bar |
| **Debug overlay** | Toggle dx/dy text on the video feed and telemetry cards |
| **Status** | Failure, stall, and assistance indicators |
| **Charts** | Rolling 15-second plots of bar height and assistance |

---

## Tailscale Tips

- Run `tailscale ip -4` on each machine to find its VPN address.
- Both machines must be signed in to the same Tailscale account.
- No port forwarding or firewall rules needed — Tailscale handles NAT traversal.
- If the Pi's Tailscale IP changes, update `dashboard/.env` and restart the dev server.
