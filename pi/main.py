"""
EcoLift Pi — thin servo client that connects to the laptop server
via Socket.IO and drives the servo based on hoist commands (U/D/N).

Usage:
  python main.py --host 100.x.x.x                  # Pi with real servo
  python main.py --host 100.x.x.x --device laptop  # debug without hardware
  python main.py --host localhost  --device laptop   # fully local debug
"""

import asyncio
import argparse
import socketio

from servo import ServoController


async def main(host: str, port: int, device: str):
    servo = ServoController(device)

    sio = socketio.AsyncClient(
        reconnection=True,
        reconnection_delay=1,
        reconnection_delay_max=5,
    )

    @sio.event
    async def connect():
        print(f"[Pi] Connected to server at {host}:{port}")
        await sio.emit("register_pi")

    @sio.event
    async def disconnect():
        print("[Pi] Disconnected from server — will reconnect")

    @sio.on("hoist_command")
    async def on_hoist_command(data):
        servo.set_direction(data["direction"])

    url = f"http://{host}:{port}"
    print(f"[Pi] Connecting to {url} ...")

    await sio.connect(url, transports=["websocket", "polling"])

    try:
        await asyncio.gather(
            asyncio.to_thread(servo.run),
            sio.wait(),
        )
    finally:
        servo.stop()
        await sio.disconnect()
        print("[Pi] Shutdown complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EcoLift Pi Servo Client")
    parser.add_argument(
        "--host",
        required=True,
        help="Laptop server IP (Tailscale IP or localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Server port (default: 8765)",
    )
    parser.add_argument(
        "--device",
        choices=["laptop", "pi"],
        default="pi",
        help="'pi' for real servo, 'laptop' for mock/debug (default: pi)",
    )
    args = parser.parse_args()

    try:
        asyncio.run(main(args.host, args.port, args.device))
    except KeyboardInterrupt:
        print("\n[Pi] Interrupted — exiting")
