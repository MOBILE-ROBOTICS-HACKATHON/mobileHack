#!/usr/bin/env python3
"""Exercise 4: send waypoints to Nav2 from Python (nav2_simple_commander).

Prereq: Nav2 running with a map and the robot localized (see exercises/03_nav2.md).
Edit WAYPOINTS (map frame, metres). In the turtlebot3_world map, these are free space.

    python3 waypoint_patrol.py            # one lap
    python3 waypoint_patrol.py --loops 3  # patrol
"""
import argparse
import math
import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

WAYPOINTS = [  # (x, y, yaw_deg)
    (1.5, 0.5, 0),
    (1.5, -1.0, -90),
    (-1.0, -1.0, 180),
    (-1.0, 0.5, 90),
]


def make_pose(nav, x, y, yaw_deg):
    p = PoseStamped()
    p.header.frame_id = "map"
    p.header.stamp = nav.get_clock().now().to_msg()
    p.pose.position.x, p.pose.position.y = float(x), float(y)
    yaw = math.radians(yaw_deg)
    p.pose.orientation.z, p.pose.orientation.w = math.sin(yaw / 2), math.cos(yaw / 2)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loops", type=int, default=1)
    args = ap.parse_args()

    rclpy.init()
    nav = BasicNavigator()
    # Pass the initial pose (matches the spawn position of turtlebot3_world), then wait for Nav2.
    nav.setInitialPose(make_pose(nav, -2.0, -0.5, 0))
    nav.waitUntilNav2Active()

    for lap in range(args.loops):
        nav.followWaypoints([make_pose(nav, *w) for w in WAYPOINTS])
        while not nav.isTaskComplete():
            fb = nav.getFeedback()
            if fb:
                print(f"lap {lap + 1}: heading to waypoint {fb.current_waypoint + 1}/{len(WAYPOINTS)}", end="\r")
        result = nav.getResult()
        print(f"\nlap {lap + 1} result: {result}")
        if result != TaskResult.SUCCEEDED:
            break
    nav.lifecycleShutdown()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
