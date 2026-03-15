import cv2
import numpy as np
import time
import threading
from shared_state import SharedState


class VisionTask:
    """OpenCV HSV colour-tracking loop. Runs in its own thread."""

    def __init__(self, state: SharedState, device: str, target_fps: int = 30):
        self.state = state
        self.device = device
        self.target_fps = target_fps
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    # ── Camera factory ──

    def _create_camera(self):
        if self.device == "pi":
            from picamera2 import Picamera2

            picam2 = Picamera2()
            picam2.configure(
                picam2.create_video_configuration(
                    main={"size": (1280, 720), "format": "RGB888"}
                )
            )
            picam2.start()

            def read():
                frame = picam2.capture_array()
                return True, frame

            def release():
                picam2.stop()

            return read, release

        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        return cap.read, cap.release

    # ── Main loop ──

    def run(self):
        read_frame, release_camera = self._create_camera()
        origin_center = None
        dx, dy = 0, 0

        try:
            while not self._stop.is_set():
                frame_start = time.monotonic()

                ret, frame = read_frame()
                if not ret:
                    time.sleep(0.01)
                    continue

                frame = cv2.flip(frame, 1)
                raw_frame = frame.copy()

                # ── Handle HSV-pick command from dashboard ──
                pick = self.state.consume_hsv_pick()
                if pick is not None:
                    px, py = pick
                    h_frame, w_frame = frame.shape[:2]
                    if 0 <= px < w_frame and 0 <= py < h_frame:
                        hsv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                        pixel = hsv_img[py, px]
                        h, s, v = int(pixel[0]), int(pixel[1]), int(pixel[2])
                        lower = [max(h - 10, 0), max(s - 60, 0), max(v - 60, 0)]
                        upper = [min(h + 10, 179), min(s + 60, 255), min(v + 60, 255)]
                        self.state.set_hsv_range(lower, upper)
                        print(f"[Vision] HSV picked: lower={lower}, upper={upper}")
                    origin_center = None

                # ── Handle recalibrate command ──
                if self.state.consume_recalibrate():
                    origin_center = None
                    print("[Vision] Origin recalibrated")

                # ── HSV tracking ──
                lower_hsv, upper_hsv = self.state.get_hsv_range()
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
                mask = cv2.erode(mask, None, iterations=2)
                mask = cv2.dilate(mask, None, iterations=2)

                contours, _ = cv2.findContours(
                    mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )

                if contours:
                    c = max(contours, key=cv2.contourArea)
                    M = cv2.moments(c)
                    cv2.drawContours(frame, [c], -1, (0, 255, 0), 2)

                    if M["m00"] > 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        cv2.circle(frame, (cx, cy), 6, (0, 255, 0), -1)

                        if origin_center is None:
                            origin_center = (cx, cy)

                        dx = cx - origin_center[0]
                        dy = -(cy - origin_center[1])

                if self.state.get_debug_overlay():
                    text = f"dx: {dx}, dy: {dy}"
                    cv2.putText(
                        frame, text, (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2,
                    )

                self.state.update_frame(raw_frame, frame)
                self.state.update_tracking(dx, dy)

                # Rate-limit to target FPS
                elapsed = time.monotonic() - frame_start
                sleep_time = (1.0 / self.target_fps) - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
        finally:
            release_camera()
            print("[Vision] Camera released")
