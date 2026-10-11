# ANT1 work: complete handoff, state and lessons (session of 10 Oct 2026)

This document is everything a new session (human or Claude) needs to continue the Olive ANT1 work exactly where it stopped. Read it top to bottom once. Command details live in [04_ANT1_COMMANDS.md](04_ANT1_COMMANDS.md); robot facts in [02_ANT1.md](02_ANT1.md).

---

## 0. TL;DR (state at the end of the session)

**Driving and seeing:**
- The ANT1 is driven from the laptop **over Wi-Fi**: robot and laptop are both on the phone hotspot "Parsa". The robot is `10.66.76.31`, the laptop `10.66.76.202`. The Ethernet cable is still a fallback (`192.168.7.100` / `.200`).
- **Manual driving works:** `ant1_keys` (arrow keys, hold-to-move, `+`/`-` speed), `ant1_drive`, `ant1_teleop`, `ant1_steer`.
- **Safety:** `ant1_watchdog` runs all session.
- **Visualization works:** `ant1_rviz` shows the map, path, costmap, footprint, lidar and odometry trail.

**Mapping and navigation:**
- Both run **on the robot**: slam_toolbox and Nav2, started from the Web UI → SLAM → Mapping.
- `ant1_nav_speed` configures Nav2, which **restarts Nav2 while keeping the map**. It sets: 0.2 m/s and 0.5 rad/s, reverse and sideways driving, loose guardrails, a relaxed progress checker, and **planning on the live lidar** instead of the stale SLAM map.
- `ant1_goto x y` drives to a map coordinate. It checks reachability first, redirects to the closest reachable point, retries, and has several fail-safes.

**Last thing done:**
- Switched Nav2's global costmap to live-lidar mode.
- Verified on the robot: `(2.5, 2.5)` is now reachable, and Nav2 is active with all settings applied.
- **The user has NOT yet driven `ant1_goto 2.5 2.5` with this config.** That's the first thing to test next session.

**All Nav2 runtime settings reset on robot reboot.** After every boot:
1. robot standing still;
2. `ant1_nav_speed` (restarts Nav2, ~10 s, map kept).

---

## 1. Where things run (the setup)

| Place | What | Notes |
|---|---|---|
| HOST (Ubuntu 26.04) | docker, git, editor, browser (robot Web UI) | no ROS on the host |
| CONTAINER `hackathon-ros:humble` (ROS 2 **Humble**) | all `ros2`, our nodes, rviz, rqt, plotjuggler | `./docker/run.sh` (first terminal), `./docker/exec.sh` (more). Repo mounted at `/hackathon`, `--net=host`, GUI works (xhost) |
| ROBOT ANT1 | Debian 12, ROS 2 **Jazzy**, CycloneDDS, domain 0 | Nav2 + slam_toolbox + rosbridge + Web UI run here |

**In every container terminal:**
```bash
ANT1_IFACE=wlp3s0 source scripts/ant1_env.sh     # Wi-Fi (phone hotspot)
source scripts/ant1_env.sh                       # Ethernet cable (default enp2s0)
cd /hackathon/ws && colcon build --symlink-install && source install/setup.bash   # once per session / after new entry points
```

---

## 2. Robot facts (all measured on the real robot)

**Platform:**
- **Olive olixBot ANT1 Pro:** 600×400×146 mm, 18 kg, 60 kg payload, **mecanum** (x, y, yaw), max 2.5 m/s.
- **Battery:** 24 V LiFePO₄. It went 100 % → 67 % → 59 % during the session; **charge it**.

**ROS interface:**
- **Namespace** `$NS=/olive/olixRobot/ant1/id001`. Frames are prefixed `olive_olixRobot_ant1_id001_`: `map`, `odom`, `base_link`, `laser`, `laser_fl/fr/bl/br`.
- **TF** is on the **global** `/tf` and `/tf_static`: `map→odom` (SLAM), `odom→base_link` (10 Hz), `base_link→laser` (0,0,0), and `laser→laser_xx` (±0.18 m).

**Sensors and data:**
- **Fused scan:** `$NS/scan`, 360°, 1441 rays, −π..π (front = middle index), 0.03–25 m, 10 Hz, BEST_EFFORT.
- **Corner scans:** `scan_fl/fr/bl/br`, 2175 rays each, with intensities.
- **Odometry:** `odom` (fused, 10 Hz), `wheel_odom` (14 Hz).
- **IMUs:** 5 × `s1/*/imu` at ~105 Hz.
- **No camera** (Pro version).

