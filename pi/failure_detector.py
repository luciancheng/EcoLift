import asyncio
import time
from shared_state import SharedState


class FailureDetector:
    """
    Async task that reads tracking telemetry from shared state, runs the
    failure-detection / assistance-ramp algorithm, and writes results back.

    Ported from controller/controller.py — same constants and logic, but
    no UDP socket and no matplotlib plotting.
    """

    FAILURE_Y_THRESHOLD = -300
    STALL_VEL_THRESHOLD = 20
    STALL_TIME = 2.0
    ASSIST_Y_THRESHOLD = -10
    VEL_SMOOTHING_ALPHA = 0.2
    RAMP_UP_RATE = 0.25
    RAMP_DOWN_RATE = 0.4
    DOWN_DURATION = 3.0

    def __init__(self, state: SharedState):
        self.state = state
        self.u = 0.0
        self.smoothed_vel = None
        self.last_motion_time = None
        self.last_time_above_threshold = None
        self.start_help = False
        self.last_time = None
        self._prev_dy = None

        self.hoist_direction = "N"
        self._was_helping = False
        self._down_since = None

    async def run(self):
        print("[Detector] Failure detection online")
        while True:
            tracking = self.state.get_tracking()
            dy = tracking["dy"]
            t = time.time()

            if self.last_time is None:
                self.last_time = t
                self.last_motion_time = t
                self.last_time_above_threshold = t
                self._prev_dy = dy
                await asyncio.sleep(0.01)
                continue

            dt = t - self.last_time
            self.last_time = t

            if self._prev_dy is None:
                self._prev_dy = dy
                await asyncio.sleep(0.01)
                continue

            ddy = dy - self._prev_dy
            safe_dt = max(dt, 1e-6)
            raw_vel = ddy / safe_dt

            if self.smoothed_vel is None:
                self.smoothed_vel = raw_vel
            else:
                self.smoothed_vel = (
                    self.VEL_SMOOTHING_ALPHA * raw_vel
                    + (1 - self.VEL_SMOOTHING_ALPHA) * self.smoothed_vel
                )

            vel = self.smoothed_vel
            speed = abs(vel)
            self._prev_dy = dy

            if speed > self.STALL_VEL_THRESHOLD:
                self.last_motion_time = t

            if dy > self.FAILURE_Y_THRESHOLD:
                self.last_time_above_threshold = t

            stalled = (t - self.last_motion_time) > self.STALL_TIME
            fail_pos = (dy < self.FAILURE_Y_THRESHOLD) and (
                (t - self.last_time_above_threshold) > self.STALL_TIME
            )
            failure_detected = fail_pos or stalled

            if failure_detected:
                self.start_help = True

            if self.start_help:
                if speed < self.STALL_VEL_THRESHOLD:
                    self.u += self.RAMP_UP_RATE * dt
                if dy > self.ASSIST_Y_THRESHOLD:
                    self.start_help = False
            else:
                self.u -= self.RAMP_DOWN_RATE * dt

            self.u = max(0.0, min(1.0, self.u))

            # ── Hoist direction state machine (U / D / N) ──
            was_helping = self._was_helping
            self._was_helping = self.start_help

            if self.start_help:
                self.hoist_direction = "U"
                self._down_since = None
            elif was_helping and not self.start_help:
                self.hoist_direction = "D"
                self._down_since = t
            elif self.hoist_direction == "D":
                if self._down_since is not None and (t - self._down_since) > self.DOWN_DURATION:
                    self.hoist_direction = "N"
                    self._down_since = None
            else:
                self.hoist_direction = "N"

            self.state.update_detection(
                velocity=vel,
                assistance=self.u,
                failure=failure_detected,
                stalled=stalled,
                helping=self.start_help,
                hoist_direction=self.hoist_direction,
            )

            await asyncio.sleep(0.01)
