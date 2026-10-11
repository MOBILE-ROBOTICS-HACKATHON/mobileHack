#!/usr/bin/env python3
"""Step 1 of the sim imitation-learning pipeline: RECORD teleop demonstrations.

Drive the TurtleBot3 in Gazebo with the keyboard/joystick; this node logs
 (downsampled lidar, your cmd_vel) at 10 Hz and saves them to an .npz on Ctrl-C.

    # terminals: sim, teleop (ros2 run teleop_twist_keyboard teleop_twist_keyboard), then:
    python3 record_demos.py --out ../data/demos_run1.npz

IMPORTANT: demonstrations must be CONSISTENT (same behaviour in same situations) and
cover recoveries (drive toward a wall, correct, repeat) otherwise the policy has never
seen the states it drifts into. Aim for 5-10 min of data.
"""
import argparse
import os
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist

N_BINS, MAX_RANGE = 24, 3.5


def lidar_features(ranges):
    """360 rays -> N_BINS min-pooled bins, inf/nan -> MAX_RANGE, scaled to [0,1]."""
    r = np.nan_to_num(np.asarray(ranges, dtype=np.float32), nan=MAX_RANGE, posinf=MAX_RANGE, neginf=0.0)
    r = np.clip(r, 0.0, MAX_RANGE)
    n = (len(r) // N_BINS) * N_BINS
    return r[:n].reshape(N_BINS, -1).min(axis=1) / MAX_RANGE


class Recorder(Node):
    def __init__(self, out):
        super().__init__("record_demos")
        self.out, self.scan, self.cmd = out, None, Twist()
        self.X, self.Y = [], []
        self.create_subscription(LaserScan, "scan", lambda m: setattr(self, "scan", m), qos_profile_sensor_data)
        self.create_subscription(Twist, "cmd_vel", lambda m: setattr(self, "cmd", m), 10)
        self.create_timer(0.1, self.tick)

    def tick(self):
        if self.scan is None:
            return
        self.X.append(lidar_features(self.scan.ranges))
        self.Y.append([self.cmd.linear.x, self.cmd.angular.z])
        if len(self.X) % 50 == 0:
            self.get_logger().info(f"{len(self.X)} samples")

    def save(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.out)), exist_ok=True)
        np.savez(self.out, X=np.array(self.X), Y=np.array(self.Y, dtype=np.float32))
        print(f"saved {len(self.X)} samples -> {self.out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/demos.npz")
    a, _ = ap.parse_known_args()
    rclpy.init()
    node = Recorder(a.out)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.save()


if __name__ == "__main__":
    main()
