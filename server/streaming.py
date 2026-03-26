import asyncio
import fractions
import numpy as np
from av import VideoFrame
from aiortc import MediaStreamTrack


class CameraStreamTrack(MediaStreamTrack):
    """
    aiortc video track that reads annotated frames from SharedState
    and delivers them at ~30 fps over WebRTC.
    """

    kind = "video"

    def __init__(self, state):
        super().__init__()
        self.state = state
        self._pts = 0
        self._time_base = fractions.Fraction(1, 30)
        self._fps = 30

    async def recv(self):
        await asyncio.sleep(1 / self._fps)

        frame = self.state.get_annotated_frame()
        if frame is None:
            frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        video_frame.pts = self._pts
        video_frame.time_base = self._time_base
        self._pts += 1

        return video_frame
