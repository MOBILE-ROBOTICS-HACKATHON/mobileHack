# The Docker image `hackathon-ros:humble`: what's in it, build it yourself, run, share the code

Everything ROS runs in this one image. The host (Ubuntu 26.04) has no ROS. The **repo folder is mounted into the container at `/hackathon`**, so code, scripts, docs and configs live in the **repo**, not in the image.

**To share the project you share only the code** (a GitHub repository, ~11 MB). The image is **not** uploaded: every teammate builds it on their own laptop with one command, which downloads all dependencies and gives the image their own user id:
```bash
bash scripts/build_image.sh            # light image: everything for the ANT, drones, missions, vision (no PyTorch)
bash scripts/build_image.sh --torch    # + CPU PyTorch + YOLO (only challenges/03 and 04 need them)
```
The files, helpers and terminal commands are then identical on every laptop (`./docker/run.sh`, `source scripts/cf_env.sh`, ...).

---

## 1. What's in the image

| Layer (Dockerfile) | Contents |
|---|---|
| base `osrf/ros:humble-desktop-full` | Ubuntu 22.04, ROS 2 Humble desktop (rviz2, rqt, Gazebo classic) |
| apt (`docker/Dockerfile`) | Nav2 + `nav2_simple_commander`, slam_toolbox, robot_localization, TurtleBot3 (+ Gazebo), teleop, tf2 tools, cv_bridge, image transport, v4l2 camera, apriltag_ros, rosbridge, rqt*, PlotJuggler, **CycloneDDS** (`RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`), xacro, colcon, rosdep, vcstool, git, tmux, htop, nmap, libusb |
| pip (`docker/Dockerfile`) | **numpy < 2** (needed by Humble's cv_bridge), OpenCV headless, scipy, matplotlib, pandas, scikit-learn, transforms3d, pyyaml |
| optional (`--torch` = `--build-arg WITH_TORCH=1`) | CPU **torch + torchvision**, **ultralytics** (YOLO): ~2.5 GB, only for challenges/03 and 04. The robot/drone/mission/vision tools don't import them |
| drones (`docker/Dockerfile`, also `docker/Dockerfile.drones`) | **crazyswarm2** (`ros-humble-crazyflie*`, `crazyflie_server_py/cpp`, interfaces, examples), motion_capture_tracking, rowan, **cfclient 2025.2**, **cflib 0.1.28** (not newer: 0.1.34 needs numpy 2) |
| user | `hack` with the builder's user id (`build_image.sh` passes `id -u`/`id -g`), passwordless sudo; `~/.bashrc` sources ROS + `/hackathon/ws/install`, starts in `/hackathon` |
| env | `ROS_DOMAIN_ID=42`, `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`, `TURTLEBOT3_MODEL=waffle` |

**Not in the image (in the repo instead):**
- `ws/src/team_pkg`: our nodes; built by `colcon build` *inside* the container into `ws/install`;
- `scripts/` (`ant1_env.sh`, `cf_env.sh`, `mission_env.sh`, diagnostics, fakes, `sim_all.sh`, `mission_tmux.sh`);
- `jetson/` (runs on the Jetson, not in Docker);
- `docs/`, the configs;
- `data/` (runtime calibrations and logs, never shared).

**Check an image:**
```bash
./docker/run.sh bash scripts/check_env.sh      # every line [ok]; torch/ultralytics show [--] in the light image
```

---

## 2. Build it

| Goal | Command (HOST, repo folder) | Time |
|---|---|---|
| **light image (everyone)** | `bash scripts/build_image.sh` | 20–30 min, ~7.6 GB on disk |
| with PyTorch + YOLO | `bash scripts/build_image.sh --torch` | +10 min, +2.5 GB (pytorch.org timed out twice on 10 Oct: retry on a good network) |
| add only the drone layer to an older image | `docker build -t hackathon-ros:humble -f docker/Dockerfile.drones docker` | ~2 min |

Both build the tag `hackathon-ros:humble`, which `run.sh` / `exec.sh` use. Rebuilding is cheap: Docker reuses every unchanged layer, and `--torch` only adds the last layers.

**Rules:**
- Anything you `pip`/`apt` install *inside* a running container is lost at exit (`--rm`). Make it permanent in a Dockerfile, preferably as a **new layer at the end**, so the big layers stay cached.
- Never `pip install -U numpy` in the image (cv_bridge needs numpy < 2).

---

## 3. Run it (same for everyone)

```bash
./docker/run.sh        # FIRST terminal: starts the container (keep it open, closing it stops everything)
./docker/exec.sh       # every further terminal
./docker/run.sh ros2 topic list    # a one-off command
```

What `run.sh` gives the container:
- `--net=host` (ROS/DDS sees the real network: Wi-Fi to the ANT, UDP from the Jetson);
- `--privileged`;
- the X11 display (rviz, cfclient);
- the repo at `/hackathon`;
- `/dev/bus/usb` + the host's `plugdev` group (**Crazyradio**, also when plugged in later);
- webcams `/dev/video*`;
- the NVIDIA GPU if the NVIDIA container toolkit is installed.

**Host prerequisites, each laptop once:**
1. Docker (`sudo usermod -aG docker $USER`, log out and in).
2. For the **Crazyradio**: the udev rule `/etc/udev/rules.d/99-bitcraze.rules` and membership in `plugdev`:
   ```bash
   sudo tee /etc/udev/rules.d/99-bitcraze.rules >/dev/null <<'R'
   SUBSYSTEM=="usb", ATTRS{idVendor}=="1915", ATTRS{idProduct}=="7777", MODE="0664", GROUP="plugdev"
   SUBSYSTEM=="usb", ATTRS{idVendor}=="1915", ATTRS{idProduct}=="0101", MODE="0664", GROUP="plugdev"
   SUBSYSTEM=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", MODE="0664", GROUP="plugdev"
   R
   sudo udevadm control --reload-rules && sudo udevadm trigger && sudo usermod -aG plugdev $USER   # log out/in
   ```
3. A Linux desktop with X11 or XWayland (for rviz).

**First time in a fresh clone (inside the container):**
```bash
cd /hackathon/ws && colcon build --symlink-install && source install/setup.bash
```

---

## 4. Share it

### 4.1 The code: a GitHub repository (on your laptop, once)
```bash
cd ~/Desktop/University/Masters/semester2/Hackathon
git init -b main
git add -A
git status                     # CHECK: no ws/build, ws/install, data/, .venv-ml, *.pt in the list
git commit -m "Hackathon workspace: ANT1 + Crazyflie missions, vision rescue, tools and docs"
```
1. On **github.com**: **New repository**, give it a name (e.g. `hackathon-robots`), choose **Private** (recommended: the docs mention the hotspot name and robot IPs), with **no** README or .gitignore.
2. Then:
   ```bash
   git remote add origin https://github.com/<your-user>/hackathon-robots.git
   git push -u origin main        # user name + a TOKEN as password (GitHub -> Settings -> Developer settings -> tokens, scope "repo")
   ```
3. Add teammates under the repo's *Settings → Collaborators*.

**Later changes:** `git add -A && git commit -m "..." && git push`.

### 4.2 Teammates: from zero to running
```bash
git clone https://github.com/<your-user>/hackathon-robots.git
cd hackathon-robots
bash scripts/build_image.sh                            # (--torch only for challenges/03, 04)
./docker/run.sh
cd /hackathon/ws && colcon build --symlink-install && source install/setup.bash
bash /hackathon/scripts/check_env.sh
```
After that, **every command in docs/04, 07, 08, 09 works the same**: the same file names, helpers and terminals. They also need the host prerequisites from section 3 (Docker, the Crazyradio udev rule) if they fly drones.

### 4.3 Optional: share a finished image instead (no build)
For a teammate with a bad network at the event: `scripts/share_image.sh` still works.
- `save` / `load`: a `hackathon-ros_humble.tar.gz` on a USB stick (~3–4 GB);
- `push <user>` / `pull <user>`: via `ghcr.io` (needs a GitHub token with `write:packages` / `read:packages`);
- then `fix-uid` on their laptop if their `id -u` differs from yours (otherwise files in `/hackathon` get the wrong owner).

### 4.4 Updating
- **The Dockerfile changed:** teammates `git pull` and run `bash scripts/build_image.sh` again (only the changed layers rebuild).
- **The code changed:** `git push`; teammates `git pull`, then `colcon build --symlink-install` if entry points changed (`setup.py`).

---

## 5. Several laptops on the same robots (read before the team uses it)
- **Drone side:** `cf_env.sh` keeps each laptop's drone traffic on **localhost** (domain 42, `ROS_LOCALHOST_ONLY=1`). Laptops don't see each other's drones, and **only the laptop with the Crazyradio controls the drones**.
- **ANT side:** domain 0 over the hotspot, so **every laptop on the hotspot can command the ANT**. Agree on **one pilot laptop** for `ant1_goto` / missions / `mission_link`. Others may watch (`ant1_rviz`, `ros2 topic echo`) but not drive.
- **Calibrations** (`data/`) are per laptop and session and not in git. Each pilot laptop calibrates itself (`mission_calib_quick`).
- **The Jetson** sends UDP to **one** laptop IP (`LAPTOP_IP` in `~/.jetson_vision.env`): the pilot laptop.

---

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| `permission denied` writing in `/hackathon` (colcon, data/) | the image was built by someone else: `bash scripts/build_image.sh` (or `share_image.sh fix-uid`) |
| `No module named torch` / `ultralytics` | light image: `bash scripts/build_image.sh --torch` |
| `docker: permission denied` | `sudo usermod -aG docker $USER`, log out and in |
| rviz/cfclient: `cannot open display` | `xhost +local:docker` on the host (`run.sh` does it), X11/XWayland session |
| `Cannot find a Crazyradio Dongle` | host udev rule + `plugdev` (section 3); container started *after* adding them; `lsusb \| grep 1915` |
| `denied` on `docker pull ghcr.io/...` | private package: `docker login ghcr.io` with a `read:packages` token, or ask for access |
| `unauthorized` on push | token without `write:packages`, or the user name is not lower case |
| `_ARRAY_API not found` | someone upgraded numpy in the container: restart the container (`--rm` resets it) |
| `Failed to find a free participant index` | new terminals need `source scripts/cf_env.sh` from 11 Oct or later (allows 120 ROS processes) |
