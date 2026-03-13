import cv2
import numpy as np
import socket
import json
import time
import argparse

lower_hsv = np.array([0, 120, 70])
upper_hsv = np.array([10, 255, 255])

current_frame = None
origin_center = None

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
TARGET = ("127.0.0.1", 5005)


def on_click(event, x, y, flags, param):
    global lower_hsv, upper_hsv, current_frame, origin_center

    if event == cv2.EVENT_LBUTTONDOWN:
        if current_frame is None:
            return

        hsv = cv2.cvtColor(current_frame, cv2.COLOR_BGR2HSV)
        pixel = hsv[y, x]

        h, s, v = int(pixel[0]), int(pixel[1]), int(pixel[2])

        lower_hsv = np.array([max(h - 10, 0), max(s - 60, 0), max(v - 60, 0)])
        upper_hsv = np.array([min(h + 10, 179), min(s + 60, 255), min(v + 60, 255)])

        print("Clicked HSV:", pixel)
        print("lower_hsv =", lower_hsv)
        print("upper_hsv =", upper_hsv)
        print()

        origin_center = None


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

        def read():
            frame = picam2.capture_array()
            return True, frame

        def release():
            picam2.stop()

        return read, release

    else:  # laptop webcam
        cap = cv2.VideoCapture(-1)

        def read():
            return cap.read()

        def release():
            cap.release()

        return read, release


def main(device):

    global current_frame, origin_center

    read_frame, release_camera = create_camera(device)

    cv2.namedWindow("Tracking")
    cv2.setMouseCallback("Tracking", on_click)

    dx = 0
    dy = 0

    while True:

        ret, frame = read_frame()

        if not ret:
            print("Cannot read from camera.")
            break

        frame = cv2.flip(frame, 1)
        current_frame = frame.copy()

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower_hsv, upper_hsv)

        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            c = max(contours, key=cv2.contourArea)
            M = cv2.moments(c)

            cv2.drawContours(frame, [c], -1, (0, 255, 0), 2)

            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])

                center = (cx, cy)
                cv2.circle(frame, center, 6, (0, 255, 0), -1)

                if origin_center is None:
                    origin_center = (cx, cy)

                dx = cx - origin_center[0]
                dy = cy - origin_center[1]

        text = f"dx: {dx}, dy: {dy}"
        cv2.putText(frame, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (0, 255, 0), 2)

        data = {
            "dx": dx,
            "dy": -dy,
            "timestamp": time.time()
        }

        sock.sendto(json.dumps(data).encode(), TARGET)

        cv2.imshow("Tracking", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    release_camera()
    cv2.destroyAllWindows()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--device",
        choices=["laptop", "pi"],
        default="laptop",
        help="Choose camera device"
    )

    args = parser.parse_args()

    main(args.device)