**Network services on the robot:**

| Port | Service |
|---|---|
| 80 | Web UI (network page `/network`, SLAM page, Configuration) |
| 5000 | Vizanti map viewer |
| 5001 | **rosbridge WebSocket** |
| 9090 | File Browser |
| 22 | SSH (**not used, needs mentor OK**) |

**Quirks:**
- **NO `cmd_vel` timeout.** The robot keeps executing the last command forever. It needed the e-stop twice: once after `ros2 topic pub -t 20`, once from an `ant1_goto` bug.
- **Built-in laser safety stop:** parameter `laser_safety_distance_cm` on `/olive_olixRobot_id001_ant1` (Olive default 19; we keep 19). Corner LEDs turn orange when it triggers.
- **Robot clock ~76 s behind the laptop.** It was 21 days behind until the user did "Sync time" in the Web UI, which is a temporary sync.
  - Goals must use stamp 0, which `ant1_goto` does.
  - rviz "2D Goal" clicks may be rejected.

---

## 3. Everything we did, in order (with what we learned)

1. **Connected over Ethernet.**
   - CycloneDDS pinned to `enp2s0`, domain 0. Discovery and data were OK at once.
   - Found the robot runs Jazzy while we run Humble. Topics interoperate.
   - `serdata.cpp ... not null-terminated` spam is harmless (Jazzy discovery metadata).
   - `ros2 node list` and `ros2 param` can't see robot nodes. Use the parameter services: `ant1_param`.
2. **Built the environment:**
   - `scripts/ant1_env.sh` (env + helpers);
   - `ant1_drive` (timed moves);
   - `ant1_keys` (arrow keys);
   - `ant1_rviz` config;
   - docs `02`/`03`/`04`.
3. **Safety lesson: the robot has no cmd_vel timeout.** It kept turning after a 2 s `ros2 topic pub -t 20`, and the user used the e-stop. Response:
   - **`ant1_watchdog`** (sends STOP if commands stop for 0.5 s);
   - all our nodes send zeros on exit, Ctrl-C, closed terminal (SIGHUP) or `docker stop` (SIGTERM);
   - rule: send STOP before releasing the e-stop.
4. **Wi-Fi.**
   - **Eduroam:** impossible. It needs an 802.1X login, and the robot only takes SSID + password.
   - **Phone hotspot "Parsa":** chosen (laptop keeps internet).
   - **First failure:** ROS topics invisible over Wi-Fi.
     - I first **wrongly** blamed the phone for dropping multicast.
     - **Real cause:** the robot's **CycloneDDS config had `wlan0` commented out** (Web UI → Configuration; needed "Sync time" first).
   - **The user edited it**: uncommented the `wlan0` NetworkInterface and set `<AllowMulticast>spdp</AllowMulticast>`. The original is saved in [ant1_cyclonedds_original.xml](ant1_cyclonedds_original.xml). **Restore it after the hackathon.**
   - After Restart Services, all topics work over Wi-Fi with plain multicast. `ANT1_PEER=<ip>` (unicast discovery) also works, as a fallback.
   - The robot only uses networks that are connected **when its ROS starts**. If it boots without the hotspot, use Restart Services in the Web UI.
5. **Second env-script bug:** `ros2 daemon stop` hung forever after unplugging the cable (the daemon was bound to the dead interface). Fixed: the script `pkill`s the daemon instead.
6. **Lidars "inactive" after a power-on** → the Web UI allowed only manual driving.
   - `change_state` activate returned `success=False`.
   - **Fix:** power-cycle with the **e-stop held ~10 s after power-on** (inrush). After that, all 4 lidars were active at 10 Hz.
7. **Mapping and navigation.**
   - The robot's onboard SLAM + Nav2 started from the Web UI.
   - **Nav2 setup found:**
     - DWB controller;
     - NavFn planner;
     - velocity smoother (`cmd_vel_nav → cmd_vel`);
     - BT `navigate_to_pose_w_replanning_and_recovery` (recoveries: clear costmaps → spin 90° → wait 5 s → back up 0.3 m, about 6 retries);
     - lifecycle manager `lifecycle_manager_navigation` (manages controller, smoother, planner, behavior, bt_navigator, waypoint_follower, velocity_smoother; **not** slam_toolbox, so a restart keeps the map).
   - Wrote `ant1_goto`. It sends `PoseStamped` on `$NS/goal_pose`; Nav2 action types differ between Humble and Jazzy, so the action interface isn't used. The result is read from `navigate_to_pose/_action/status` (action_msgs, identical in both distros).
