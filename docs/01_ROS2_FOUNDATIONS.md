# ROS 2 foundations: read this before any challenge notes

Everything in the hackathon sits on top of this. Aim: after this file you can read any ROS 2 code and know what it does.

## 1. What ROS 2 is
A set of libraries + tools for building robot software as **many small programs (nodes)** that talk by **messages**. Not an OS. You write nodes in Python (`rclpy`) or C++ (`rclcpp`). We use **Humble** (LTS, 2022); the robots at the event are mostly Humble.

## 2. Core concepts (with the commands that show them)

### Node
A running program with a name. `ros2 node list`, `ros2 node info /node_name`.

### Topic (publish/subscribe, many-to-many, fire-and-forget)
A named stream with a **message type**. Publishers send, subscribers receive.
```bash
ros2 topic list -t             # names + types
ros2 topic echo /scan          # print messages
ros2 topic hz /scan            # rate
ros2 topic info /scan -v       # who publishes/subscribes + QoS
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.1}}"   # publish by hand
```
Messages you will meet constantly:
| Type | Meaning | Key fields |
|---|---|---|
| `geometry_msgs/Twist` | velocity command | `linear.x` (m/s forward), `angular.z` (rad/s turn left+) |
| `sensor_msgs/LaserScan` | 2D lidar | `ranges[]`, `angle_min`, `angle_increment`, `range_max` |
| `sensor_msgs/Image` | camera frame | `data`, `encoding` (bgr8/rgb8/mono8), `header.stamp` |
| `sensor_msgs/CameraInfo` | camera intrinsics | `k` (3×3 matrix) |
| `nav_msgs/Odometry` | where the robot thinks it is | `pose.pose`, `twist.twist` |
| `geometry_msgs/PoseStamped` | pose + frame + time | `header.frame_id`, `pose.position`, `pose.orientation` (quaternion) |
| `nav_msgs/OccupancyGrid` | the map | `data[]` (0 free,100 occupied,-1 unknown), `info.resolution` |
| `tf2_msgs/TFMessage` | coordinate transforms | see TF |
Inspect any: `ros2 interface show sensor_msgs/msg/LaserScan`.

### Service (request/response, like a function call)
`ros2 service list`, `ros2 service call /reset_simulation std_srvs/srv/Empty`.

### Action (long-running goal with feedback + cancel)
Used by Nav2: "navigate to this pose": gives progress and can be cancelled. `ros2 action list`.

### Parameter
Per-node config values. `ros2 param list /node`, `ros2 param set /node name value`.

### Launch file
Python script starting many nodes with parameters/remaps. `ros2 launch <package> <file>.launch.py`. Used everywhere; the team template is `ws/src/team_pkg/launch/hello.launch.py`.

### Package / workspace
Package = unit of code (`package.xml` + `setup.py`). Workspace = folder with `src/`; `colcon build` makes `install/`; `source install/setup.bash` registers it.

## 3. TF2: coordinate frames (the #1 source of bugs)
Every sensor/robot part has a **frame**; TF is a tree of transforms (position+rotation) between frames, with timestamps.
```
map ──► odom ──► base_footprint ──► base_link ──► base_scan (lidar)
                                          └──► camera_link ──► camera_rgb_optical_frame
```
- **odom**: smooth, drifts over time (wheel odometry). **map**: globally correct but can jump when localization corrects. `map→odom` = the correction, published by SLAM/AMCL.
- Camera *optical* frame convention: x right, y down, z forward. Robot convention: x forward, y left, z up. They differ: this trips everyone.
- Tools: `ros2 run tf2_tools view_frames` (→ `frames.pdf`), `ros2 run tf2_ros tf2_echo map base_link`.
- In code: use `tf2_ros.Buffer` + `TransformListener`; transform with the **message's timestamp**, not "now".
- Errors like "Could not transform ... frame does not exist" or "extrapolation into the future" = missing/late transform, or `use_sim_time` mismatch.

