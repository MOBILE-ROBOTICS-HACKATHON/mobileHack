#!/usr/bin/env bash
# Start (or re-enter) the ROS 2 Humble dev container.
#   ./docker/run.sh            -> open a shell in the container
#   ./docker/run.sh <command>  -> run a command, e.g. ./docker/run.sh ros2 topic list
# Open more terminals into the SAME running container with ./docker/exec.sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME=hackathon
IMAGE=hackathon-ros:humble

# Allow the container to draw windows (rviz2 / gazebo) on the host display (X11 / XWayland).
xhost +local:docker >/dev/null 2>&1 || echo "[warn] xhost failed: GUI apps may not open"

if docker ps --format '{{.Names}}' | grep -qx "$NAME"; then
  exec docker exec -it "$NAME" bash -ic "${*:-bash}"
fi
docker rm -f "$NAME" >/dev/null 2>&1 || true

EXTRA=()
# Webcam passthrough if present
for v in /dev/video*; do [ -e "$v" ] && EXTRA+=(--device "$v"); done
# USB (Crazyradio): bind /dev/bus/usb so a dongle plugged in AFTER start still appears, and join the
# host's plugdev group, which the udev rule (/etc/udev/rules.d/99-bitcraze.rules) gives access to.
EXTRA+=(-v /dev/bus/usb:/dev/bus/usb)
PLUGDEV=$(getent group plugdev | cut -d: -f3); [ -n "$PLUGDEV" ] && EXTRA+=(--group-add "$PLUGDEV")
# NVIDIA GPU inside the container only if the NVIDIA container toolkit is installed (see PACKAGES.md)
if docker info 2>/dev/null | grep -qi nvidia; then EXTRA+=(--gpus all -e NVIDIA_DRIVER_CAPABILITIES=all); fi

exec docker run -it --rm --name "$NAME" \
  --net=host --ipc=host --privileged \
  -e DISPLAY="$DISPLAY" -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$ROOT":/hackathon \
  "${EXTRA[@]}" \
  "$IMAGE" bash -ic "${*:-bash}"
