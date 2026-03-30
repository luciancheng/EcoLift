import asyncio
import socketio
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription

from streaming import CameraStreamTrack
from shared_state import SharedState


class SignalingServer:
    """
    Socket.IO server (on aiohttp) that handles:
      - WebRTC offer/answer signaling for video streaming
      - Telemetry broadcasting at ~20 Hz
      - hoist_command broadcasting for the Pi servo client
      - Dashboard commands (HSV pick, recalibrate, manual HSV set)
    """

    def __init__(self, state: SharedState, host: str = "0.0.0.0", port: int = 8765):
        self.state = state
        self.host = host
        self.port = port

        self.sio = socketio.AsyncServer(
            cors_allowed_origins="*",
            async_mode="aiohttp",
        )
        self.app = web.Application()
        self.sio.attach(self.app)

        self.pcs: set[RTCPeerConnection] = set()
        self._pi_sids: set[str] = set()
        self._register_events()

    # ── Socket.IO event handlers ──

    def _register_events(self):
        sio = self.sio
        state = self.state
        pcs = self.pcs
        pi_sids = self._pi_sids

        @sio.event
        async def connect(sid, environ):
            print(f"[Signaling] Client connected: {sid}")

        @sio.event
        async def disconnect(sid):
            print(f"[Signaling] Client disconnected: {sid}")
            if sid in pi_sids:
                pi_sids.discard(sid)
                state.set_pi_connected(len(pi_sids) > 0)
                print("[Signaling] Pi disconnected")

        @sio.event
        async def register_pi(sid, data=None):
            pi_sids.add(sid)
            state.set_pi_connected(True)
            print(f"[Signaling] Pi registered: {sid}")

        @sio.event
        async def offer(sid, data):
            offer_desc = RTCSessionDescription(sdp=data["sdp"], type=data["type"])

            pc = RTCPeerConnection()
            pcs.add(pc)

            @pc.on("connectionstatechange")
            async def on_state_change():
                if pc.connectionState in ("failed", "closed"):
                    await pc.close()
                    pcs.discard(pc)

            pc.addTrack(CameraStreamTrack(state))

            await pc.setRemoteDescription(offer_desc)
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)

            await sio.emit(
                "answer",
                {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type},
                to=sid,
            )
            print(f"[Signaling] WebRTC answer sent to {sid}")

        @sio.event
        async def hsv_pick(sid, data):
            state.request_hsv_pick(int(data["x"]), int(data["y"]))

        @sio.event
        async def set_hsv(sid, data):
            state.set_hsv_range(data["lower"], data["upper"])
            print(f"[Signaling] HSV range updated: {data['lower']} → {data['upper']}")

        @sio.event
        async def recalibrate(sid, data=None):
            state.request_recalibrate()
            print("[Signaling] Recalibration requested")

        @sio.event
        async def toggle_overlay(sid, data):
            state.set_debug_overlay(bool(data.get("enabled", False)))
            print(f"[Signaling] Debug overlay: {data.get('enabled')}")

        @sio.event
        async def set_failure_threshold(sid, data):
            state.set_failure_y_threshold(float(data["value"]))
            print(f"[Signaling] Failure Y threshold: {data['value']}")

        @sio.event
        async def reset_hoist(sid, data=None):
            print("[Signaling] Reset hoist — forwarding to Pi")
            for pi_sid in pi_sids:
                await sio.emit("reset_hoist", {}, to=pi_sid)

    # ── Telemetry + hoist command broadcast loop ──

    async def _broadcast_telemetry(self):
        while True:
            telemetry = self.state.get_telemetry()
            await self.sio.emit("telemetry", telemetry)
            await self.sio.emit(
                "hoist_command", {"direction": telemetry["hoist_direction"]}
            )
            await asyncio.sleep(0.05)

    # ── Lifecycle ──

    async def run(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f"[Signaling] Server listening on http://{self.host}:{self.port}")

        await self._broadcast_telemetry()

    async def cleanup(self):
        coros = [pc.close() for pc in self.pcs]
        await asyncio.gather(*coros)
        self.pcs.clear()
        print("[Signaling] All peer connections closed")
