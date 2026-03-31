"""
Dual servo controller that receives hoist direction (U/D/N) and drives
two servos simultaneously via pigpio PWM.

Servo 1 (GPIO 18): left servo,  ±1000µs range (500–2500µs)
Servo 2 (GPIO 13): right servo, ±550µs range  (950–2050µs)

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
    SERVO1_PIN = 18  # left servo
    SERVO2_PIN = 13  # right servo

    DEFAULT_POS = 1500

    # Servo 1 (GPIO 18) — ±1000µs
    SERVO1_UP = DEFAULT_POS - 1000    # 2500
    SERVO1_DOWN = DEFAULT_POS + 1000  # 500

    # Servo 2 (GPIO 13) — ±550µs
    SERVO2_UP = DEFAULT_POS - 570     # 2050
    SERVO2_DOWN = DEFAULT_POS +  570   # 950

    POLL_INTERVAL = 0.05  # 20 Hz
    RESET_DOWN_DURATION = 2.9

    def __init__(self, device: str):
        self.device = device
        self._direction = "N"
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._reset_requested = threading.Event()
        self._resetting = False

    def stop(self):
        self._stop.set()

    def set_direction(self, direction: str):
        with self._lock:
            if not self._resetting:
                self._direction = direction

    def get_direction(self) -> str:
        with self._lock:
            return self._direction

    def request_reset(self):
        self._reset_requested.set()

    def run(self):
        if self.device == "pi":
            self._run_hardware()
        else:
            self._run_mock()

    def _move(self, pi, pos1: int, pos2: int):
        pi.set_servo_pulsewidth(self.SERVO2_PIN, pos2)
        pi.set_servo_pulsewidth(self.SERVO1_PIN, pos1)

    def _move1(self, pi, pos1: int):
        pi.set_servo_pulsewidth(self.SERVO1_PIN, pos1)

    def _move2(self, pi, pos2: int):
        pi.set_servo_pulsewidth(self.SERVO2_PIN, pos2)

    def _run_hardware(self):
        import pigpio

        pi = pigpio.pi()
        if not pi.connected:
            print("[Servo] Could not connect to pigpio daemon — is pigpiod running?")
            return

        print("[Servo] Connected to pigpio, moving both servos to default position")
        self._move(pi, self.DEFAULT_POS, self.DEFAULT_POS)

        prev = "N"
        try:
            while not self._stop.is_set():
                if self._reset_requested.is_set():
                    self._reset_requested.clear()
                    with self._lock:
                        self._resetting = True
                    print("[Servo] RESET: moving DOWN")
                    self._move1(pi, self.SERVO1_DOWN)
                    self._move2(pi, self.SERVO2_DOWN)
                    
                    time.sleep(self.RESET_DOWN_DURATION)

                    print("[Servo] RESET: returning to DEFAULT")
                    self._move(pi, self.DEFAULT_POS, self.DEFAULT_POS)
                    with self._lock:
                        self._resetting = False
                        self._direction = "N"
                    prev = "N"
                    print("[Servo] RESET complete")
                    continue

                d = self.get_direction()
                if d != prev:
                    if d == "U":
                        self._move1(pi, self.SERVO1_UP)
                        time.sleep(0.3)
                        self._move2(pi, self.SERVO2_UP)
                        print("[Servo] → UP (both)")
                    elif d == "D":
                        self._move2(pi, self.SERVO2_DOWN)
                        time.sleep(0.2)
                        self._move1(pi, self.SERVO1_DOWN)
                        print("[Servo] → DOWN (both)")
                    else:
                        self._move(pi, self.DEFAULT_POS, self.DEFAULT_POS)
                        print("[Servo] → NEUTRAL (both)")
                    prev = d
                time.sleep(self.POLL_INTERVAL)
        finally:
            print("[Servo] Returning to default and releasing pins")
            self._move(pi, self.DEFAULT_POS, self.DEFAULT_POS)
            time.sleep(0.5)
            self._move(pi, 0, 0)
            pi.stop()
            print("[Servo] Stopped")

    def _run_mock(self):
        """Laptop mode — log direction changes without hardware."""
        print("[Servo] Running in mock mode (no hardware, 2 servos)")
        prev = "N"
        while not self._stop.is_set():
            if self._reset_requested.is_set():
                self._reset_requested.clear()
                with self._lock:
                    self._resetting = True
                print(f"[Servo mock] RESET: DOWN for {self.RESET_DOWN_DURATION}s")
                time.sleep(self.RESET_DOWN_DURATION)
                print("[Servo mock] RESET: returning to DEFAULT")
                with self._lock:
                    self._resetting = False
                    self._direction = "N"
                prev = "N"
                print("[Servo mock] RESET complete")
                continue

            d = self.get_direction()
            if d != prev:
                print(f"[Servo mock] → {d} (GPIO {self.SERVO1_PIN} + GPIO {self.SERVO2_PIN})")
                prev = d
            time.sleep(self.POLL_INTERVAL)
        print("[Servo mock] Stopped")