8. **"Gives up often":** caused by MY speed reduction.
   - Olive's progress checker requires 0.5 m in 2 s; at 0.1 m/s that's impossible.
   - Fixed: **0.25 m in 10 s**, set by `ant1_nav_speed`.
9. **`ant1_goto` "no TF" error:** over Wi-Fi the first TF takes 1–5 s and the tool waited only 2 s. It now waits up to 15 s.
10. **"Rotates a lot / gives up" (first round), diagnosed with a passive recorder.** Three causes:
    1. goals at or near obstacles → planner fails → recovery spins;
    2. the recovery spin ignored our speed limit (1.0 rad/s, read only at Nav2 start);
    3. goal messages lost over Wi-Fi.

    Fixes: `ant1_goto` re-sends unconfirmed goals; it checks the goal against the costmap.
11. **Sideways and reverse:**
    - `min_vel_x=0`, `max_vel_y=0` and **`vy_samples=0`**.
    - `vy_samples`, the recovery spin speed and critic weights are **only read when Nav2 starts**, so `ant1_nav_speed` sets them and then does a lifecycle **RESET + STARTUP**. The map is kept.
    - Never set y limits without `vy_samples` + restart: a y range with 0 samples makes DWB always strafe.
12. **Faster, looser, less turning, "don't give up":**
    - 0.2 m/s and 0.5 rad/s;
    - inflation 0.25 m and cost scaling 3.0;
    - goal tolerance 0.3 m / 0.3 rad;
    - `failure_tolerance` 1 s;
    - **PathAlign/GoalAlign scale 0**, so it slides instead of rotating to face the path;
    - `ant1_goto` keeps the heading by default, retries 3×, and redirects goals inside objects;
    - laser safety back to 19 cm (the user had set 30, which would stop the robot exactly where Nav2 now plans).
13. **Speed on the fly:**
    - `ant1_nav_speed v w --live` changes only the DWB + smoother limits, with no restart, so it's safe mid-goal.
    - **Relative values:** `+0.1` / `-0.1`.
    - **Caps:** 0.5 m/s, 1.0 rad/s.
    - `ant1_keys` got `+`/`-`.
14. **Serious bug: `ant1_goto` printed ARRIVED while the robot was still driving** (e-stop needed).
    - **Cause:** over Wi-Fi the latched list of OLD finished goals arrived after we sent ours, so an old SUCCEEDED goal was taken as ours.
    - **Fixes:**
      1. wait for the status list before sending;
      2. an unknown goal id counts as ours **only if first seen ACCEPTED or EXECUTING**;
      3. **fail-safe:** on SUCCEEDED, if the robot is > 0.6 m from the goal, cancel all goals and stop.
15. **"Rotates on the spot" (second round):** the goal `(2.5, 2.5)` was **unreachable**.
    - It sat in a closed pocket (no gap ≥ robot size) → the planner never found a path → only recovery spins.
    - **Fix:** `ant1_goto` now does a **reachability flood-fill** on the global costmap from the robot and drives to the **closest reachable point** if the goal can't be reached.
16. **Root cause of the pocket: stale SLAM map.**
    - People move chairs and tables. The `stale_map_check` showed **22 % of the SLAM map's obstacles were ghosts**: the lidar now sees through them.
    - Nav2's global costmap used the SLAM map (static layer, permanent), and its obstacle layer only marked within 2.5 m and cleared within 3 m.
    - **Fix (current):** `ant1_nav_speed` makes the **global costmap live-lidar only**:
      - plugins `[obstacle_layer, inflation_layer]`;
      - `rolling_window` 25×25 m, resolution 0.05;
      - marked to 10 m, cleared to 12 m.
    - Result: `(2.5, 2.5)` became free and reachable. `ant1_nav_speed --static-map` restores Olive's map-based planning.
    - **Trade-off:** occluded walls count as free until seen, so Nav2 may replan when they appear.
