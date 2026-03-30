import pigpio
import time

pi = pigpio.pi()
if not pi.connected:
    print("[Servo] Could not connect to pigpio daemon — is pigpiod running?")

SERVO1_PIN = 18  # left servo
SERVO2_PIN = 13  # right servo

DEFAULT_POS = 1500

# Servo 1 (GPIO 18) — ±1000µs
SERVO1_UP = DEFAULT_POS - 1000    # 2500
SERVO1_DOWN = DEFAULT_POS + 1000  # 500

# Servo 2 (GPIO 13) — ±550µs
SERVO2_UP = DEFAULT_POS - 550     # 2050
SERVO2_DOWN = DEFAULT_POS +  550   # 950

def move(pi, pos1: int, pos2: int):
    pi.set_servo_pulsewidth(SERVO2_PIN, pos2)
    pi.set_servo_pulsewidth(SERVO1_PIN, pos1)

move(pi, SERVO1_DOWN, SERVO2_DOWN)

time.sleep(4)

move(pi, DEFAULT_POS, DEFAULT_POS)