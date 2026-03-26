import cv2
import numpy as np
import time
import threading
from shared_state import SharedState

# Default red HSV ranges (red wraps around the hue wheel)
DEFAULT_LOWER_1 = [0,   100,  60]
DEFAULT_UPPER_1 = [10,  255, 255]
DEFAULT_LOWER_2 = [160, 100,  60]
DEFAULT_UPPER_2 = [179, 255, 255]


class VisionTask:
    """OpenCV HSV red-circle tracking loop. Runs in its own thread."""

    def __init__(self, state: SharedState, device: str, target_fps: int = 30):
        self.state = state
        self.device = device
        self.target_fps = target_fps
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    # ── Camera factory ────────────────────────────────────────────────────────

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
            return lambda: (True, picam2.capture_array()), picam2.stop

        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT,  720)
        return cap.read, cap.release

    # ── Mask builder ──────────────────────────────────────────────────────────

    @staticmethod
    def _build_red_mask(hsv):
        """Merge both red hue bands and clean up with ellipse morphology."""
        m1 = cv2.inRange(hsv, np.array(DEFAULT_LOWER_1), np.array(DEFAULT_UPPER_1))
        m2 = cv2.inRange(hsv, np.array(DEFAULT_LOWER_2), np.array(DEFAULT_UPPER_2))
        mask = cv2.bitwise_or(m1, m2)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.erode(mask,  kernel, iterations=2)
        mask = cv2.dilate(mask, kernel, iterations=3)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        return mask

    # ── Contour helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _circularity(contour):
        area = cv2.contourArea(contour)
        if area == 0:
            return 0.0
        perim = cv2.arcLength(contour, True)
        return (4 * np.pi * area / (perim ** 2)) if perim else 0.0

    @staticmethod
    def _best_contour(contours, min_area=300, min_circularity=0.35):
        """Return the largest, most circular blob. None if nothing qualifies."""
        candidates = [
            c for c in contours
            if cv2.contourArea(c) >= min_area
            and VisionTask._circularity(c) >= min_circularity
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda c: cv2.contourArea(c) * VisionTask._circularity(c))

    # ── Main loop ─────────────────────────────────────────────────────────────

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

                raw_frame = frame.copy()

                # ── Recalibrate origin ────────────────────────────────────
                if self.state.consume_recalibrate():
                    origin_center = None
                    print("[Vision] Origin recalibrated")

                # ── Build red mask and find best circle ───────────────────
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                mask = self._build_red_mask(hsv)

                contours, _ = cv2.findContours(
                    mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                c = self._best_contour(contours)

                if c is not None:
                    M = cv2.moments(c)
                    cv2.drawContours(frame, [c], -1, (0, 255, 0), 2)

                    (ex, ey), er = cv2.minEnclosingCircle(c)
                    cv2.circle(frame, (int(ex), int(ey)), int(er), (0, 200, 255), 1)

                    if M["m00"] > 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        cv2.circle(frame, (cx, cy), 6, (0, 255, 0), -1)

                        if origin_center is None:
                            origin_center = (cx, cy)

                        dx = cx - origin_center[0]
                        dy = -(cy - origin_center[1])

                # ── Debug overlay ─────────────────────────────────────────
                if self.state.get_debug_overlay():
                    cv2.putText(
                        frame, f"dx: {dx}  dy: {dy}",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2,
                    )

                self.state.update_frame(raw_frame, frame)
                self.state.update_tracking(dx, dy)

                # ── Rate-limit to target FPS ──────────────────────────────
                elapsed = time.monotonic() - frame_start
                sleep_time = (1.0 / self.target_fps) - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        finally:
            release_camera()
            print("[Vision] Camera released")