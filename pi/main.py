"""
EcoLift — single entry-point for the Raspberry Pi.

Spawns three concurrent tasks:
  1. Vision       – OpenCV HSV tracking           (thread)
  2. Detector     – failure / assistance algorithm (async)
  3. Signaling    – Socket.IO + WebRTC server      (async)

Usage:
  python main.py --device pi          # Raspberry Pi camera
  python main.py --device laptop      # laptop webcam (for development)
  python main.py --port 9000          # custom signaling port
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

    print(f"[Main] EcoLift starting  device={device}  port={port}")
    print(f"[Main] Dashboard → connect to http://<this-ip>:{port}")

    try:
        await asyncio.gather(
            asyncio.to_thread(vision.run),
            detector.run(),
            server.run(),
        )
    finally:
        vision.stop()
        await server.cleanup()
        print("[Main] Shutdown complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EcoLift Squat-Rack Spotter")
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
        print("\n[Main] Interrupted — exiting")