17. **First drive with live-lidar planning: "not moving" (session 2, 10 Oct).** The recorder showed:
    - controller loop at **0.1–1 Hz** instead of 20;
    - `Timed out while waiting for action server to acknowledge goal request for follow_path` → ABORTED;
    - repeated Nav2 resets (likely lifecycle bond timeouts) → goals rejected.
    - **Cause:** DWB scored 20×10×32 = **6400 trajectories per cycle** (`valid 5246/5246`); `vy_samples 10` had multiplied the load by 10.
    - **Fix:** `ant1_nav_speed` now sets vx/vy/vθ samples **8/5/10 = 400**. Applied and read back on the robot. Controller rate warnings then only appeared at goal start.
19. **`ant1_goto`: "no TF map -> base_link after 15 s" (later in session 2).**
    - Measured through rosbridge: the robot was publishing TF and the scan.
    - Over the hotspot with **multicast-only discovery**, `/scan` didn't arrive and `/tf` came and went; odom still arrived.
    - With **`ANT1_PEER=10.66.76.31`** (unicast discovery to the robot), in the same minute: scan 6.4 Hz, tf 60 Hz, and `map -> base_link` resolved.
    - The Wi-Fi link itself was fine (−39 dBm, 144 Mbit/s, ~0.5 MB/s used). Nav2 service calls failed in the same period.
    - **Use `ANT1_IFACE=wlp3s0 ANT1_PEER=10.66.76.31 source scripts/ant1_env.sh` in every terminal on the hotspot.** It adds unicast discovery on top of multicast.
18. **Serious bug #2: `ant1_goto` printed ABORTED, the robot kept driving (e-stop needed).**
    - **Cause:** Nav2 aborted `navigate_to_pose`, but the BT failed to halt the controller (`Failed to cancel action server for follow_path`), so **`follow_path` kept driving**. `ant1_goto` exited on ABORTED **without cancelling anything**, and its cancel only covered `navigate_to_pose`. The watchdog can't help while the controller is still publishing.
    - **Fixes in `ant1_goto`:**
      1. **every** exit after a goal (arrived, gave up, timeout, Ctrl-C, crash) runs `cancel_and_stop` from `finally`;
      2. it cancels all goals of navigate_to_pose, follow_path, spin, backup, drive_on_heading and wait, then sends zeros;
      3. if non-zero `cmd_vel` is still seen 1–2.5 s later, it **PAUSEs Nav2** (lifecycle) and tells you to run `ant1_nav_speed`; if even that fails it says to use the e-stop;
      4. goal re-send waits 5 s instead of 2 s (loaded Nav2 took 3.6 s to confirm, and re-sends preempted the goal).
    - Tested with `fake_nav2.py` modes `orphan`, `orphanpause` (new), `succeed`, `abortfirst`, `hang`, `liesucceed`, and Ctrl-C. **Not yet driven on the robot.**

---

## 4. Our tools (code map)

| File | What it is |
|---|---|
| `scripts/ant1_env.sh` | sourced env: domain 0, CycloneDDS pinned to `ANT1_IFACE` (+ optional `ANT1_PEER` unicast), `$NS`, daemon restart via pkill. Helpers: `ant1_watchdog`, `ant1_keys`, `ant1_goto`, `ant1_nav_speed`, `ant1_teleop`, `ant1_drive`, `ant1_rviz`, `ant1_steer`, `ant1_param` |
| `ws/src/team_pkg/team_pkg/ant1_watchdog.py` | STOP when `cmd_vel` stops while moving (0.5 s). Laptop-side only: can't help if Wi-Fi or the laptop dies |
| `.../ant1_keys.py` | arrow-key teleop, hold-to-move (0.6 s), caps 0.15 m/s / 0.5 rad/s, `+`/`-`, zeros on exit or signals |
| `.../ant1_drive.py` | timed moves / demo sequence, clamped, zeros on exit |
| `.../ant1_goto.py` | goal via `goal_pose` (stamp 0); waits for TF, status list and subscriber (15 s); reachability flood-fill; redirect; heading keep/face/deg; re-send if unconfirmed; retries on ABORTED; relays Nav2 WARN logs from `/rosout`; fail-safe distance check; Ctrl-C/crash → cancel all + stop |
| `.../ant1_nav_speed.py` | full mode: stationary check → set ~30 params on controller, smoother, behavior server, costmaps, robot safety → lifecycle RESET+STARTUP. `--live`: speeds only. Relative `+/-`, caps. `--static-map` |
| `ws/src/team_pkg/config/ant1.rviz` | fixed frame odom, top-down following the robot; map, local costmap, plan, footprint, TF, odom trail, scan |
| `scripts/ant1_diag/` | **diagnostics**, see below |
| `docs/ant1_cyclonedds_original.xml` | robot's original DDS config (restore after the hackathon) |

