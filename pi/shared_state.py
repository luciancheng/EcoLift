import threading
import numpy as np
from typing import Optional, Tuple


class SharedState:
    """Thread-safe state shared between vision, detection, signaling, and streaming tasks."""

    def __init__(self):
        self._lock = threading.Lock()

        # HSV tracking parameters
        self.lower_hsv = np.array([0, 120, 70])
        self.upper_hsv = np.array([10, 255, 255])

        self._raw_frame: Optional[np.ndarray] = None
        self._annotated_frame: Optional[np.ndarray] = None

        self._dx = 0
        self._dy = 0
        self._origin_center: Optional[Tuple[int, int]] = None

        self._velocity = 0.0
        self._assistance = 0.0
        self._failure = False
        self._stalled = False
        self._helping = False
        self._hoist_direction = "N"

        self._hsv_pick_coords: Optional[Tuple[int, int]] = None
        self._recalibrate_requested = False
        self._show_debug_overlay = False

    # ── Frame access ──

    def update_frame(self, raw: np.ndarray, annotated: np.ndarray):
        with self._lock:
            self._raw_frame = raw
            self._annotated_frame = annotated

    def get_annotated_frame(self) -> Optional[np.ndarray]:
        with self._lock:
            return self._annotated_frame.copy() if self._annotated_frame is not None else None

    def get_raw_frame(self) -> Optional[np.ndarray]:
        with self._lock:
            return self._raw_frame.copy() if self._raw_frame is not None else None

    # ── Tracking telemetry ──

    def update_tracking(self, dx: int, dy: int):
        with self._lock:
            self._dx = dx
            self._dy = dy

    def get_tracking(self) -> dict:
        with self._lock:
            return {"dx": self._dx, "dy": self._dy}

    # ── Failure-detection output ──

    def update_detection(
        self,
        velocity: float,
        assistance: float,
        failure: bool,
        stalled: bool,
        helping: bool,
        hoist_direction: str = "N",
    ):
        with self._lock:
            self._velocity = velocity
            self._assistance = assistance
            self._failure = failure
            self._stalled = stalled
            self._helping = helping
            self._hoist_direction = hoist_direction

    # ── Aggregated telemetry for the dashboard ──

    def get_telemetry(self) -> dict:
        with self._lock:
            return {
                "dx": self._dx,
                "dy": self._dy,
                "velocity": round(self._velocity, 4),
                "assistance": round(self._assistance, 3),
                "failure": self._failure,
                "stalled": self._stalled,
                "helping": self._helping,
                "hoist_direction": self._hoist_direction,
                "lower_hsv": self.lower_hsv.tolist(),
                "upper_hsv": self.upper_hsv.tolist(),
            }

    # ── HSV range ──

    def set_hsv_range(self, lower, upper):
        with self._lock:
            self.lower_hsv = np.array(lower, dtype=np.uint8)
            self.upper_hsv = np.array(upper, dtype=np.uint8)

    def get_hsv_range(self):
        with self._lock:
            return self.lower_hsv.copy(), self.upper_hsv.copy()

    # ── Dashboard commands ──

    def request_hsv_pick(self, x: int, y: int):
        with self._lock:
            self._hsv_pick_coords = (x, y)

    def consume_hsv_pick(self) -> Optional[Tuple[int, int]]:
        with self._lock:
            coords = self._hsv_pick_coords
            self._hsv_pick_coords = None
            return coords

    # ── Debug overlay toggle ──

    def set_debug_overlay(self, enabled: bool):
        with self._lock:
            self._show_debug_overlay = enabled

    def get_debug_overlay(self) -> bool:
        with self._lock:
            return self._show_debug_overlay

    def request_recalibrate(self):
        with self._lock:
            self._recalibrate_requested = True

    def consume_recalibrate(self) -> bool:
        with self._lock:
            val = self._recalibrate_requested
            self._recalibrate_requested = False
            return val

    # ── Origin center (used by tracker) ──

    @property
    def origin_center(self):
        with self._lock:
            return self._origin_center

    @origin_center.setter
    def origin_center(self, value):
        with self._lock:
            self._origin_center = value
