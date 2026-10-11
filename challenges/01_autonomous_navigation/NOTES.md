# NOTES: Challenge 01 · Autonomous Navigation (RouteMaster · PathQuest)

Read this file top to bottom for the complete picture. Hands-on steps are in `exercises/`, the plan in `ROADMAP.md`.

## 1. The challenge in plain words
Make a robot (ground robot, rover or drone) **know where it is, decide a route, and drive it without hitting anything** using its own sensors. The organisers hint at hard conditions: **changing lighting, feature-poor spaces (long empty corridors), dynamic scenes (people moving)**. Judges want to see reliability under those conditions, not only a pretty path.

Likely robots: TurtleBot3, ROSbot XL, Clearpath Jackal, Olive ANT, Robomaster EP (ground, lidar); Spot (legged); Crazyflie/PX4 drones (much harder: no wheel odometry, need VIO or Lighthouse). **Recommendation: use a ground robot with a 2D lidar.** It is by far the fastest path to a working demo.

## 2. Concepts you must understand
**Localization**: estimating the robot pose (x, y, yaw) in a frame.
- *Odometry*: integrate wheel encoders (+ IMU). Smooth, but errors accumulate (**drift**).
- *Map-based localization (AMCL)*: particle filter comparing the lidar scan to a known map; corrects drift.
- *SLAM*: build the map **while** localizing (slam_toolbox = graph-based SLAM with loop closure).
- *Feature-poor environments*: a long featureless corridor looks the same at every metre, so scan matching can't tell how far you moved → map "stretches". Mitigations: fuse wheel odom + IMU with an EKF; use landmarks (AprilTags); add features (boxes) to the environment; drive slowly.

**Mapping**: *occupancy grid*: a 2D image; each cell is free/occupied/unknown (`.pgm` + `.yaml` with resolution and origin).

**Planning**
- *Global planner* (NavFn, Smac): finds a path on the **global costmap** from A to B (A*/Dijkstra/lattice).
- *Local controller* (DWB, RPP, MPPI): follows the path while reacting to nearby obstacles on the **local costmap**; outputs `cmd_vel`. MPPI samples thousands of trajectories per cycle and picks the best; handles dynamic obstacles better than DWB.
- *Costmap*: occupancy grid + **inflation** (cost grows near obstacles so the robot keeps distance). Layers: static map, obstacle (from sensors), inflation.
- *Behavior tree* (`bt_navigator`): orchestrates "plan → follow → if stuck: clear costmap, spin, back up".
- *Recovery behaviors*: spin, back up, wait, clear costmaps.

**Control basics**: differential drive: command `v` (m/s) and `ω` (rad/s). `go_to_goal.py` shows a proportional controller on distance/heading error.

**Frames** (see `docs/01_ROS2_FOUNDATIONS.md` §3): `map → odom → base_link → laser`. Most Nav2 failures are frame or time problems.

## 3. Packages: what each does
| Package (in the image) | Role |
|---|---|
| `navigation2` + `nav2_bringup` | The whole Nav2 stack: planners, controllers, costmaps, BT navigator, lifecycle manager, map server, AMCL |
| `nav2_simple_commander` | Python API: `BasicNavigator.goToPose / followWaypoints / waitUntilNav2Active` (used by `waypoint_patrol.py`) |
| `slam_toolbox` | Online SLAM (`online_async_launch.py`), map serialisation, localization-only mode |
| `robot_localization` | EKF/UKF to fuse odometry, IMU, other pose sources → better `odom` |
| `nav2_map_server` | `map_saver_cli` saves maps; `map_server` serves them |
| `turtlebot3_gazebo` / `turtlebot3_navigation2` / `turtlebot3_cartographer` | Simulated robot + world, ready-made Nav2 and Cartographer configs: your practice robot |
| `gazebo_ros_pkgs` | Gazebo ↔ ROS bridge |
| `teleop_twist_keyboard` | Drive manually (mapping, data collection) |
| `tf2_tools`, `tf_transformations` | Inspect frames; quaternion ↔ euler helpers |
| `apriltag_ros` | Detect tags → poses (landmark relocalization) |
| `rviz2` | See the map, scans, costmaps, plans, particles; send goals |

