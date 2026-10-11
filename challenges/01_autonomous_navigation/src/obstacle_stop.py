#!/usr/bin/env python3
"""Exercise 1: reactive obstacle stop (the 'ROS 2 core' checkpoint).

Subscribes /scan, publishes /cmd_vel. Drives forward; if anything is closer than
STOP_DIST in the front cone it turns in place instead. No map, no planner: just
sensor -> decision -> actuator. Run in the TurtleBot3 sim.

    python3 obstacle_stop.py
"""
import math
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist

STOP_DIST = 0.5     # m
FRONT_HALF_ANGLE = math.radians(30)


class ObstacleStop(Node):
    def __init__(self):
        super().__init__("obstacle_stop")
        # Sensor topics are BEST_EFFORT: using the default (RELIABLE) subscriber gives NO data.
        self.create_subscription(LaserScan, "scan", self.on_scan, qos_profile_sensor_data)
        self.pub = self.create_publisher(Twist, "cmd_vel", 10)

    def on_scan(self, msg: LaserScan):
        front = []
        for i, r in enumerate(msg.ranges):
            ang = msg.angle_min + i * msg.angle_increment
            ang = math.atan2(math.sin(ang), math.cos(ang))      # wrap to [-pi, pi]
            if abs(ang) < FRONT_HALF_ANGLE and msg.range_min < r < msg.range_max:
                front.append(r)
        cmd = Twist()
        if front and min(front) < STOP_DIST:
            cmd.angular.z = 0.6          # blocked -> rotate
        else:
            cmd.linear.x = 0.15          # free -> go
        self.pub.publish(cmd)


def main():
    rclpy.init()
    rclpy.spin(ObstacleStop())


if __name__ == "__main__":
    main()
