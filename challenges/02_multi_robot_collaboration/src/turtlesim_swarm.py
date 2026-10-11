#!/usr/bin/env python3
"""Multi-robot coordination playground using turtlesim (zero hardware, zero Gazebo).

Spawns N turtles, runs a decentralised controller on each (every robot only uses the poses of the
others, like a real fleet over the network) with:
   - formation keeping (consensus on a circle formation around a moving leader/centroid)
   - collision avoidance (repulsion if closer than SAFE)
This is the same algorithm structure you'd use with namespaced real robots: /robotN/cmd_vel, /robotN/pose.

    # terminal 1
    ros2 run turtlesim turtlesim_node
    # terminal 2
    python3 turtlesim_swarm.py --n 4 --mode formation      # or: --mode rendezvous
"""
import argparse
import math
import rclpy
from rclpy.node import Node
from turtlesim.msg import Pose
from turtlesim.srv import Spawn, Kill
from geometry_msgs.msg import Twist

SAFE = 1.0


class Swarm(Node):
    def __init__(self, n, mode):
        super().__init__("turtlesim_swarm")
        self.n, self.mode = n, mode
        self.names = [f"t{i}" for i in range(n)]
        self.poses = {}
        self.pubs = {}
        spawn = self.create_client(Spawn, "spawn")
        kill = self.create_client(Kill, "kill")
        spawn.wait_for_service()
        kill.call_async(Kill.Request(name="turtle1"))
        for i, name in enumerate(self.names):
            req = Spawn.Request(x=1.0 + 9.0 * ((i * 0.37) % 1), y=1.0 + 9.0 * ((i * 0.61) % 1), theta=0.0, name=name)
            spawn.call_async(req)
            self.pubs[name] = self.create_publisher(Twist, f"/{name}/cmd_vel", 10)
            self.create_subscription(Pose, f"/{name}/pose", lambda m, nm=name: self.poses.__setitem__(nm, m), 10)
        self.t = 0.0
        self.create_timer(0.05, self.step)

    def step(self):
        if len(self.poses) < self.n:
            return
        self.t += 0.05
        cx = sum(p.x for p in self.poses.values()) / self.n
        cy = sum(p.y for p in self.poses.values()) / self.n
        for i, name in enumerate(self.names):
            p = self.poses[name]
            if self.mode == "formation":   # circle of radius 2 around the (static) arena centre, rotating slowly
                ang = 2 * math.pi * i / self.n + 0.3 * self.t
                tx, ty = 5.5 + 2.0 * math.cos(ang), 5.5 + 2.0 * math.sin(ang)
            else:                          # rendezvous at the centroid
                tx, ty = cx, cy
            vx, vy = 1.5 * (tx - p.x), 1.5 * (ty - p.y)
            for other, q in self.poses.items():     # collision avoidance
                if other == name:
                    continue
                d = math.hypot(p.x - q.x, p.y - q.y)
                if 0 < d < SAFE:
                    k = (SAFE - d) / d * 4.0
                    vx += (p.x - q.x) * k
                    vy += (p.y - q.y) * k
            # unicycle conversion: heading error -> angular, forward speed shrinks with error
            des = math.atan2(vy, vx)
            err = math.atan2(math.sin(des - p.theta), math.cos(des - p.theta))
            cmd = Twist()
            cmd.angular.z = 4.0 * err
            cmd.linear.x = min(2.0, math.hypot(vx, vy)) * max(0.0, math.cos(err))
            self.pubs[name].publish(cmd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--mode", choices=["formation", "rendezvous"], default="formation")
    a, _ = ap.parse_known_args()
    rclpy.init()
    rclpy.spin(Swarm(a.n, a.mode))


if __name__ == "__main__":
    main()
