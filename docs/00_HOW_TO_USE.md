# How to use this workspace (Docker, venv, terminals, everything)

Read this once, top to bottom. After it you will know **where each command runs** and what each tool is.

## 0. The one idea you must understand: THREE places commands run

| Place | What it is | Used for | How you know you're in it |
|---|---|---|---|
| **HOST** | your normal Ubuntu 26.04 terminal | Docker commands, `git`, GPU model training, editing files, browser | prompt: `parsa@...:~/Desktop/...$` |
| **CONTAINER** | a mini Ubuntu 22.04 with ROS 2 Humble inside Docker | **all `ros2 ...` commands**, Gazebo, rviz2, Nav2, YOLO ROS nodes | prompt: `hack@<hostname>:/hackathon$` |
| **HOST VENV** (`.venv-ml`) | a Python 3.12 environment on the host | GPU training (PyTorch CUDA, LeRobot, YOLO training) | prompt starts with `(.venv-ml)` |

**Why not install ROS directly on the host?** Your host is Ubuntu 26.04. ROS 2 Humble only has packages for Ubuntu 22.04. Docker gives us a 22.04 box with Humble, without touching your system. The host's Python is 3.14, which is too new for PyTorch/LeRobot wheels, hence the separate 3.12 venv.

**The workspace folder is shared.** `/home/parsa/Desktop/University/Masters/semester2/Hackathon` on the host appears as `/hackathon` inside the container. A file you edit on the host (in VS Code etc.) is instantly visible in the container, and files the container creates (maps, bags, datasets) appear on the host. Everything else inside the container is **temporary** and disappears when you exit.

---

## 1. Docker: step by step

### 1.1 What "image" and "container" mean
- **Image** = a frozen template (like an installer / a VM disk that is read-only). Ours is called `hackathon-ros:humble`. You build it once.
- **Container** = a running instance of an image (like a started VM). You start it, work, exit. It is deleted on exit (`--rm`), but the **image stays**.
- Analogy: image = class, container = object.

### 1.2 What is the 8.7 GB?
It is the **disk space the image takes on your SSD**, the one-time cost of having ROS 2, Gazebo and PyTorch preinstalled. It is **not** RAM and it is not copied per terminal. Measured with `docker history hackathon-ros:humble`:

| Part | ≈ Size (uncompressed) | Contents |
|---|---|---|
| Base `osrf/ros:humble-desktop-full` | ~4.2 GB | Ubuntu 22.04 (88 MB) + ROS 2 Humble core + rviz2 + rqt + Gazebo + simulation tools + OpenCV/PCL (the big 2.9 GB layer is `desktop-full`) |
| Our `apt` layer | ~0.9 GB | Nav2, slam_toolbox, TurtleBot3 + Gazebo bindings, robot_localization, apriltag, rosbridge, teleop, plotjuggler, CycloneDDS |
| Our `pip` layer | ~1.7 GB | CPU PyTorch, ultralytics (YOLO), OpenCV, SciPy, matplotlib, pandas, scikit-learn, cflib |

These layers add up to ≈ 6.8 GB. `docker images` shows **8.74 GB** ("DISK USAGE") because Docker's image store counts unpacked layers a bit differently. The **1.93 GB** "CONTENT SIZE" column is the compressed size that would be downloaded or pushed. Don't worry about the difference; the practical number is "about 7-9 GB of SSD".

Check it: `docker images hackathon-ros` · layer by layer: `docker history hackathon-ros:humble` · everything Docker uses (images, containers, build cache): `docker system df`. Note that the **build cache** (16 GB on your machine, 5 GB reclaimable) is separate from the image; `docker builder prune` frees it.
Free it later (after the event): `docker rmi hackathon-ros:humble`. You have ~210 GB free, so it's fine.
Copies are cheap: starting 5 containers from it does not use 5 × 8.7 GB, because the image layers are shared.

### 1.3 Build the image (already done once; redo only if you edit `docker/Dockerfile`)
```bash
# HOST, from the workspace folder
cd ~/Desktop/University/Masters/semester2/Hackathon
bash scripts/build_image.sh       # light image; --torch adds CPU PyTorch + YOLO (challenges 03/04)
```
Takes ~10-15 min the first time (downloads ~3 GB); later rebuilds reuse cached layers. `UID/GID` make the `hack` user in the container match you, so files it creates in `/hackathon` are owned by *you*, not root.

