#!/usr/bin/env python3
"""Visual servoing: turn toward / approach a detected object (closes the perception→action loop).

 sub: detections (JSON from yolo_node.py)   pub: cmd_vel

Angular velocity ∝ horizontal pixel error; forward speed ∝ how small the box is (far away),
stopping when the box fills TARGET_FILL of the image width. Pure proportional control, a good
base for 'robot follows the person/cup' demos.

    python3 follow_object.py --label person
    python3 follow_object.py --label "sports ball"
"""
import argparse
import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist


class Follow(Node):
    def __init__(self, label):
        super().__init__("follow_object")
        self.label = label
        self.create_subscription(String, "detections", self.on_det, 10)
        self.pub = self.create_publisher(Twist, "cmd_vel", 10)
        self.last = self.get_clock().now()
        self.create_timer(0.2, self.watchdog)

    def on_det(self, msg):
        dets = [d for d in json.loads(msg.data) if d["label"] == self.label]
        if not dets:
            return
        d = max(dets, key=lambda d: d["conf"])
        self.last = self.get_clock().now()
        w = d["img_w"]
        err = (d["center"][0] - w / 2) / (w / 2)               # -1 (left) .. +1 (right)
        fill = (d["bbox"][2] - d["bbox"][0]) / w               # box width / image width
        cmd = Twist()
        cmd.angular.z = max(-1.0, min(1.0, -0.8 * err))        # image right -> turn right (negative z)
        cmd.linear.x = 0.0 if fill > 0.5 else min(0.2, 0.4 * (0.5 - fill))
        self.pub.publish(cmd)

    def watchdog(self):    # safety: no target for 0.5 s -> stop
        if (self.get_clock().now() - self.last).nanoseconds > 5e8:
            self.pub.publish(Twist())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="person")
    a, _ = ap.parse_known_args()
    rclpy.init()
    rclpy.spin(Follow(a.label))


if __name__ == "__main__":
    main()
