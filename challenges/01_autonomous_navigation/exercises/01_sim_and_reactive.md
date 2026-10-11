# Exercise 1: Simulation, teleop, reactive stop

Open 3 terminals: `./docker/run.sh` (first), then `./docker/exec.sh` for the others.

**T1: simulator**
```bash
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```
(GUI is slow in software rendering? Use headless: `ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py gui:=false` and view with rviz.)

**T2: rviz**
```bash
rviz2     # Fixed Frame = odom; Add > LaserScan (/scan), Add > TF, Add > RobotModel (needs robot_description)
```

**T3: teleop**
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## Inspect (answer in experiments/LOG.md)
```bash
ros2 topic list -t
ros2 topic hz /scan ; ros2 topic echo /odom --once
ros2 topic info /scan -v        # note the QoS profile: reliability?
ros2 interface show sensor_msgs/msg/LaserScan
```
Q1. What rate is `/scan`? What are `angle_min`, `angle_increment`, `range_max`?
Q2. Why does a `RELIABLE` subscriber on `/scan` get nothing? (change `qos_profile_sensor_data` to `10` in the script and see)

## Run the reactive node
```bash
python3 challenges/01_autonomous_navigation/src/obstacle_stop.py
```
Tasks: (a) make it follow walls on the right; (b) add a deadman: stop if no scan for 0.5 s; (c) clamp speeds.
