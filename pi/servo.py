"""
Servo controller that receives hoist direction (U/D/N) and drives
a servo via pigpio PWM.

In --device pi mode, controls real hardware.
In --device laptop mode, just logs direction changes (for debugging).

pigpio prerequisites (Pi only):
    sudo apt update
    sudo apt install pigpio python3-pigpio
    sudo systemctl enable pigpiod
    sudo systemctl start pigpiod
"""

import time
import threading


class ServoController:
    SERVO_PIN = 18

    # Calibrated PWM pulse widths (µs). 270° servo range is 500–2500µs.
    DEFAULT_POS = 1500
    UP_POS = DEFAULT_POS + 1000       # 2500 – max CW
    DOWN_POS = DEFAULT_POS - 1000     # 500  – max CCW

    POLL_INTERVAL = 0.05  # 20 Hz

    def __init__(self, device: str):
        self.device = device
        self._direction = "N"
        self._lock = threading.Lock()
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def set_direction(self, direction: str):
        with self._lock:
            self._direction = direction

    def get_direction(self) -> str:
        with self._lock:
            return self._direction

    def run(self):
        if self.device == "pi":
            self._run_hardware()
        else:
            self._run_mock()

    def _run_hardware(self):
        import pigpio

        pi = pigpio.pi()
        if not pi.connected:
            print("[Servo] Could not connect to pigpio daemon — is pigpiod running?")
            return

        print("[Servo] Connected to pigpio, moving to default position")
        pi.set_servo_pulsewidth(self.SERVO_PIN, self.DEFAULT_POS)

        prev = "N"
        try:
            while not self._stop.is_set():
                d = self.get_direction()
                if d != prev:
                    if d == "U":
                        pi.set_servo_pulsewidth(self.SERVO_PIN, self.UP_POS)
                        print("[Servo] → UP")
                    elif d == "D":
                        pi.set_servo_pulsewidth(self.SERVO_PIN, self.DOWN_POS)
                        print("[Servo] → DOWN")
                    else:
                        pi.set_servo_pulsewidth(self.SERVO_PIN, self.DEFAULT_POS)
                        print("[Servo] → NEUTRAL")
                    prev = d
                time.sleep(self.POLL_INTERVAL)
        finally:
            print("[Servo] Returning to default and releasing pin")
            pi.set_servo_pulsewidth(self.SERVO_PIN, self.DEFAULT_POS)
            time.sleep(0.5)
            pi.set_servo_pulsewidth(self.SERVO_PIN, 0)
            pi.stop()
            print("[Servo] Stopped")

    def _run_mock(self):
        """Laptop mode — log direction changes without hardware."""
        print("[Servo] Running in mock mode (no hardware)")
        prev = "N"
        while not self._stop.is_set():
            d = self.get_direction()
            if d != prev:
                print(f"[Servo mock] → {d}")
                prev = d
            time.sleep(self.POLL_INTERVAL)
        print("[Servo mock] Stopped")
