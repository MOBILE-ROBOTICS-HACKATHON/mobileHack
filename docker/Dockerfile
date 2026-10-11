# ROS 2 Humble: the distro most hackathon robots support
# (Crazyflie, Spot, Olive ANT, ModalAI Starling, TurtleBot).
# The host is Ubuntu 26.04, which has no native Humble packages, so we use Docker.
# Build (teammates too, from the repo folder):   bash scripts/build_image.sh          (light, ~20-30 min)
#                                                 bash scripts/build_image.sh --torch  (+ PyTorch/YOLO, +~2.5 GB)
# Guide: docs/11_DOCKER_IMAGE_AND_SHARING.md
FROM osrf/ros:humble-desktop-full

ARG USERNAME=hack
ARG UID=1000
ARG GID=1000
ENV DEBIAN_FRONTEND=noninteractive

# ---- ROS 2 packages (navigation, sim, vision, HRI, tooling) ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-navigation2 ros-humble-nav2-bringup ros-humble-nav2-simple-commander \
    ros-humble-slam-toolbox ros-humble-robot-localization \
    ros-humble-turtlebot3 ros-humble-turtlebot3-gazebo ros-humble-turtlebot3-msgs \
    ros-humble-turtlebot3-navigation2 ros-humble-turtlebot3-cartographer \
    ros-humble-gazebo-ros-pkgs ros-humble-gazebo-ros2-control \
    ros-humble-teleop-twist-keyboard ros-humble-teleop-twist-joy \
    ros-humble-tf2-tools ros-humble-tf-transformations \
    ros-humble-cv-bridge ros-humble-vision-opencv ros-humble-image-transport \
    ros-humble-v4l2-camera ros-humble-image-tools ros-humble-apriltag-ros \
    ros-humble-rosbridge-suite ros-humble-rqt* ros-humble-plotjuggler-ros \
    ros-humble-rmw-cyclonedds-cpp ros-humble-xacro \
    python3-pip python3-colcon-common-extensions python3-rosdep python3-vcstool \
    git curl wget nano vim tmux htop iputils-ping net-tools nmap \
    mesa-utils sudo bash-completion libusb-1.0-0 libxcb-cursor0 libxcb-xinerama0 libxkbcommon-x11-0 \
 && rm -rf /var/lib/apt/lists/*

# ---- Python: vision + science basics (no PyTorch here, see WITH_TORCH below) ----
# numpy<2 is REQUIRED: Humble's cv_bridge is compiled against numpy 1.x.
RUN pip3 install --no-cache-dir --timeout 120 --retries 10 "numpy<2" "opencv-python-headless<4.11" \
    scipy matplotlib pandas scikit-learn transforms3d pyyaml

# ---- Crazyflie 2.x drones: crazyswarm2 (ROS 2 stack, binary), cfclient GUI, cflib ----
# Own layer so adding it doesn't rebuild the big layers above. numpy<2 kept for cv_bridge.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-crazyflie ros-humble-crazyflie-py ros-humble-crazyflie-examples \
    ros-humble-crazyflie-interfaces ros-humble-crazyflie-server-cpp ros-humble-crazyflie-server-py \
    ros-humble-motion-capture-tracking \
 && rm -rf /var/lib/apt/lists/* \
 && pip3 install --no-cache-dir "numpy<2" rowan cflib cfclient

# ---- OPTIONAL: PyTorch (CPU) + YOLO, only with --build-arg WITH_TORCH=1 (GPU training runs in the host venv) ----
# Only challenges/03 (YOLO) and challenges/04 (imitation learning) use them; the robot / drone / mission / vision
# tools don't. Declared HERE (not at the top) so changing it doesn't rebuild the layers above.
ARG WITH_TORCH=0
RUN if [ "$WITH_TORCH" = "1" ]; then \
      pip3 install --no-cache-dir --timeout 120 --retries 10 "numpy<2" torch torchvision \
        --index-url https://download.pytorch.org/whl/cpu \
   && pip3 install --no-cache-dir --timeout 120 --retries 10 "numpy<2" ultralytics ; \
    else echo "light image: no PyTorch/YOLO (WITH_TORCH=0)"; fi

# ---- non-root user matching the host UID so files in the workspace aren't root-owned ----
RUN (getent group ${GID} || groupadd -g ${GID} ${USERNAME}) \
 && useradd -m -u ${UID} -g ${GID} -s /bin/bash ${USERNAME} 2>/dev/null || true \
 && echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME}

USER ${USERNAME}
ENV TURTLEBOT3_MODEL=waffle \
    GAZEBO_MODEL_PATH=/opt/ros/humble/share/turtlebot3_gazebo/models \
    RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
    ROS_DOMAIN_ID=42
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc \
 && echo "[ -f /hackathon/ws/install/setup.bash ] && source /hackathon/ws/install/setup.bash" >> ~/.bashrc \
 && echo "source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash" >> ~/.bashrc \
 && echo "source /usr/share/gazebo/setup.sh" >> ~/.bashrc \
 && echo "cd /hackathon" >> ~/.bashrc
WORKDIR /hackathon
CMD ["bash"]