## 4. QoS (Quality of Service): why a subscriber receives nothing
Publisher and subscriber must have **compatible** QoS or they silently don't connect.
- Sensors publish **BEST_EFFORT** (drop OK, low latency). A default (RELIABLE) subscriber is incompatible → no data.
- In Python for sensor topics: `from rclpy.qos import qos_profile_sensor_data` and pass it to `create_subscription`.
- Map topics use **TRANSIENT_LOCAL** (late joiners still get the last map).
- Diagnose: `ros2 topic info /scan -v` and compare the "Reliability" lines.

## 5. DDS, domains, and networking
ROS 2 uses DDS underneath for discovery. Machines on the same network with the same **`ROS_DOMAIN_ID`** (0-101) see each other's topics automatically.
- Different team = different ID, or you hear everybody's robots. Our container default is **42**; change with `export ROS_DOMAIN_ID=17`.
- `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` (our default) vs `rmw_fastrtps_cpp` (Humble default). Mismatches with a robot may hide topics; switch to match the robot.
- Multicast blocked on Wi-Fi/5G? Discovery fails: ask mentors; Cyclone can use a unicast peer list (`CYCLONEDDS_URI`).
- `ROS_LOCALHOST_ONLY=1` isolates ROS to your machine (useful when practising at home to avoid noise).
- Simulated time: Gazebo publishes `/clock`; nodes use `use_sim_time:=true`. On real robots it must be **false**.

## 6. Writing a node (Python template)
```python
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist

class MyNode(Node):
    def __init__(self):
        super().__init__("my_node")
        self.create_subscription(LaserScan, "scan", self.on_scan, qos_profile_sensor_data)
        self.pub = self.create_publisher(Twist, "cmd_vel", 10)
        self.create_timer(0.1, self.tick)        # 10 Hz loop
    def on_scan(self, msg): self.last = msg
    def tick(self): ...                           # compute + publish

def main():
    rclpy.init(); rclpy.spin(MyNode())
```
Patterns used in this repo: topic names are *relative* (`scan`, not `/scan`) so you can namespace/remap: `--ros-args -r scan:=/robot1/scan`. Always keep a **watchdog** (stop if no data) and **speed clamps**.

## 7. Tools you'll use daily
| Tool | Use |
|---|---|
| `rviz2` | visualise scans, maps, TF, paths, images, markers. Set **Fixed Frame**, then Add display by topic |
| `rqt_graph` | picture of nodes+topics (is my node actually connected?) |
| `rqt_image_view` | see camera/annotated images |
| `ros2 bag` | record/replay: develop vision/learning with no robot |
| `PlotJuggler` | plot numeric topics (`plotjuggler`) |
| `colcon` | build |
| `ros2 doctor` | environment diagnostics |

## 8. Debugging checklist (in this order)
1. Is the node running? `ros2 node list`
2. Is the topic there and the right type? `ros2 topic list -t`
3. Is data flowing? `ros2 topic hz`, `echo`
4. QoS compatible? `ros2 topic info -v`
5. Right frame / TF present? `view_frames`, `tf2_echo`
6. Sim time consistent? `use_sim_time` on all nodes
7. Same domain ID / RMW as the robot?
8. Read the **first** error message in the log, not the last.

## 9. Study plan (≈6–8 h): official tutorials + our checks
Official: https://docs.ros.org/en/humble/Tutorials.html: do **Beginner: CLI tools** (all) and **Beginner: Client libraries** (publisher/subscriber Python, services, parameters, launch, tf2 intro). Skim Intermediate: tf2, QoS.
Then verify yourself (without looking at solutions):
- [ ] Publish a `Twist` from the CLI and watch the simulated robot move.
- [ ] Write a node that subscribes to `/scan` and prints the closest obstacle.
- [ ] Write a launch file that starts it with a parameter `stop_distance`.
- [ ] Record a bag, replay it, and see the same data in rviz.
- [ ] Draw the TF tree and explain every arrow.
- [ ] Reproduce a QoS mismatch on purpose, and fix it.
