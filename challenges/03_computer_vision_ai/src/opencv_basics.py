#!/usr/bin/env python3
"""Classical CV in 60 lines: colour segmentation + contours + camera geometry.
Often beats a neural net for hackathon demos (coloured cube, tape line, marker) and runs instantly.

    python3 opencv_basics.py --image test.jpg      # or no args -> synthetic image
Experiment: change HSV range to track other colours, print pixel->bearing angle.
"""
import argparse
import math
import cv2
import numpy as np

# --- camera model: pixel -> bearing angle. horizontal FOV of the TB3 waffle camera ~ 1.085 rad (62 deg)
HFOV = 1.085


def pixel_to_bearing(u, width, hfov=HFOV):
    fx = (width / 2) / math.tan(hfov / 2)       # focal length in pixels
    return math.atan2(u - width / 2, fx)        # + = right of centre


def find_red(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # red wraps around hue 0 -> two ranges
    m = cv2.inRange(hsv, (0, 120, 70), (10, 255, 255)) | cv2.inRange(hsv, (170, 120, 70), (180, 255, 255))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return m, [c for c in cnts if cv2.contourArea(c) > 200]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image")
    a = ap.parse_args()
    if a.image:
        img = cv2.imread(a.image)
    else:
        img = np.full((480, 640, 3), 40, np.uint8)
        cv2.circle(img, (450, 240), 50, (0, 0, 255), -1)
    mask, cnts = find_red(img)
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        u = x + w / 2
        print(f"red blob area={cv2.contourArea(c):.0f} centre_u={u:.0f} bearing={math.degrees(pixel_to_bearing(u, img.shape[1])):.1f} deg")
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.imwrite("opencv_out.png", np.hstack([img, cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)]))
    print("wrote opencv_out.png")


if __name__ == "__main__":
    main()
