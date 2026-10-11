# ANT1 later steps: RealSense D555 camera, Crazyflie drones, teammates (research of 10 Oct 2026)

Not built yet. This is the researched plan for steps 5–7 of the roadmap, so it doesn't have to be looked up again.
Current state and steps 1–4: [05_ANT1_HANDOFF_AND_LESSONS.md](05_ANT1_HANDOFF_AND_LESSONS.md).

## Mission (user's goal)
The ANT1 explores and maps the area; **Crazyflie 2.x drones land on its top plate** (600×400 mm, flat, M7 holes).

Stretch goals:
- the ANT1 finds and drives to the drones;
- later it **sees the drones with its camera**.

Order: step by step, own laptop first, teammates later.

---

## 1. Intel RealSense D555 (camera; not connected yet)

**Specs:**
- **Depth:** stereo, up to 1280×720 @ up to 90 fps, FOV 87°×58°, min distance ~26 cm.
- **RGB:** 1280×800 @ up to 60 fps. **Global shutter** on depth and RGB, so drones don't smear.
- **Built-in IMU.**
- **Body:** IP65, 5.5 W, 167×42×48 mm.

**Connections:**
- **PoE+** (RJ45, IEEE 802.3at, gigabit). The ANT1 has GbE/**PoE+** ports.
- **USB-C**, which also supplies power.
- **The camera's own computer streams natively over DDS** ("SafeDDS", interoperable with Fast DDS).

**Ethernet defaults (from RealSense's PoE setup guide):**
- camera IP **192.168.11.55/24**, host e.g. **192.168.11.70/24**;
- **MTU 9000** (jumbo frames) on the host interface. Check with `ping -M do -s 8972 192.168.11.55`.

**How to use it with ROS 2 (what works in practice):**
- **Use Intel's driver `realsense2_camera`** (realsense-ros ≥ 4.56.4, librealsense ≥ 2.56.4).
  - Over Ethernet, librealsense must be **built with `-DBUILD_WITH_DDS=ON`**.
  - The driver gives standard `sensor_msgs/Image` topics such as `/<ns>/<camera_name>/color/image_raw`.
- **Don't subscribe to the camera's raw native DDS topics** (`rt/realsense/D555_<serial>_Color` …). Husarion users with CycloneDDS got type-hash errors and malformed packets, and only colour worked.
  - Put the camera on its **own DDS domain**: `rs-dds-config --domain-id 60`.
  - Let the driver republish into the ROS domain.
- RealSense maintainers said native SafeDDS streaming is officially only supported on **Humble**. Our container is Humble, the robot is Jazzy.
- **Known issues:**
  - over DDS: topics visible but no data, unless the USB cable is unplugged ("USB must be unplugged for DDS mode");
  - firmware must match the SDK version (e.g. FW 7.56.19918.835 for SDK 2.56.4);
  - in Docker, add `-v /dev:/dev` for device detection;
  - set stream QoS to Best-Effort;
  - `initial_reset:=true` helps.
- **Easiest path:** the D555 over **USB-C into the laptop** + `ros-humble-realsense2-camera` in our image.
  - Add a *separate* `RUN apt-get install` layer at the end of `docker/Dockerfile`, so the 1.7 GB pip layer isn't rebuilt.
  - Add `-v /dev:/dev` in `docker/run.sh`.

**Where the driver runs:**
- **(a) Laptop rides on the robot:** easiest; the payload of 60 kg is plenty. Camera on USB-C or PoE to the laptop.
- **(b) Laptop stationary on Wi-Fi:** the camera plugs into the robot's PoE port, and the driver must run **on the robot**. That needs SSH and installing software on the robot (mentor OK). The robot has **no RealSense driver** installed (checked via `vizanti/list_packages`).
- **Bandwidth:** raw depth is ~25 MB/s, too much for Wi-Fi. Send compressed RGB, low-rate depth, or only results.

**What it enables:**
- YOLO + depth → 3D object position → map → Nav2 goal. That's the planned chain: `challenges/03_computer_vision_ai/src/yolo_node.py` → `exercises/04_geometry_3d.md` → `ant1_goto`.
- RGB-D SLAM / 3D map (`ros-humble-rtabmap-ros`), exportable as `.ply`.
- 3D obstacles above the lidar plane (tables, overhangs) via a Nav2 voxel/obstacle layer or `depthimage_to_laserscan`.
- AprilTags (`apriltag_ros` is already in the image) for docking, landmarks and tagged drones.
- **Seeing drones:**
  - YOLO fine-tuned on venue photos (GPU venv) works only up close, because Crazyflies are ~9 cm.
  - Better: an AprilTag on the drone, or the LED-ring / active-marker deck (colour segmentation). Depth then gives the 3D position.
- Person following, gesture HRI; visual-inertial odometry.

**Mount:** add a static TF `base_link → camera_link` for the measured mount position (`static_transform_publisher`).

---

## 2. Crazyflie 2.x drones landing on the ANT1

**Communication:** a laptop with a **Crazyradio** USB dongle (2.4 GHz) runs **crazyswarm2** (ROS 2 Humble; build from source in `ws/src`) or `cflib` (already in our image). That laptop also gets the ANT1's pose over DDS, so it's the **bridge**: ANT1 pose in, drone `go_to`/`land` out. The drones never talk to the ANT1 directly.

**Positioning decides the method (ask which deck the drones have):**
- **Flow deck v2** (optical flow + height): positions are relative to the takeoff point.
  - Take off **from** the ANT1.
  - Record the ANT1 pose at takeoff.
  - Later fly to "ANT1 pose now − ANT1 pose at takeoff".
  - **Land only while the ANT1 is stationary.**
  - The height jumps ~15 cm over its top, so descend slowly.
  - Put a textured mat on the top plate so the flow sensor has something to track.
- **Lighthouse / Loco positioning:** absolute room frame. Align it once with the ANT1 `map` frame (ANT1 at a known spot); then poses convert directly.

**Stages:**
1. The ANT1 explores and maps (done: SLAM + Nav2 + `ant1_goto`).
2. Crazyflies land on the ANT1: the ANT1 stops; the bridge sends `go_to` above the ANT1, then `land`. A 27 g Crazyflie can't trip the laser safety stop (floor plane only).
3. The ANT1 drives to the drones: crazyswarm2 publishes drone poses → transform to `map` → `ant1_goto` (sideways driving helps the final alignment).
4. The ANT1 sees the drones with the D555 (see above).

The lidar can't see anything in the air (single plane ~10 cm above the floor): drones are invisible to it.

---

## 3. Getting data to teammates / other machines

| Channel | Protocol / port | Use |
|---|---|---|
| ROS 2 | DDS/RTPS over UDP. Domain 0: discovery multicast `239.255.0.1:7400`, data unicast 7410+. CycloneDDS | everything ROS. Humble ↔ Jazzy works at the topic level |
| rosbridge | JSON over **WebSocket `ws://<robot-ip>:5001`** (verified) | machines without ROS (Python, JS, dashboards) |
| Web UI / Vizanti / File Browser | HTTP :80 / :5000 / :9090 | status, map view, downloading maps and bags |
| Olive IMU JSON export | UDP/TCP, configured in the Web UI | IMU data without ROS |

**Ways to share data:**
1. **Same network (our phone hotspot), same domain 0, CycloneDDS:** teammates see everything natively, with any distro. Teammates without ROS: `docker save hackathon-ros:humble | gzip > hackathon-ros.tar.gz` → USB stick → `docker load`.
2. If a network drops multicast: `ANT1_PEER=<robot-ip>` (unicast discovery, already in `scripts/ant1_env.sh`).
3. If the robot is on a network the teammates can't join: **`zenoh-bridge-ros2dds`** on both sides, or rosbridge.
4. Offline: `ros2 bag record` (MCAP), saved maps (PGM/YAML), `.ply`.

**On a shared network:** all ANT1s may be `id001` on domain 0, so **your `cmd_vel` could drive other teams' robots**. Change the domain ID in the robot Web UI first.

---

## Sources
- Olive docs: https://docs.olive-robotics.com/Products/olixBot%E2%84%A2ANT1-ProUltra/SoftwareDevelopment (also `/GettingStarted`, `/Specifications`)
- D555 product page: https://www.realsenseai.com/products/d555-poe/
- D555 PoE setup guide: https://realsenseai.com/wp-content/uploads/2025/12/D555_PoESetupGuide-Rev001.pdf
- Husarion D555 + CycloneDDS thread: https://community.husarion.com/t/panther-robot-integrating-realsense-d555-urdf-and-cyclonedds-communication-issues/2194
- librealsense issue #14532 (D555 DDS on Jazzy): https://github.com/realsenseai/librealsense/issues/14532
- realsense-ros: https://github.com/realsenseai/realsense-ros
- Olive repo (rviz configs, waypoint_server_interfaces): https://github.com/olive-robotics/olvx_g1
