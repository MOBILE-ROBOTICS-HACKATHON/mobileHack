#!/usr/bin/env python3
"""Exercise 5: goal-to-pose navigator with a hand-written P-controller (no Nav2).

Subscribes to /odom, drives to (GOAL_X, GOAL_Y) with a proportional controller on
distance and heading error. Teaches frames + odometry + control; also the baseline
to understand what Nav2's local planner does for you.

    python3 go_to_goal.py --x 1.0 --y 1.0
"""
import argparse
import math
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist


def yaw_from_quat(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


class GoToGoal(Node):
    def __init__(self, gx, gy):
        super().__init__("go_to_goal")
        self.gx, self.gy = gx, gy
        self.create_subscription(Odometry, "odom", self.on_odom, 10)
        self.pub = self.create_publisher(Twist, "cmd_vel", 10)

    def on_odom(self, msg: Odometry):
        p = msg.pose.pose.position
        yaw = yaw_from_quat(msg.pose.pose.orientation)
        dx, dy = self.gx - p.x, self.gy - p.y
        dist = math.hypot(dx, dy)
        err = math.atan2(math.sin(math.atan2(dy, dx) - yaw), math.cos(math.atan2(dy, dx) - yaw))
        cmd = Twist()
        if dist > 0.08:
            # slow down when pointing the wrong way, cap speeds (safety!)
            cmd.angular.z = max(-1.0, min(1.0, 1.5 * err))
            cmd.linear.x = min(0.22, 0.5 * dist) * max(0.0, math.cos(err))
        else:
            self.get_logger().info("goal reached")
        self.pub.publish(cmd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--x", type=float, default=1.0)
    ap.add_argument("--y", type=float, default=0.0)
    a, _ = ap.parse_known_args()
    rclpy.init()
    rclpy.spin(GoToGoal(a.x, a.y))


if __name__ == "__main__":
    main()