**Diagnostics in `scripts/ant1_diag/`.** Run them in a container terminal after `ANT1_IFACE=wlp3s0 source scripts/ant1_env.sh`, with `python3 scripts/ant1_diag/<file>`:
- `nav_recorder.py [seconds]`: **passive** timeline of goals, action states (navigate/spin/backup/wait), Nav2 logs, pose, commands incl. y, and DWB critic scores of the chosen trajectory. Run it, then let the user drive.
- `costmap_picture.py`: global costmap + reachability flood-fill → `costmap.png`. Shows what the planner thinks is blocked.
- `stale_map_check.py`: SLAM map vs live lidar → `stale_map.png` (red = ghost obstacles) and prints the costmap/planner/SLAM settings.
- `show_nav_settings.py`: reads back the key Nav2 settings.
- `cancel_all_goals.py`: prints goal states, cancels everything, sends zeros. Run it after any runaway.
- `rosbridge_call.py SERVICE 'JSON'` (**HOST**, not the container): calls a robot service through rosbridge (port 5001). Use it for Jazzy-only types and when DDS service discovery over Wi-Fi is flaky.
  - **Fresh SLAM map** (10 Oct; the old map was stale): `python3 scripts/ant1_diag/rosbridge_call.py /olive/olixRobot/ant1/id001/slam_toolbox/reset '{"pause_new_measurements": false}'`, then clear the global costmap the same way (`.../global_costmap/clear_entirely_global_costmap '{}'`).
  - **After a reset, map = odom frame.** The map origin is the odometry origin, not where the robot stands, so old goal coordinates mean different places.
- `fake_nav2.py MODE`: fake Nav2 (TF, `goal_pose`, status, cancel, costmap with obstacles and a closed pocket, `/rosout`) in namespace `/test`. Test `ant1_goto` **without the robot**:
  ```bash
  docker run --rm -v "$PWD":/hackathon -w /hackathon/ws -e ROS_DOMAIN_ID=77 -e ROS_LOCALHOST_ONLY=1 hackathon-ros:humble bash -c '
  source /opt/ros/humble/setup.bash; source install/setup.bash
  python3 /hackathon/scripts/ant1_diag/fake_nav2.py succeed & sleep 2
  ros2 run team_pkg ant1_goto 1.0 0.5 --ros-args -r __ns:=/test'
  ```
  Modes: `succeed`, `hang`, `dropfirst`, `abortfirst`, `latestatus`, `liesucceed`.

---

## 5. Current robot configuration (what is changed vs Olive)

| Where | Setting | Now | Olive default | Persists after reboot? |
|---|---|---|---|---|
| Robot CycloneDDS file (Web UI → Configuration) | wlan0 interface, AllowMulticast | **enabled, spdp** | commented out, true | **yes** (file) |
| Robot Wi-Fi (Web UI → /network) | client of phone hotspot "Parsa" | **joined** | not set | **yes** |
| Robot clock | synced from browser | ~76 s behind | 21 days behind | probably not |
| `laser_safety_distance_cm` | | 19 | 19 | — |
| Nav2 controller (DWB) | speed / turn | 0.2 / 0.5 | 0.3 / 0.65 | **no** |
| | min_vel_x / y range / samples vx·vy·vθ | −0.2 / ±0.2 / 8·5·10 | 0 / 0 / 20·0·32 | no |
| | PathAlign / GoalAlign scale | 0 / 0 | 12.5 / 12.5 | no |
| | goal tolerance xy / yaw | 0.3 / 0.3 | 0.25 / 0.1 | no |
| | failure_tolerance | 1.0 | 0.3 | no |
| | progress checker | 0.25 m / 10 s | 0.5 m / 2 s | no |
| velocity_smoother | max/min velocity, y accel | ±[0.2, 0.2, 0.5], y 0.3 | [0.3, 0, 0.75], y 0 | no |
| behavior_server | spin max / min / accel | 0.5 / 0.1 / 1.0 | 1.0 / 0.4 / 3.2 | no |
| costmaps | inflation radius / global cost scaling | 0.25 / 3.0 | 0.325 / 2.0 | no |
| global costmap | plugins / window | **obstacle+inflation, rolling 25 m, live lidar to 10/12 m** | static+obstacle+inflation, lidar 2.5/3 m | no |

