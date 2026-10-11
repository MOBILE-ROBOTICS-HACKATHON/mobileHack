# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Prep workspace for the Mobile Robotics Hackathon (TU Dresden, 10–11 Oct 2026, ROS 2 on real robots). Not a single application: it is a ROS 2 colcon workspace plus six per-challenge study folders. Priority tracks are 01 (navigation), 03 (computer vision), 04 (imitation learning); 02/05/06 are low priority. Human-oriented docs: `README.md`, `docs/00_HOW_TO_USE.md` (read first), `ROADMAP.md`, `PACKAGES.md`.

## Current work: the Olive ANT1 robot (read this first)

Active since 10 Oct 2026. **Before doing anything robot-related, read `docs/05_ANT1_HANDOFF_AND_LESSONS.md`.** It has the full state, current robot config, open items and the user's working preferences. Then use `docs/04_ANT1_COMMANDS.md` (commands), `docs/02_ANT1.md` (robot facts) and, for camera/drones/teammates, `docs/06_ANT1_CAMERA_DRONES_PLAN.md`.

**Robot:**
- ROS 2 **Jazzy**, CycloneDDS, domain 0, `NS=/olive/olixRobot/ant1/id001`.
- Reached from the container via `ANT1_IFACE=wlp3s0 source scripts/ant1_env.sh` (phone hotspot Wi-Fi; robot `10.66.76.31`) or `source scripts/ant1_env.sh` (Ethernet; robot `192.168.7.100`).
- Our nodes are in `ws/src/team_pkg/team_pkg/ant1_*.py`; diagnostics are in `scripts/ant1_diag/`.

**Hard rules:**
- The robot has **no cmd_vel timeout**, so `ant1_watchdog` must run, every motion ends with zeros, and STOP is sent before the e-stop is released.
- Test `ant1_goto` changes against `scripts/ant1_diag/fake_nav2.py` (isolated `ROS_DOMAIN_ID`) before the real robot.
- Nav2 runtime settings reset on robot reboot. After every boot, run `ant1_nav_speed` with the robot standing still.
- Humble can't see Jazzy nodes (`ros2 node list`/`ros2 param` fail): use parameter services (`ant1_param`).
- `serdata.cpp ... not null-terminated` spam is harmless.
- Robot-side files and SSH only with mentor OK.
- The user drives the robot; Claude only reads data, sets parameters, cancels goals, and sends zero velocity.

## Crazyflie 2.1 drones

**Full guide: `docs/07_CRAZYFLIE.md`.** Setup in every container terminal: `source scripts/cf_env.sh` (domain 42, `ROS_LOCALHOST_ONLY=1`).

**Terminals (like the ANT1):**
1. `cf_server`: crazyswarm2, cflib backend, config `ws/src/team_pkg/config/crazyflies.yaml` (assumes a Flow deck). Or `cf_fake` for practice and tests.
2. `cf_guard`: the safety guard. SPACE lands, `K` kills the motors; it auto-lands on fence, low battery or lost link.
3. `cf_rviz`.
4. `cf_keys`: keyboard steps plus typed go-to. Or `cf_takeoff`, `cf_goto`, `cf_move`, `cf_land`.

**Rules:**
- **Slow on purpose:** user's request, 10 Oct. 0.15 m/s (`CF_SPEED`), firmware cap `posCtlPid` 0.3 m/s, takeoff 0.3 m, zmax 1.0 m, fence ±1.0 m / 1.2 m around HOME.
- **Our drone is `radio://0/70/2M/E7E7E7E702` with a Lighthouse deck,** so positions are room coordinates and it needs ≥ 2 base stations. `cf_check` verifies this; on 10 Oct it saw 0 stations. `E7E7E7E704` belongs to another team.
- **The firmware needs arming** (`/cf1/arm`; cflib 0.1.28 = `cf.platform.send_arming_request`). Don't upgrade cflib: 0.1.34 needs numpy 2, which breaks `cv_bridge`.
- **No timeout on radio loss:** the drone keeps hovering at its last target. Catch it and flip it (tumble detection stops the motors).
- **`GoTo.yaw` is in radians.**
- **Test `cf_guard` / `cf_keys` changes** against `scripts/cf_diag/fake_cf.py` before flying.
- **The drone stack was added** with `docker/Dockerfile.drones`, because the full rebuild timed out on pytorch.org.

## ANT1 + drone missions (11 Oct)

**Full guide: `docs/08_ANT_DRONE_MISSIONS.md`.**
- **Method 1:** `mission_follow`: the ANT follows the drone you fly.
- **Method 2:** `mission_scout`: the ANT patrols; the drone escorts or scouts; recall lands it on the ANT.
- **Bridge:** `ant_link` is the only process in both domains: one process, two rclpy contexts, a two-`<Domain>` CycloneDDS config from `scripts/mission_env.sh`. Everything else stays in its own env.
- **Calibration:** `mission_calib`, map = R(θ)·room + t. It uses **stops** only, because a continuous drive biased θ by 2–3°.
- **Tests:** against the fakes: `scripts/mission_diag/sim_all.sh` (fake_nav2 `drive` + fake_cf `onant` + ant_link). Not run on hardware yet.
- **Shared ANT code:** `team_pkg/ant1_nav.py` (`free_goal`, `ACTIONS`), used by `ant1_goto` and `ant_link`.
- **Added 11 Oct, evening:**
  - **ROAM** formation (`f`), independent of the ANT; use `cf_guard -p area:=` with it, not the leash.
  - **Two drones:** `CF_DRONES=2`, `crazyflies_two.yaml`; cf2's URI is a placeholder until identified with `cf_identify`.
  - **`mission_hop`** (carrier hop).
  - Shared per-drone code in `mission_fleet.py`: plate slots, altitude layers 0.55 / 0.90 m, recall landing queue.
  - Step-by-step guide: `docs/09_MISSION_STEP_BY_STEP.md`.
