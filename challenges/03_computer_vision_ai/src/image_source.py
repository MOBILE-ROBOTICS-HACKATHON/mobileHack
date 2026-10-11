#!/usr/bin/env python3
"""Publish images to /image_raw WITHOUT a robot: webcam, a video file, or a synthetic test pattern.
Lets you develop vision nodes anywhere (laptop with no camera, in Docker, on a train).

    python3 image_source.py                       # synthetic moving shapes (default)
    python3 image_source.py --source 0            # webcam index
    python3 image_source.py --source clip.mp4     # video file (loops)
"""
import argparse
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class ImageSource(Node):
    def __init__(self, source, fps, topic):
        super().__init__("image_source")
        self.pub = self.create_publisher(Image, topic, 10)
        self.bridge = CvBridge()
        self.cap = None
        if source != "synthetic":
            self.cap = cv2.VideoCapture(int(source) if source.isdigit() else source)
            if not self.cap.isOpened():
                raise RuntimeError(f"cannot open {source}")
        self.t = 0
        self.create_timer(1.0 / fps, self.tick)

    def synthetic(self):
        img = np.full((480, 640, 3), 40, np.uint8)
        cx = int(320 + 200 * np.sin(self.t / 30))
        cv2.circle(img, (cx, 240), 50, (0, 0, 255), -1)
        cv2.rectangle(img, (50, 350), (200, 450), (0, 255, 0), -1)
        cv2.putText(img, f"synthetic {self.t}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        return img

    def tick(self):
        if self.cap is None:
            frame = self.synthetic()
        else:
            ok, frame = self.cap.read()
            if not ok:  # loop video
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                return
        self.t += 1
        msg = self.bridge.cv2_to_imgmsg(frame, "bgr8")
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "camera"
        self.pub.publish(msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="synthetic")
    ap.add_argument("--fps", type=float, default=15.0)
    ap.add_argument("--topic", default="image_raw")
    a, _ = ap.parse_known_args()
    rclpy.init()
    rclpy.spin(ImageSource(a.source, a.fps, a.topic))


if __name__ == "__main__":
    main()