## 4. The code in `src/`
| File | What it teaches | Run |
|---|---|---|
| `obstacle_stop.py` | sensor → decision → actuator; QoS for sensors; angle handling | `python3 src/obstacle_stop.py` (sim running) |
| `go_to_goal.py` | odometry, yaw from quaternion, P-control, speed clamps | `python3 src/go_to_goal.py --x 1 --y 1` |
| `waypoint_patrol.py` | Nav2 from Python, initial pose, waypoint following, result handling | after Nav2 is up |

## 5. What you should DO, in order (≈8 h)
1. Run `exercises/01_sim_and_reactive.md` (1 h): simulator, rviz, teleop, reactive stop.
2. `exercises/02_tf_odom.md` (1 h): TF tree, odom drift, go-to-goal controller.
3. `exercises/03_slam.md` (1.5 h): build and save a map.
4. `exercises/04_nav2.md` (1.5 h): localize + send goals, then Python waypoints.
5. `exercises/05_tuning_and_failures.md` (2 h): stress tests (feature-poor corridor, dynamic obstacle, sensor dropout, latency).
6. Write what you learn in `experiments/LOG.md`. Judges ask "what failed and why?" and you'll have answers.

## 6. How to prepare mentally for the real robot
- You will not build a perfect system; you will **adapt** known tools. Priority is getting `/scan`, `/odom`, `/cmd_vel`, and TF right.
- First hour on site checklist: topic names? frames? namespace? ROS distro? DDS? lidar frame in TF? maximum safe speed? where is the e-stop?
- Edit these in Nav2's params for the robot: `robot_radius`/footprint, `max_vel_x`, `max_vel_theta`, `inflation_radius`, scan topic, `base_frame_id`, `odom_frame_id`.
- Map the arena **slowly** (≤0.15 m/s), loop around, close loops; save the map immediately.
- Keep a `ros2 bag record -a` on all runs.

## 7. Winning angles (pick one differentiator)
- **Semantic goals**: "go to the red box" using Challenge 03 detections → map-frame goal.
- **AprilTag relocalization** in feature-poor corridors: tags at known positions snap the pose back.
- **Dynamic obstacle handling**: MPPI + demonstrate a person walking in.
- **Mission layer**: patrol with tasks (visit A, B, return; UI to add waypoints on a web map via rosbridge).
- **Evidence**: plot of planned vs. executed path; table of N runs (time, success, near misses).

## 8. Common failures and fixes
| Symptom | Likely cause → fix |
|---|---|
| Robot doesn't move on goal | not localized (`map→odom` missing): set initial pose; Nav2 lifecycle not active; `cmd_vel` remapped |
| Spins / oscillates | controller too aggressive; wrong footprint; lower `max_vel`, accel |
| Drives through walls | costmap not getting scan (QoS, topic name, frame); `use_sim_time` mismatch |
| "Failed to make progress" | inflation too big for narrow gap; footprint too large |
| Map is smeared | moved too fast; featureless corridor; add landmarks / lower speed |
| Pose jumps in rviz | AMCL re-localizing; a normal behaviour but check initial pose and particle spread |

## 9. Glossary
AMCL · BT (behavior tree) · costmap · EKF · inflation · lifecycle node · loop closure · MPPI · occupancy grid · odometry · particle filter · SLAM · TF · yaw.

## 10. Readiness checklist
- [ ] I can explain `map→odom→base_link` and who publishes each.
- [ ] I mapped the TB3 world and saved `maps/tb3_world.{pgm,yaml}`.
- [ ] I sent goals in rviz and from `waypoint_patrol.py`.
- [ ] I changed a Nav2 parameter and saw the behaviour change.
- [ ] I reproduced and understood at least 3 failure modes in the table above.
- [ ] I can list the first-hour real-robot checklist from memory.

## 11. Resources
Nav2 docs https://docs.nav2.org (Concepts → Setup Guides → Configuration Guide → Tutorials) · slam_toolbox GitHub README · *Articulated Robotics* YouTube (ROS 2 navigation series) · robot_localization docs.
