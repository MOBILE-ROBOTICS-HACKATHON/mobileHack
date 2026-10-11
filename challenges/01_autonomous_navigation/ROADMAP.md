# Challenge 01: Autonomous Navigation (RouteMaster · PathQuest)

> Brief: navigation stack that guides a drone / AGV / rover through waypoints using onboard perception.
> Localize, plan, execute collision-free trajectories in changing light, feature-poor spaces and dynamic scenes.

**Likely hardware on the day:** TurtleBot3, Clearpath Jackal, Olive ANT, ROSbot XL, Robomaster EP, Spot, Crazyflie.
Ground robots use **2D lidar + Nav2** (cheapest path to a working demo). Drones need VIO/Lighthouse: harder, so avoid unless your team has drone experience.

## The mental model (learn this in 30 min)
```
sensors (lidar, camera, IMU, wheel odom)
   │
   ▼  localization / SLAM  ──►  TF:  map → odom → base_link → laser
   │
   ▼  global planner (NavFn / Smac)  ──►  path on the costmap
   │
   ▼  local controller (DWB / MPPI / RPP)  ──►  /cmd_vel   (what the robot actually runs)
   │
   ▼  recovery behaviours (spin, back up, clear costmap)  ◄── Behavior Tree (bt_navigator) orchestrates all of this
```
- `odom` frame: smooth but drifts. `map` frame: globally correct but can jump. `map→odom` is the localization correction.
- Costmap = occupancy grid + inflation around obstacles. Most "robot won't move" bugs are costmap/TF bugs.

## Study order (≈8 h total)
| # | Time | What | Where |
|---|---|---|---|
| 1 | 1.0h | Sim + teleop + reactive obstacle stop | `exercises/01_sim_and_reactive.md`, `src/obstacle_stop.py` |
| 2 | 1.0h | TF2 + odometry + P-controller go-to-goal | `exercises/02_tf_odom.md`, `src/go_to_goal.py` |
| 3 | 1.5h | SLAM: build and save a map | `exercises/03_slam.md` |
| 4 | 1.5h | Nav2: localize + send goals in rviz | `exercises/04_nav2.md` |
| 5 | 1.0h | Nav2 from Python: waypoint patrol | `src/waypoint_patrol.py` |
| 6 | 1.0h | Tune params, dynamic obstacles, failure modes | `exercises/05_tuning_and_failures.md` |
| 7 | 1.0h | Real-robot adaptation checklist | below |

## Theory to skim (just enough)
- Differential-drive kinematics: `v, ω → wheel speeds`; `x' = v cosθ, y' = v sinθ, θ' = ω`.
- Occupancy grids; AMCL = particle filter on the map; SLAM = build map + localize simultaneously (graph-based in `slam_toolbox`).
- A*/Dijkstra for global plans; DWA / MPPI for local control (sample velocity commands, score by goal progress/clearance).
- EKF fusion (`robot_localization`): wheel odom + IMU → better `odom`. Useful when wheels slip.
- Read: Nav2 docs → "Concepts", "Setup Guides → Odometry/SLAM", "Configuration Guide".

## Hackathon strategy for this track
**What judges can see in 5 min:** robot autonomously completes a multi-waypoint mission, avoids a surprise obstacle, shows rviz with map/path/costmap.
1. **Hour 0–2:** get the robot driving via `cmd_vel` + `/scan` visible in rviz. Identify real topic names (`ros2 topic list`) and the frame names (`ros2 run tf2_tools view_frames`).
2. **Hour 2–5:** map the arena with slam_toolbox (drive slowly!). Save the map.
3. **Hour 5–8:** bring up Nav2 with that map; adjust `robot_radius`, max speeds, `inflation_radius` to the real robot.
4. **Hour 8+:** the "twist" = your differentiator: e.g. semantic goals ("go to the red box" using Challenge 03), mission UI, multi-waypoint logistics task, recovery when blocked.
5. Always keep a **record** running: `ros2 bag record -a -o run1` so you can debug offline.

### Real-robot adaptation checklist
- [ ] Same `ROS_DOMAIN_ID` / DDS as the robot (CycloneDDS vs FastDDS mismatch = "can't see topics").
- [ ] Topic names: `/scan`, `/odom`, `/cmd_vel` may be namespaced or renamed → use launch remaps.
- [ ] Is `use_sim_time` **false** on the real robot? (true only in Gazebo)
- [ ] Footprint/robot radius in `nav2_params.yaml` matches the robot.
- [ ] Cap velocities (`max_vel_x ≤ 0.3 m/s` for first tests). Keep e-stop in hand.
- [ ] Lidar frame in TF (`base_link → laser`) published? check `view_frames`.
- [ ] Feature-poor corridor? Lidar SLAM degrades; rely on wheel odom + IMU EKF, or add AprilTags as landmarks.

## Stretch ideas (differentiators)
- AprilTag-assisted relocalization (`ros-humble-apriltag-ros`): tags at known map positions fix drift.
- Navigate to detected objects (fuse with Challenge 03: detection → 3D point → `NavigateToPose`).
- Dynamic obstacle handling: human walking → test costmap `obstacle_layer` clearing & MPPI controller.
- Learned local planner trained from your own demos (fuse with Challenge 04).

## Folder layout
```
src/          runnable Python (obstacle_stop, go_to_goal, waypoint_patrol)
exercises/    step-by-step guides with commands + questions to answer
experiments/  YOUR notebook: copy a script, break it, write what you learned in LOG.md
maps/         saved SLAM maps
```
