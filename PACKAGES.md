# Packages: what to install and why

The host is **Ubuntu 26.04**, which has no native ROS 2 Humble packages. So ROS 2 and its packages live in **Docker** (`docker/Dockerfile`). GPU ML training runs on the **host** in a Python 3.12 venv.

## Already handled by the setup (nothing to install by hand)

### Inside the Docker image `hackathon-ros:humble` (see `docker/Dockerfile`)
| Group | Packages | Why |
|---|---|---|
| Base | `ros-humble-desktop-full` (rviz2, rqt, Gazebo/ignition, turtlesim, tf2, rosbag2, cv_bridge…) | core |
| Navigation | `navigation2`, `nav2-bringup`, `nav2-simple-commander`, `slam-toolbox`, `robot-localization` | Challenge 01 |
| Simulation | `gazebo-ros-pkgs`, `turtlebot3`, `turtlebot3-gazebo`, `turtlebot3-navigation2`, `turtlebot3-cartographer` | practice without hardware |
| Teleop | `teleop-twist-keyboard`, `teleop-twist-joy` | drive + record demos |
| Vision | `cv-bridge`, `vision-opencv`, `image-transport`, `v4l2-camera`, `image-tools`, `apriltag-ros` | Challenge 03 |
| HRI/tools | `rosbridge-suite`, `rqt*`, `plotjuggler-ros`, `tf2-tools`, `xacro` | UI, debugging |
| DDS | `rmw-cyclonedds-cpp` (set as default) | more reliable than Fast DDS on Wi-Fi |
| Python (pip) | `numpy<2`, `torch` (CPU), `torchvision`, `ultralytics`, `opencv-python-headless<4.11`, `scipy`, `matplotlib`, `pandas`, `scikit-learn`, `transforms3d`, `cflib` | ML/vision/crazyflie |
| System | `git curl wget nano vim tmux htop nmap net-tools` | utilities |

> **`numpy<2` matters.** Humble's `cv_bridge` is compiled against NumPy 1.x. NumPy 2 makes `cv_bridge` crash with `_ARRAY_API not found`. Never `pip install -U numpy` in the container.

### On the host, `scripts/setup_host_ml.sh` (`.venv-ml`, Python 3.12 via `uv`)
`torch`/`torchvision` (CUDA 12.4 wheels), `lerobot`, `ultralytics`, `opencv-python`, `gymnasium`, `numpy`, `matplotlib`, `tqdm`, `jupyterlab`.
Why separate from Docker? The container can't see the GPU without the NVIDIA toolkit, and LeRobot needs Python ≥ 3.10/3.12. The host venv has none of those limits.

## Do by hand (need `sudo` or a decision)

### Host, recommended
```bash
# GPU inside Docker (optional but useful for YOLO on the GPU in ROS nodes)
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html
sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker
# Then ./docker/run.sh adds --gpus all automatically. The container image has CPU torch only if built with `bash scripts/build_image.sh --torch`;
# to use the GPU inside the container: pip3 install torch torchvision (CUDA wheels) there.

# Debug / hacking tools
sudo apt install -y wireshark android-tools-adb mosquitto-clients jq curl git-lfs
# Display for container GUI apps
sudo apt install -y x11-xserver-utils      # provides xhost
```

### Install on demand, inside the container (a few minutes each)
| Need | Command |
|---|---|
| Gesture HRI | `pip3 install mediapipe "numpy<2"` |
| Speech | `pip3 install faster-whisper` |
| Open-vocab / CLIP | `pip3 install open_clip_torch transformers` |
| AprilTags w/o ROS | `pip3 install pupil-apriltags` |
| Multi-robot | `pip3 install pyrvo2` · `crazyswarm2` from source: https://imrclab.github.io/crazyswarm2 |
| Spot | `git clone https://github.com/bdaiinstitute/spot_ros2` (needs the SDK `pip install bosdyn-client`) |

Packages installed inside a running container are lost when it exits (`--rm`). To keep them, add them to the Dockerfile and rebuild: `bash scripts/build_image.sh` (add `--torch` for PyTorch/YOLO).

## Python quick-reference by track
| Track | Python libs |
|---|---|
| 01 Navigation | `rclpy`, `nav2_simple_commander`, `transforms3d`, `numpy`, `matplotlib` |
| 03 Vision | `cv_bridge`, `opencv`, `ultralytics`, `torch`, `open_clip_torch` |
| 04 Imitation | `torch`, `lerobot`, `gymnasium`, `numpy`, `h5py`/`pandas` for datasets |

## Pre-download list (Wi-Fi at the event will be crowded)
- YOLO: `yolov8n.pt`, `yolov8s.pt`, `yolov8n-seg.pt`, `yolov8s-worldv2.pt` → `challenges/03_computer_vision_ai/models/`
  `python3 -c "from ultralytics import YOLO; [YOLO(m) for m in ['yolov8n.pt','yolov8s.pt','yolov8n-seg.pt','yolov8s-worldv2.pt']]"`
- LeRobot datasets/policies: `lerobot/pusht`, `lerobot/diffusion_pusht` (cached in `~/.cache/huggingface`)
- Docker base images: `docker save` your image to a tarball for teammates.
- Docs offline: Nav2, ROS 2 Humble tutorials, Ultralytics, LeRobot (print to PDF).
