import cv2
import numpy as np
import socket
import json
import time
import argparse

# Red wraps around in HSV — cover both ends of the hue spectrum
LOWER_RED_1 = np.array([0,   100,  60])
UPPER_RED_1 = np.array([10,  255, 255])
LOWER_RED_2 = np.array([160, 100,  60])
UPPER_RED_2 = np.array([179, 255, 255])

current_frame = None
origin_center = None

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
TARGET = ("127.0.0.1", 5005)


def on_click(event, x, y, flags, param):
    """Click to recalibrate the red HSV range around the clicked pixel."""
    global LOWER_RED_1, UPPER_RED_1, LOWER_RED_2, UPPER_RED_2
    global current_frame, origin_center

    if event == cv2.EVENT_LBUTTONDOWN:
        if current_frame is None:
            return

        hsv = cv2.cvtColor(current_frame, cv2.COLOR_BGR2HSV)
        pixel = hsv[y, x]
        h, s, v = int(pixel[0]), int(pixel[1]), int(pixel[2])

        # Generous hue tolerance for red (±20), and looser S/V for varied lighting
        H_TOL, S_TOL, V_TOL = 20, 80, 80

        h_lo = h - H_TOL
        h_hi = h + H_TOL

        if h_lo < 0:
            # Wraps into the upper red range
            LOWER_RED_1 = np.array([0,              max(s - S_TOL, 0),   max(v - V_TOL, 0)])
            UPPER_RED_1 = np.array([h_hi,           min(s + S_TOL, 255), min(v + V_TOL, 255)])
            LOWER_RED_2 = np.array([180 + h_lo,     max(s - S_TOL, 0),   max(v - V_TOL, 0)])
            UPPER_RED_2 = np.array([179,             min(s + S_TOL, 255), min(v + V_TOL, 255)])
        elif h_hi > 179:
            # Wraps into the lower red range
            LOWER_RED_1 = np.array([h_lo,           max(s - S_TOL, 0),   max(v - V_TOL, 0)])
            UPPER_RED_1 = np.array([179,             min(s + S_TOL, 255), min(v + V_TOL, 255)])
            LOWER_RED_2 = np.array([0,              max(s - S_TOL, 0),   max(v - V_TOL, 0)])
            UPPER_RED_2 = np.array([h_hi - 180,     min(s + S_TOL, 255), min(v + V_TOL, 255)])
        else:
            # No wrap — non-red click, still adapt gracefully
            LOWER_RED_1 = np.array([max(h_lo, 0),   max(s - S_TOL, 0),   max(v - V_TOL, 0)])
            UPPER_RED_1 = np.array([min(h_hi, 179),  min(s + S_TOL, 255), min(v + V_TOL, 255)])
            LOWER_RED_2 = LOWER_RED_1.copy()
            UPPER_RED_2 = UPPER_RED_1.copy()

        print(f"Clicked HSV: {pixel}")
        print(f"LOWER_RED_1={LOWER_RED_1}  UPPER_RED_1={UPPER_RED_1}")
        print(f"LOWER_RED_2={LOWER_RED_2}  UPPER_RED_2={UPPER_RED_2}\n")

        origin_center = None  # Reset origin on recalibrate


def build_red_mask(hsv):
    """Combine both red hue bands into a single cleaned-up mask."""
    mask1 = cv2.inRange(hsv, LOWER_RED_1, UPPER_RED_1)
    mask2 = cv2.inRange(hsv, LOWER_RED_2, UPPER_RED_2)
    mask = cv2.bitwise_or(mask1, mask2)

    # Remove speckle noise, then fill gaps inside the blob
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.erode(mask,  kernel, iterations=2)
    mask = cv2.dilate(mask, kernel, iterations=3)   # slight over-dilate to bridge gaps
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)  # fill holes

    return mask


def circularity(contour):
    """Return circularity score [0–1]. 1.0 = perfect circle."""
    area = cv2.contourArea(contour)
    if area == 0:
        return 0
    perimeter = cv2.arcLength(contour, True)
    if perimeter == 0:
        return 0
    return (4 * np.pi * area) / (perimeter ** 2)


def best_red_contour(contours, min_area=300, min_circularity=0.35):
    """
    Pick the most circle-like red blob.
    Filters by minimum area and circularity, then scores by
    (area * circularity) so big round blobs win.
    """
    candidates = [
        c for c in contours
        if cv2.contourArea(c) >= min_area and circularity(c) >= min_circularity
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda c: cv2.contourArea(c) * circularity(c))


def create_camera(device):
    if device == "pi":
        from picamera2 import Picamera2
        picam2 = Picamera2()
        picam2.configure(
            picam2.create_video_configuration(
                main={"size": (640, 480), "format": "RGB888"}
            )
        )
        picam2.start()
        return lambda: (True, picam2.capture_array()), picam2.stop

    cap = cv2.VideoCapture(0)
    return cap.read, cap.release


def main(device):
    global current_frame, origin_center

    read_frame, release_camera = create_camera(device)

    cv2.namedWindow("Tracking")
    cv2.setMouseCallback("Tracking", on_click)

    dx = dy = 0

    while True:
        ret, frame = read_frame()
        if not ret:
            print("Cannot read from camera.")
            break

        frame = cv2.flip(frame, 1)
        current_frame = frame.copy()

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = build_red_mask(hsv)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        c = best_red_contour(contours)

        if c is not None:
            M = cv2.moments(c)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])

                # Draw contour outline + centre dot in green (keeping your style)
                cv2.drawContours(frame, [c], -1, (0, 255, 0), 2)
                cv2.circle(frame, (cx, cy), 6, (0, 255, 0), -1)

                # Also draw the fitted enclosing circle so you can see how round it looks
                (ex, ey), er = cv2.minEnclosingCircle(c)
                cv2.circle(frame, (int(ex), int(ey)), int(er), (0, 200, 255), 1)

                if origin_center is None:
                    origin_center = (cx, cy)

                dx = cx - origin_center[0]
                dy = cy - origin_center[1]

        cv2.putText(frame, f"dx: {dx}  dy: {dy}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

        sock.sendto(json.dumps({"dx": dx, "dy": -dy, "timestamp": time.time()}).encode(), TARGET)

        cv2.imshow("Tracking", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    release_camera()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", choices=["laptop", "pi"], default="laptop")
    args = parser.parse_args()
    main(args.device)