### 1.4 Start the container (every work session)
```bash
# HOST
cd ~/Desktop/University/Masters/semester2/Hackathon
./docker/run.sh
```
What it does: allows the container to open windows on your screen (`xhost`), mounts this folder to `/hackathon`, shares the host network (`--net=host`, so robots on the network are reachable), passes through a webcam if present, and drops you in a shell. Your prompt changes to `hack@...:/hackathon$`.

Run one command without an interactive shell: `./docker/run.sh ros2 topic list`

### 1.5 Open more terminals in the SAME container
You always need several terminals (simulator, rviz, your node, teleop...). In each new **HOST** terminal:
```bash
cd ~/Desktop/University/Masters/semester2/Hackathon
./docker/exec.sh          # (or ./docker/run.sh; it re-enters if already running)
```
Tip: install `tmux` on your host or use the terminal's split panes. Inside the container `tmux` is already installed: `tmux`, `Ctrl-b %` (split), `Ctrl-b "` (split horizontally), `Ctrl-b arrows` (move).

### 1.6 Exit and stop
`exit` or `Ctrl-D` in the **first** terminal (the one that ran `run.sh`) stops the container, and all other terminals die with it. If you need to hard-stop: `docker stop hackathon` (HOST).

### 1.7 Things that are lost when the container exits
Anything installed with `pip3 install` / `apt install` *inside* the container; any file outside `/hackathon`. To make an install permanent, add it to `docker/Dockerfile` and rebuild (1.3). For quick one-off installs just redo them next session.

### 1.8 Verify the container is healthy
```bash
# CONTAINER
bash scripts/check_env.sh      # every line must say [ok]
rviz2                          # a window must open on your desktop
```
If `rviz2` shows "could not connect to display": on HOST run `xhost +local:docker`, then `echo $DISPLAY` should print `:0` (or similar). On Wayland, XWayland handles it and that works.

### 1.9 GPU inside the container (optional)
The container currently uses **CPU PyTorch** (fine for YOLOv8n/s on a laptop: ~5-15 FPS). Your RTX 3050 is used by the **host venv** instead. If you want GPU inside the container too: install the NVIDIA Container Toolkit (commands in `PACKAGES.md`), then `./docker/run.sh` auto-adds `--gpus all`; inside run `pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu124` (temporary) and use `--device cuda:0`.

### 1.10 Take the image to another machine / teammate (offline)
```bash
docker save hackathon-ros:humble | gzip > ~/hackathon-ros.tar.gz       # HOST, ~3-4 GB file
docker load < hackathon-ros.tar.gz                                     # on the other machine
```
Do this Friday and keep the tarball on a USB stick: no downloads needed at the venue.

---

## 2. The ROS 2 workspace (`ws/`) and building your own code

Your own packages go in `ws/src/`. A template package `team_pkg` is already there.

```bash
# CONTAINER
cd /hackathon/ws
colcon build --symlink-install          # compiles all packages in src/  (--symlink-install: Python edits apply without rebuilding)
source install/setup.bash               # makes `ros2 run/launch team_pkg ...` visible. Needed in EVERY new terminal (already auto-sourced in ~/.bashrc once install/ exists)
ros2 launch team_pkg hello.launch.py
```
- Edit Python in `ws/src/team_pkg/team_pkg/*.py`; register a new executable in `setup.py` → `entry_points`; add a launch file in `launch/`.
- After adding a *new* file/entry point: `colcon build --symlink-install` again.
- The scripts in `challenges/*/src/*.py` are **standalone**: run with `python3 path/to/script.py`; no build needed. When one is ready for the real project, copy it into `team_pkg`.

---

## 3. The host venv (`.venv-ml`): GPU machine learning

