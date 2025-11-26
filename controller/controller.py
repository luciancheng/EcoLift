import socket
import json
import time
import matplotlib.pyplot as plt
from collections import deque

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("127.0.0.1", 5005))

print("Listening...")

FAILURE_Y_THRESHOLD = -300          # abirtrary y position to determine failure
STALL_VEL_THRESHOLD = 20         # if speed < this = stalling
STALL_TIME = 2                 # seconds of stall to consider failure
ASSIST_Y_THRESHOLD = -10
VEL_SMOOTHING_ALPHA = 0.2

RAMP_UP_RATE = 0.25               # per second (when assisting)
RAMP_DOWN_RATE = 0.4              # per second back to 0 when not assisting

# State
u = 0.0                           # assistance output (0–1)
last_time = time.time()

prev_dx = None
prev_dy = None
smoothed_vel = None    
last_motion_time = time.time()
last_time_above_threshold = time.time()
start_help = False

print("Control system online...")

# plot
WINDOW_SECONDS = 10

time_buffer = deque(maxlen=1000)
dy_buffer = deque(maxlen=1000)
u_buffer  = deque(maxlen=1000)

# Set up the live plot
plt.ion()
fig, ax = plt.subplots(2, 1, figsize=(10, 6))

ax_dy = ax[0]
ax_u = ax[1]

# Add horizontal reference lines
ax_dy.axhline(0, color="gray", linestyle="--", linewidth=1)
ax_dy.axhline(FAILURE_Y_THRESHOLD, color="red", linestyle="--", linewidth=1)

ax_dy.set_title("Bar Height (dy) — Last 10 seconds")
ax_u.set_title("Assistance (u) — Last 10 seconds")

ax_dy.set_xlabel("Time (s)")
ax_dy.set_ylabel("dy")

ax_u.set_xlabel("Time (s)")
ax_u.set_ylabel("u (0–1)")

line_dy, = ax_dy.plot([], [], linewidth=2)
line_u,  = ax_u.plot([], [], linewidth=2)

plt.tight_layout()
plt.show()

while True:
    msg, addr = sock.recvfrom(4096)
    data = json.loads(msg.decode())

    dx = data.get("dx", 0.0)
    dy = data.get("dy", 0.0)
    timestamp = data.get("timestamp", 0.0)

    t = time.time()
    dt = t - last_time
    last_time = t

    if prev_dx is None:
        # First iteration
        prev_dx, prev_dy = dx, dy
        continue

    ddx = dx - prev_dx
    ddy = dy - prev_dy

    # Velocity - only care about y velocity
    safe_dt = max(dt, 1e-6)
    vel = ddy / safe_dt  # y-velocity, can be negative
    speed = abs(vel)
    raw_vel = ddy / safe_dt  # y-velocity, can be negative

    if smoothed_vel is None:
        smoothed_vel = raw_vel
    else:
        # Smooth the velocity using an exponential moving average
        smoothed_vel = (VEL_SMOOTHING_ALPHA * raw_vel) + ((1 - VEL_SMOOTHING_ALPHA) * smoothed_vel)

    vel = smoothed_vel
    speed = abs(vel)

    prev_dx = dx
    prev_dy = dy

    if speed > STALL_VEL_THRESHOLD:
        last_motion_time = t

    if dy > FAILURE_Y_THRESHOLD:
        last_time_above_threshold = t

    stalled = (t - last_motion_time) > STALL_TIME

    fail_pos = (dy < FAILURE_Y_THRESHOLD) and (t - last_time_above_threshold) > STALL_TIME
    fail_stall = stalled

    failure_detected = fail_pos or fail_stall

    # help them up fully if failure is detected
    if failure_detected:
        start_help = True
    
    if start_help:
        if speed < STALL_VEL_THRESHOLD:
            # Not moving → slowly increase assistance
            u += RAMP_UP_RATE * dt
        else:
            # Moving a bit → hold assistance
            u = u

        if dy > ASSIST_Y_THRESHOLD:
            start_help = False
    else:
        # No failure → remove assistance slowly
        u -= RAMP_DOWN_RATE * dt

    # Clamp
    u = max(0.0, min(1.0, u))

    status = {
        "u": round(u, 3),
        "vel": round(vel, 4),
        "y": round(dy, 2),
        "failure": failure_detected,
        "stalled": stalled
    }

    time_buffer.append(t)
    dy_buffer.append(dy)
    u_buffer.append(u)

    # Trim to last 10 seconds
    while len(time_buffer) > 1 and (time_buffer[-1] - time_buffer[0]) > WINDOW_SECONDS:
        time_buffer.popleft()
        dy_buffer.popleft()
        u_buffer.popleft()

    # --- Update plot ---
    if len(time_buffer) > 2:
        line_dy.set_data(time_buffer, dy_buffer)
        line_u.set_data(time_buffer, u_buffer)

        ax_dy.set_xlim(time_buffer[0], time_buffer[-1])
        ax_u.set_xlim(time_buffer[0], time_buffer[-1])

        # Auto-scale Y
        ax_dy.set_ylim(-500, 100)
        ax_u.set_ylim(0, 1)

        plt.pause(0.001)


    print(
        f"u: {u:5.3f} \t vel: {vel:9.4f} \t y: {dy:8.2f} \t "
        f"failure: {str(failure_detected):<5} \t stalled: {str(stalled):<5}  \t helping: {start_help} ",
        end="\r", flush=True)