- **Guard takeover rule:** when `cf_guard` lands or kills a drone, it publishes `/cfN/guard_event`. The missions and `cf_keys` must stop commanding that drone, because a `go_to` cancels a firmware landing. The guard re-lands if the drone isn't descending 1.5 s later.
- **Never send `go_to` to a drone that isn't flying:** an armed drone on the ground can take off.

## Three execution environments (the key thing to get right)

The host is Ubuntu 26.04 (no native ROS 2 Humble, system Python 3.14), so commands run in one of three places:

| Place | Used for |
|---|---|
| **HOST** | docker, git, editing files |
| **CONTAINER** (`hackathon-ros:humble`, ROS 2 Humble, Ubuntu 22.04) | everything `ros2`/`rclpy`/`colcon`, Gazebo, rviz2, Nav2, YOLO ROS nodes, CPU torch (only if built with `--torch`) |
| **HOST VENV** `.venv-ml` (Python 3.12 via uv) | GPU training (torch CUDA, LeRobot, YOLO fine-tuning). Has **no ROS**; `rclpy` nodes never run here |

The repo root is bind-mounted at `/hackathon` in the container, so edits on the host are instantly visible there. Anything else in the container (pip/apt installs) is lost on exit (`--rm`); make it permanent in `docker/Dockerfile` and rebuild. Typical ML flow: record data in the container → files appear on host → train in the venv → copy `.pt` back → run in the container.

## Commands

```bash
# HOST
bash scripts/build_image.sh       # light image; --torch adds CPU PyTorch + YOLO (challenges 03/04)
./docker/run.sh                 # start/re-enter container (also runs xhost, passes webcam/GPU if present)
./docker/run.sh ros2 topic list # one-off command
./docker/exec.sh                # extra terminal in the running container
bash scripts/setup_host_ml.sh && source .venv-ml/bin/activate   # GPU ML env

# CONTAINER
bash scripts/check_env.sh       # verifies ROS pkgs + Python libs; every line should be [ok]
cd /hackathon/ws && colcon build --symlink-install && source install/setup.bash
ros2 launch team_pkg hello.launch.py
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py gui:=false   # sim (TURTLEBOT3_MODEL=waffle)
```

There is no test suite or linter for the project code. The only tests are the ament boilerplate in `ws/src/learning_tf2_py/test/` (flake8/pep257/copyright), run with `colcon test` in the container.

## Architecture

- `ws/src/` – colcon workspace. `team_pkg` is the template package (ament_python; register executables in `setup.py` `entry_points`, launch files in `launch/`, config in `config/`). `learning_tf2_py` is the ROS tf2 tutorial package. After adding a new entry point or file, rerun `colcon build --symlink-install` (symlink-install makes plain Python edits live). `ws/build|install|log` are gitignored.
- `challenges/NN_*/` – each has `NOTES.md` (deep dive), `ROADMAP.md`, `exercises/*.md`, `experiments/LOG.md` (template: hypothesis/setup/result/lesson), and `src/`. Scripts in `src/` are **standalone** (`python3 path/to/script.py` inside the container, no colcon build); they are meant to be copied into `team_pkg` once they are project-ready.
- Intended integration chain (see `ROADMAP.md` Phase D): camera → `03/src/yolo_node.py` (publishes JSON on `detections`) → map-frame target (`03/exercises/04_geometry_3d.md`) → Nav2 (`01/src/waypoint_patrol.py`, via `nav2_simple_commander`) → behaviour. `03/src/image_source.py` publishes synthetic/webcam/video frames to `/image_raw` so vision work needs no robot; `follow_object.py` consumes `detections` and publishes `cmd_vel`.
- Imitation-learning pipeline (04) is split across environments: `record_demos.py` (container, logs lidar bins + cmd_vel to `data/*.npz`) → `train_policy.py` (pure torch, venv or container) → `run_policy.py` (container; imports `lidar_features` from `record_demos.py` so preprocessing stays identical, and wraps the policy with clamping + watchdog). `toy_bc.py` is a ROS-free BC vs DAgger demo.
- `06_hack_the_service_bot/src/recon.sh` is network recon; only point it at devices you are authorized to test (the hackathon-provided robots).

## Gotchas

- **`numpy<2` in the container.** Humble's `cv_bridge` is built against NumPy 1.x; NumPy 2 gives `_ARRAY_API not found`. Never `pip install -U numpy` there.
- Sensor subscribers must use `qos_profile_sensor_data` (BEST_EFFORT) or they receive nothing from `/scan`, camera, etc.
- DDS defaults baked into the image: `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`, `ROS_DOMAIN_ID=42`; on real robots set the team/robot domain ID and matching RMW, and use `use_sim_time:=false`.
- `*.pt`, `*.pth`, `*.onnx`, `challenges/*/data/*.npz`, bags, and `.venv-ml/` are gitignored (note `yolov8n.pt` sits in `challenges/03_computer_vision_ai/`); model weights are meant to be pre-downloaded for offline use at the event.
- Real-robot rules from `ROADMAP.md`: start slow (≈0.1 m/s), record a bag on every run, always wrap learned policies in safety code.
- Repo root contains stray `frames_*.pdf/.gv` files generated by `ros2 run tf2_tools view_frames`.
