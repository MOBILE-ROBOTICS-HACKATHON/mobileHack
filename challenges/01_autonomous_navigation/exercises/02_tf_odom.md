# Exercise 2: TF2, odometry and control

```bash
ros2 run tf2_tools view_frames            # creates frames.pdf; open it
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 topic echo /odom --field pose.pose
```
Understand: `odom → base_footprint → base_link → base_scan`. Gazebo publishes `odom`; there is **no `map` frame yet** (SLAM/AMCL adds it).

## Run the P-controller
```bash
python3 challenges/01_autonomous_navigation/src/go_to_goal.py --x 1.0 --y 1.0
```
Tasks:
1. Plot the path: `ros2 bag record /odom -o ../experiments/p_ctrl`, then plot x/y with matplotlib.
2. Tune the gains (1.5 and 0.5). What happens when angular gain is too high? (oscillation)
3. Drive to the goal, then restart the sim without resetting the node. Why is the goal "wrong"? (odom resets → frames matter)
4. Extension: combine with `obstacle_stop.py` logic (simple potential-field avoidance).

Key concept: **odometry drifts**. Drive a 2 m square, return to start, measure error. That is why you need SLAM/localization.