To make the Nav2 settings permanent, edit `/opt/olive/config/current/olixRobot/nav_params/jazzy/navigation_omni.yaml` on the robot. That's a robot file, so get mentor OK first. Until then: **`ant1_nav_speed` after every boot.**

---

## 6. Safety rules learned the hard way

1. The robot **never stops on its own** when commands stop. Keep `ant1_watchdog` running, stream at ≥ 5 Hz, end every motion with a zero Twist.
2. **Before releasing the e-stop:**
   ```bash
   ros2 service call $NS/navigate_to_pose/_action/cancel_goal action_msgs/srv/CancelGoal "{}"
   ros2 topic pub -w 1 -r 10 -t 10 $NS/cmd_vel geometry_msgs/msg/Twist "{}"
   ```
   Otherwise a remembered goal or command resumes.
3. If the robot drives on after `ant1_goto` quit: run the cancel command above (or `scripts/ant1_diag/cancel_all_goals.py`).
4. Over Wi-Fi a dropout cannot be caught by laptop-side safety. Nav2 goals keep running on the robot, and its velocity smoother stops the robot if Nav2 stops. For manual driving: e-stop in reach, low speed.
5. `ant1_nav_speed` (full mode) restarts Nav2: only with the robot standing still (the tool checks).
6. Power-on: e-stop pressed → power → wait ~10 s → release. Otherwise the lidars may stay inactive.

---

## 7. Open items / next steps (in priority order)

1. **Test `ant1_goto 2.5 2.5`** with the live-lidar config (verified reachable, not yet driven). Run `scripts/ant1_diag/nav_recorder.py` in parallel. If it misbehaves, read the recorder output.
2. Watch for side effects of live-lidar planning: replanning when occluded walls appear, goals outside the room through doors, CPU load. The robot already reported controller/planner loops below 20 Hz; consider lowering DWB samples (vx 20 / vy 10 / vθ 32 is heavy).
3. Possibly switch the planner to **Theta\*** or Smac (installed on the robot) for straighter paths. The plugin param plus a Nav2 restart, same mechanism as `ant1_nav_speed`.
4. Optional helper `ant1_map`: a one-command costmap/reachability picture before choosing goals. `costmap_picture.py` already does this.
5. Charge the battery; keep an eye on it (it was dropping fast).
6. Make the Nav2 settings permanent in `navigation_omni.yaml` (mentor OK).
7. Bigger roadmap (user's mission, **step by step, own laptop first**), researched in [06_ANT1_CAMERA_DRONES_PLAN.md](06_ANT1_CAMERA_DRONES_PLAN.md):
   - D555 RealSense camera (not connected yet; needs a driver on the laptop or the robot);
   - Crazyflie 2.x drones landing on the ANT1 (crazyswarm2 + Crazyradio bridge on a laptop);
   - teammates' laptops.
8. After the hackathon: restore `docs/ant1_cyclonedds_original.xml` on the robot, forget the hotspot Wi-Fi, set the safety distance as found (19).

---

## 8. How Claude should work with this user (preferences)

- **Step by step, own laptop first:** connect/command → sensors → navigation → camera/drones → teammates. Don't build ahead.
- Very low speeds and safety first. The user had to use the e-stop twice because of our mistakes (wrong tutorial claim about `-t 20`, then the false ARRIVED bug): **test with `fake_nav2.py` before touching the real robot**, and never claim something works on the robot unless it was measured there.
- **Diagnose with data** (recorder, costmap picture) before changing settings.
- Robot-side file changes (DDS config, Nav2 yaml) and SSH: only with mentor OK. Runtime parameter changes via ROS are OK.
- The user runs motion commands themselves. Claude may: read data, set parameters, restart Nav2 while stationary, cancel goals, send zero velocity.