```bash
# HOST, once (takes a while; downloads ~3 GB of CUDA PyTorch)
bash scripts/setup_host_ml.sh

# Every time you want to train:
cd ~/Desktop/University/Masters/semester2/Hackathon
source .venv-ml/bin/activate            # prompt gets (.venv-ml)
python -c "import torch; print(torch.cuda.is_available())"     # must print True
deactivate                              # leave the venv
```
Use it for: training the imitation policy (`challenges/04.../src/train_policy.py`), LeRobot, YOLO fine-tuning, Jupyter (`jupyter lab`), any heavy ML. It does **not** have ROS, so ROS nodes (`rclpy`) never run here. Typical flow: record data in the container → files appear on host → train in venv → `.pt` file appears → run it in the container.

If the install stalls (slow network): re-run the same script; it resumes. Check progress: `tail scripts/setup_host_ml.log`.

---

## 4. Daily routines (copy-paste)

**Start a session**
```bash
cd ~/Desktop/University/Masters/semester2/Hackathon
./docker/run.sh                                  # terminal 1 (CONTAINER)
./docker/exec.sh                                 # in more terminals as needed
```
**Typical simulation session** (each line in its own container terminal)
```bash
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py gui:=false   # the simulated robot + world (headless = fast)
rviz2                                                                 # visualise (Fixed Frame: odom)
ros2 run teleop_twist_keyboard teleop_twist_keyboard                  # drive
python3 challenges/01_autonomous_navigation/src/obstacle_stop.py      # your code
```
Drop `gui:=false` to see the Gazebo window (slower without a GPU).
**End of the day**: `git add -A && git commit -m "..."` (HOST), then `exit` the container.

## 5. Tool cheat sheet (what each thing is)
| Tool | One line | Where |
|---|---|---|
| `ros2 topic list/echo/hz/info` | inspect message streams | CONTAINER |
| `ros2 node list`, `ros2 service call`, `ros2 param` | inspect/control nodes | CONTAINER |
| `ros2 bag record -a -o name` / `ros2 bag play name` | record/replay all topics | CONTAINER |
| `rviz2` | 3D viewer: maps, scans, TF, paths, images | CONTAINER |
| `rqt`, `rqt_image_view`, `rqt_graph` | GUI tools: image viewer, node graph | CONTAINER |
| `ros2 run tf2_tools view_frames` | draws the TF tree to `frames.pdf` | CONTAINER |
| `colcon build` | compiles your ROS packages | CONTAINER |
| `gazebo` / `turtlebot3_gazebo` | physics simulator + robot model | CONTAINER |
| `plotjuggler` | plot topics/bags in time | CONTAINER |
| `docker images / ps / stop / rmi` | manage images/containers | HOST |
| `source .venv-ml/bin/activate` | enter the GPU ML Python | HOST |
| `uv pip install X` | install into the venv (fast pip) | HOST (venv active) |

## 6. Real robot day: what changes
1. Do **not** start Gazebo. The robot's computer publishes `/scan`, `/odom`, etc.
2. Same network + same `ROS_DOMAIN_ID` + compatible DDS: `export ROS_DOMAIN_ID=<given>`; default here is 42 (`docker/Dockerfile`). If the robot uses Fast DDS: `export RMW_IMPLEMENTATION=rmw_fastrtps_cpp` (Cyclone and Fast can often interoperate, but not always).
3. `ros2 topic list` must show the robot's topics. If not → see README troubleshooting.
4. Launch with `use_sim_time:=false`.
5. The container uses `--net=host`, so it sees the same network as your laptop. Join the venue Wi-Fi on the host first.

## 7. When something breaks
| Symptom | Do |
|---|---|
| `docker: permission denied` | you're in the `docker` group already; log out/in once if needed |
| `Cannot connect to the Docker daemon` | `sudo systemctl start docker` |
| Window won't open | `xhost +local:docker` on HOST |
| Everything slow | use `gui:=false`, close the Gazebo GUI, run YOLO with `yolov8n.pt` |
| `ros2: command not found` in container | you forgot `bash -i`; use `./docker/run.sh` (it sources ROS) or `source /opt/ros/humble/setup.bash` |
| New package not found | `colcon build` then `source /hackathon/ws/install/setup.bash` |
| Out of disk | `docker system prune` (HOST) removes stopped containers/unused layers (not your image if it's in use) |
