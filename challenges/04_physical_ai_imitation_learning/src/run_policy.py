#!/usr/bin/env python3
"""Step 3: DEPLOY the learned policy on the (simulated or real) robot.

 sub: /scan   pub: /cmd_vel   (clamped + watchdog: ALWAYS wrap learned policies in safety code)

    python3 run_policy.py --model ../models/bc_policy.pt
Add --max-v 0.15 for the first real-robot test. Evaluate quantitatively (collisions / minute,
time to complete lap), not by 'looks ok'.
"""
import argparse
import math
import numpy as np
import torch
import torch.nn as nn
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from record_demos import lidar_features   # same preprocessing as training (never duplicate it!)


class PolicyNode(Node):
    def __init__(self, path, max_v, max_w):
        super().__init__("run_policy")
        ck = torch.load(path, map_location="cpu", weights_only=False)
        self.net = nn.Sequential(nn.Linear(ck["in_dim"], 128), nn.ReLU(), nn.Dropout(0.1),
                                 nn.Linear(128, 128), nn.ReLU(), nn.Linear(128, 2))
        self.net.load_state_dict(ck["state"]); self.net.eval()
        self.y_mean, self.y_std = ck["y_mean"], ck["y_std"]
        self.max_v, self.max_w = max_v, max_w
        self.create_subscription(LaserScan, "scan", self.on_scan, qos_profile_sensor_data)
        self.pub = self.create_publisher(Twist, "cmd_vel", 10)

    def on_scan(self, msg):
        x = torch.tensor(lidar_features(msg.ranges)).unsqueeze(0)
        with torch.no_grad():
            v, w = (self.net(x)[0].numpy() * self.y_std + self.y_mean)
        cmd = Twist()
        cmd.linear.x = float(np.clip(v, 0.0, self.max_v))
        cmd.angular.z = float(np.clip(w, -self.max_w, self.max_w))
        if front_min(msg) < 0.2:      # hard safety override
            cmd = Twist()
        self.pub.publish(cmd)


def front_min(msg, half_angle=math.radians(20)):
    """Closest valid range within ±half_angle of straight ahead. Uses angles, not indices:
    TurtleBot scans start at the front (0..2π), the ANT1's start at the rear (-π..π)."""
    r = np.asarray(msg.ranges, dtype=np.float32)
    a = msg.angle_min + np.arange(len(r)) * msg.angle_increment
    front = r[(np.abs(np.arctan2(np.sin(a), np.cos(a))) < half_angle) & (r > msg.range_min) & np.isfinite(r)]
    return float(front.min()) if front.size else math.inf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="models/bc_policy.pt")
    ap.add_argument("--max-v", type=float, default=0.22)
    ap.add_argument("--max-w", type=float, default=1.5)
    a, _ = ap.parse_known_args()
    rclpy.init()
    rclpy.spin(PolicyNode(a.model, a.max_v, a.max_w))


if __name__ == "__main__":
    main()
