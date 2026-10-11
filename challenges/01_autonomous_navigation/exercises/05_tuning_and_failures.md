# Exercise 5: Tuning and failure modes (hackathon-style stress tests)

Do each, log results in `../experiments/LOG.md` (template below).

1. **Lighting / perception:** (camera-based) darken the Gazebo world; does your vision node still work? Lidar nav is unaffected: why is that a valid design choice?
2. **Feature-poor:** build a long empty corridor in Gazebo; run SLAM; observe drift. Fix: EKF (`robot_localization`) fusing odom+IMU, or AprilTag landmarks.
3. **Dynamic scene:** spawn a moving obstacle (Gazebo model with a `<plugin>` or push a box by hand). Switch controller DWB → MPPI and compare.
4. **Sensor dropout:** `ros2 topic pub` a stale /scan or kill the lidar driver. Your node must stop the robot (add a watchdog).
5. **Latency:** run over a bad network (use `tc qdisc add dev lo root netem delay 100ms`; needs root). Observe control quality. (The hackathon runs a 5G network!)
6. **Speed vs. safety:** find the max speed where the robot reliably avoids a surprise box.

LOG template:
```
## Experiment: <name>
Hypothesis:
Setup (params changed):
Result (numbers, rosbag name):
Lesson:
```
