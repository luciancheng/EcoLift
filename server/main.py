"""
EcoLift Server — runs on the laptop.

Spawns three concurrent tasks:
  1. Vision       – OpenCV HSV tracking           (thread)
  2. Detector     – failure / assistance algorithm (async)
  3. Signaling    – Socket.IO + WebRTC server      (async)

The signaling server broadcasts telemetry to the React dashboard
and hoist commands (U/D/N) to the Raspberry Pi servo client.

Usage:
  python main.py                      # laptop webcam (default)
  python main.py --device pi          # Pi camera (if running on Pi)
  python main.py --port 9000          # custom port
"""

import asyncio
import argparse

from shared_state import SharedState
from tracker import VisionTask
from failure_detector import FailureDetector
from signaling import SignalingServer


async def main(device: str, port: int):
    state = SharedState()

    vision = VisionTask(state, device)
    detector = FailureDetector(state)
    server = SignalingServer(state, port=port)

    print(f"[Server] EcoLift starting  device={device}  port={port}")
    print(f"[Server] Dashboard  → http://localhost:5173")
    print(f"[Server] Pi servo   → connect to http://<this-ip>:{port}")

    try:
        await asyncio.gather(
            asyncio.to_thread(vision.run),
            detector.run(),
            server.run(),
        )
    finally:
        vision.stop()
        await server.cleanup()
        print("[Server] Shutdown complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EcoLift Server")
    parser.add_argument(
        "--device",
        choices=["laptop", "pi"],
        default="laptop",
        help="Camera source (default: laptop)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Signaling-server port (default: 8765)",
    )
    args = parser.parse_args()

    try:
        asyncio.run(main(args.device, args.port))
    except KeyboardInterrupt:
        print("\n[Server] Interrupted — exiting")
