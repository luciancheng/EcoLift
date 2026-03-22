"""
Servo controller that reads hoist direction (U/D/N) from SharedState
and drives a servo via pigpio PWM.

Only runs on the Raspberry Pi (requires pigpio daemon).
Install prerequisites:
    sudo apt update
    sudo apt install pigpio python3-pigpio
    sudo systemctl enable pigpiod
    sudo systemctl start pigpiod
"""

import time
import threading
from shared_state import SharedState


class ServoController:
    SERVO_PIN = 18

    # Calibrated PWM pulse widths (µs). 270° servo range is 500–2500µs.
    DEFAULT_POS = 1500
    UP_POS = DEFAULT_POS + 1000       # 2500 – max CW
    DOWN_POS = DEFAULT_POS - 1000     # 500  – max CCW

    POLL_INTERVAL = 0.05  # 20 Hz

    def __init__(self, state: SharedState):
        self.state = state
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        import pigpio

        pi = pigpio.pi()
        if not pi.connected:
            print("[Servo] Could not connect to pigpio daemon — is pigpiod running?")
            return

        print("[Servo] Connected to pigpio, moving to default position")
        pi.set_servo_pulsewidth(self.SERVO_PIN, self.DEFAULT_POS)

        prev_direction = "N"

        try:
            while not self._stop.is_set():
                direction = self.state.get_hoist_direction()

                if direction != prev_direction:
                    if direction == "U":
                        pi.set_servo_pulsewidth(self.SERVO_PIN, self.UP_POS)
                        print("[Servo] → UP")
                    elif direction == "D":
                        pi.set_servo_pulsewidth(self.SERVO_PIN, self.DOWN_POS)
                        print("[Servo] → DOWN")
                    else:
                        pi.set_servo_pulsewidth(self.SERVO_PIN, self.DEFAULT_POS)
                        print("[Servo] → NEUTRAL")
                    prev_direction = direction

                time.sleep(self.POLL_INTERVAL)
        finally:
            print("[Servo] Returning to default and releasing pin")
            pi.set_servo_pulsewidth(self.SERVO_PIN, self.DEFAULT_POS)
            time.sleep(0.5)
            pi.set_servo_pulsewidth(self.SERVO_PIN, 0)
            pi.stop()
            print("[Servo] Stopped")
