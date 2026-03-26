# EcoLift

## Automatic Smart Spotting and Assisted Rep System

### Group 17 — IBEHS 5P06 Capstone 2025-2026

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                      Laptop                          │
│                                                      │
│  server/main.py              dashboard/ (React)      │
│  ├─ Vision (OpenCV)          ├─ Live video (WebRTC)  │
│  ├─ Failure Detector ──────▶ ├─ Telemetry            │
│  └─ Signaling Server ◀────▶ ├─ Hoist output panel   │
│         │     (Socket.IO     └─ HSV / controls       │
│         │      + WebRTC)                             │
│         │                                            │
└─────────┼────────────────────────────────────────────┘
          │  hoist_command (U/D/N)
          │  via Socket.IO over Tailscale
          ▼
┌──────────────────────┐
│   Raspberry Pi       │
│                      │
│  pi/main.py          │
│  ├─ Socket.IO client │
│  └─ Servo controller │──▶ Physical hoist
│      (pigpio PWM)    │
└──────────────────────┘
```

- **Laptop** runs all computation: camera capture, OpenCV tracking, failure detection, WebRTC streaming, and the Socket.IO signaling server
- **Pi** is a thin client that receives hoist commands (U/D/N) over Socket.IO and drives the servo
- **Dashboard** is a React app on the laptop that displays live video, telemetry, and controls
- **Tailscale** provides zero-config networking between laptop and Pi

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

Note each machine's Tailscale IP: `tailscale ip -4`

### 2. Laptop — Server (vision + detection + signaling)

```bash
cd server/
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# macOS may need: brew install ffmpeg

python main.py
```

The server starts on port **8765** (change with `--port`).

### 3. Laptop — Dashboard (React)

```bash
cd dashboard/
npm install

# .env should have VITE_PI_HOST=localhost (default)
npm run dev
```

Open **http://localhost:5173**.

### 4. Raspberry Pi — Servo Client

```bash
cd pi/
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# pigpio (system package):
# sudo apt install pigpio python3-pigpio
# sudo systemctl enable pigpiod && sudo systemctl start pigpiod

# Run with real servo hardware
python main.py --host <LAPTOP_TAILSCALE_IP>

# Or debug without hardware
python main.py --host <LAPTOP_TAILSCALE_IP> --device laptop
```

---

## Development — Fully Local (no Pi needed)

Run everything on the laptop to test end-to-end without hardware:

```bash
# Terminal 1 — server (vision + detection + signaling)
cd server/
python main.py

# Terminal 2 — dashboard
cd dashboard/
npm run dev

# Terminal 3 — mock servo client (optional, to verify hoist commands)
cd pi/
python main.py --host localhost --device laptop
```

---

## Project Structure

```
EcoLift/
├── server/                      # Runs on laptop
│   ├── main.py                  # Entry point — starts vision, detection, signaling
│   ├── shared_state.py          # Thread-safe shared state
│   ├── tracker.py               # OpenCV HSV colour tracking (thread)
│   ├── failure_detector.py      # Failure detection + hoist state machine (async)
│   ├── signaling.py             # Socket.IO + WebRTC server (async)
│   ├── streaming.py             # WebRTC video track
│   └── requirements.txt
│
├── pi/                          # Runs on Raspberry Pi
│   ├── main.py                  # Socket.IO client — receives hoist commands
│   ├── servo.py                 # Servo controller (pigpio PWM or mock)
│   └── requirements.txt
│
├── dashboard/                   # React dashboard (runs on laptop)
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/          # VideoFeed, TelemetryPanel, HoistPanel, etc.
│   │   ├── hooks/               # useSocket, useWebRTC
│   │   └── types.ts
│   ├── .env                     # VITE_PI_HOST / VITE_PI_PORT
│   └── package.json
│
├── motion_tracking/             # Legacy standalone tracker
├── controller/                  # Legacy standalone controller
└── README.md
```

---

## Communication Summary

| Path | Protocol | Data |
|---|---|---|
| Server → Dashboard | WebRTC | Live video stream |
| Server → Dashboard | Socket.IO | Telemetry (dx, dy, velocity, assistance, hoist direction) |
| Dashboard → Server | Socket.IO | Commands (HSV pick, recalibrate, set HSV, debug toggle) |
| Server → Pi | Socket.IO | Hoist commands (U / D / N) |
