# Mobile Robotics Hackathon: prep workspace

Event: https://mobile-robotics.eu · TU Dresden, 10–11 Oct 2026 · ROS 2 on real robots.

## Teammates: get it running (4 commands)
```bash
git clone <this repo> && cd <repo>
bash scripts/build_image.sh       # builds hackathon-ros:humble on YOUR laptop with YOUR user id (~20-30 min, ~7.6 GB)
                                  # add --torch only for challenges/03 (YOLO) or 04 (imitation learning)
./docker/run.sh                   # then inside: cd /hackathon/ws && colcon build --symlink-install
bash scripts/check_env.sh         # inside the container: every line [ok] ([--] torch is fine)
```
Image contents, building, sharing (GitHub, ghcr.io, USB stick) and multi-laptop rules: [docs/11_DOCKER_IMAGE_AND_SHARING.md](docs/11_DOCKER_IMAGE_AND_SHARING.md).

## Start here
1. [docs/00_HOW_TO_USE.md](docs/00_HOW_TO_USE.md): **Must read first!** Explicit instructions on Host vs Docker vs venv, commands, and workflow.
2. [docs/01_ROS2_FOUNDATIONS.md](docs/01_ROS2_FOUNDATIONS.md): Comprehensive ROS 2 notes (nodes, topics, messages, TF2, QoS, launch, debugging).
3. [ROADMAP.md](ROADMAP.md): Overall 4-day prep plan, weekend strategy, and self-test.
4. [PACKAGES.md](PACKAGES.md): Everything installed, package breakdowns, and what to install on demand.
5. [docs/02_ANT1.md](docs/02_ANT1.md): Our Olive ANT1 robot: connect, drive, sensors, protocols, gotchas (`source scripts/ant1_env.sh`).
6. [docs/03_ANT1_FIRST_DRIVE.md](docs/03_ANT1_FIRST_DRIVE.md): Step-by-step tutorial: first slow drive of the ANT1 (topic commands, then arrow keys).
7. [docs/04_ANT1_COMMANDS.md](docs/04_ANT1_COMMANDS.md): ANT1 command cheat sheet: every command in one page (safety, drive, rviz, Wi-Fi).
8. [docs/05_ANT1_HANDOFF_AND_LESSONS.md](docs/05_ANT1_HANDOFF_AND_LESSONS.md): **Where we are**: everything done/learned with the ANT1, current robot config, open items.
9. [docs/06_ANT1_CAMERA_DRONES_PLAN.md](docs/06_ANT1_CAMERA_DRONES_PLAN.md): Researched plan for the next steps: D555 camera, Crazyflie landing, sharing data with teammates.
10. [docs/07_CRAZYFLIE.md](docs/07_CRAZYFLIE.md): Crazyflie 2.1: connect, fly with ROS 2, guard, keys (`source scripts/cf_env.sh`).
11. [docs/08_ANT_DRONE_MISSIONS.md](docs/08_ANT_DRONE_MISSIONS.md) + [docs/09_MISSION_STEP_BY_STEP.md](docs/09_MISSION_STEP_BY_STEP.md): ANT + drone missions (follow, escort/scout/roam + recall, carrier hop), terminal by terminal.
12. [docs/11_DOCKER_IMAGE_AND_SHARING.md](docs/11_DOCKER_IMAGE_AND_SHARING.md): the Docker image and how to share it with the team.

### Challenges & Study Notes
Each challenge has a comprehensive deep-dive `NOTES.md`, a step-by-step `ROADMAP.md`, runnable code in `src/`, guided `exercises/`, and an `experiments/LOG.md`.

| Folder | Challenge | Notes & Plan | Priority |
|---|---|---|---|
| [01_autonomous_navigation](challenges/01_autonomous_navigation/) | Autonomous Navigation | [NOTES](challenges/01_autonomous_navigation/NOTES.md) · [ROADMAP](challenges/01_autonomous_navigation/ROADMAP.md) | ★★★ |
| [03_computer_vision_ai](challenges/03_computer_vision_ai/) | Computer Vision & AI | [NOTES](challenges/03_computer_vision_ai/NOTES.md) · [ROADMAP](challenges/03_computer_vision_ai/ROADMAP.md) | ★★★ |
| [04_physical_ai_imitation_learning](challenges/04_physical_ai_imitation_learning/) | Physical AI & Imitation Learning | [NOTES](challenges/04_physical_ai_imitation_learning/NOTES.md) · [ROADMAP](challenges/04_physical_ai_imitation_learning/ROADMAP.md) | ★★★ |
| [02_multi_robot_collaboration](challenges/02_multi_robot_collaboration/) | Multi-Robot Collaboration | [NOTES](challenges/02_multi_robot_collaboration/NOTES.md) · [ROADMAP](challenges/02_multi_robot_collaboration/ROADMAP.md) | ★ |
| [05_human_robot_interaction](challenges/05_human_robot_interaction/) | Intuitive HRI | [NOTES](challenges/05_human_robot_interaction/NOTES.md) · [ROADMAP](challenges/05_human_robot_interaction/ROADMAP.md) | ★ |
| [06_hack_the_service_bot](challenges/06_hack_the_service_bot/) | Hack the Service Bot | [NOTES](challenges/06_hack_the_service_bot/NOTES.md) · [ROADMAP](challenges/06_hack_the_service_bot/ROADMAP.md) | ★ |

## Quick start
```bash
# 1. Build the ROS 2 Humble image (once, ~15 min; the host OS has no native Humble)
docker build -t hackathon-ros:humble --build-arg UID=$(id -u) --build-arg GID=$(id -g) -f docker/Dockerfile docker

# 2. Enter the container (this folder is mounted at /hackathon). More terminals: ./docker/exec.sh
./docker/run.sh
bash scripts/check_env.sh

# 3. Build the team package (inside the container)
cd /hackathon/ws && colcon build --symlink-install && source install/setup.bash
ros2 launch team_pkg hello.launch.py

# 4. First sim (inside the container)
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py

# 5. Host-side GPU ML env (imitation learning / LeRobot), run on the host
bash scripts/setup_host_ml.sh && source .venv-ml/bin/activate
```

## Layout
```
docker/       Dockerfile, run.sh (enter container), exec.sh (extra terminals)
scripts/      check_env.sh (inside container), setup_host_ml.sh (host)
ws/src/       colcon workspace; team_pkg = your template package
challenges/   one folder per challenge: ROADMAP.md, src/, exercises/, experiments/
```

## Troubleshooting
| Problem | Fix |
|---|---|
| rviz/gazebo window doesn't open | on the host: `xhost +local:docker` (run.sh does it), check `echo $DISPLAY` |
| Gazebo very slow | no GPU in the container: use `gui:=false` and view in rviz |
| `_ARRAY_API not found` from cv_bridge | NumPy 2 got installed: `pip3 install "numpy<2"` |
| Subscriber gets no data | QoS mismatch: `ros2 topic info -v <topic>`; use `qos_profile_sensor_data` for sensors |
| Can't see another machine's topics | same `ROS_DOMAIN_ID`, same `RMW_IMPLEMENTATION`, same network, no firewall |
| Files in the workspace owned by root | image built with a different UID: rebuild with `--build-arg UID=$(id -u)` |
