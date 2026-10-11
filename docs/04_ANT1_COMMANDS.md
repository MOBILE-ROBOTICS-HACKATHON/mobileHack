# ANT1 command cheat sheet

Every command for working with the Olive ANT1 from this workspace, in the order you use them.
Background and explanations: [02_ANT1.md](02_ANT1.md). First-drive tutorial: [03_ANT1_FIRST_DRIVE.md](03_ANT1_FIRST_DRIVE.md).

`HOST` = normal laptop terminal · `CONTAINER` = inside `hackathon-ros:humble` (`./docker/run.sh`).
`$NS` = `/olive/olixRobot/ant1/id001` (set by `scripts/ant1_env.sh`).

> **Safety rules (the ANT1 has NO command timeout: it keeps the last command forever)**
> 1. E-stop within reach, always. Robot on the floor, ~1 m clear, charger unplugged.
> 2. `ant1_watchdog` running in its own terminal the whole session.
> 3. Stream commands at ≥ 5 Hz (`-r 10`), and end every motion with a zero Twist.
> 4. **Before releasing the e-stop, send a stop first** (section 5).
> 5. On the cable: don't turn more than ~90° one way (the cable wraps around the robot).

---

## 1. Power on (at the robot)
1. E-stop **pressed** → power button → wait ~10 s → twist the e-stop to release (it only matters at boot; send a stop first if the robot was moving before, see section 5).
2. LED: green = ready · red = e-stop · blue = joystick manual mode (hold **L1**) · orange corners = laser safety stop.

## 2. HOST: check the link (Ethernet)
```bash
ip -br addr show enp2s0          # must show 192.168.7.200/24
ping -c 3 192.168.7.100          # robot answers
xhost +local:docker              # allow GUI windows from the container (run.sh does this too)
```
Web UIs in a browser: robot http://192.168.7.100 · network page http://192.168.7.100/network · map viewer http://192.168.7.100:5000 · files http://192.168.7.100:9090

## 3. HOST: open container terminals
```bash
cd ~/Desktop/University/Masters/semester2/Hackathon
./docker/run.sh                  # terminal 1 (exit here = container stops, all terminals close)
./docker/exec.sh                 # every additional terminal
```

## 4. CONTAINER: in EVERY terminal
```bash
source scripts/ant1_env.sh                         # cable (enp2s0)
ANT1_IFACE=wlp3s0 source scripts/ant1_env.sh       # Wi-Fi / hotspot instead
```
Once per session (and after adding new nodes):
```bash
cd /hackathon/ws && colcon build --symlink-install && source install/setup.bash && cd /hackathon
```
`serdata.cpp ... not null-terminated` spam = harmless (Humble ↔ Jazzy).

## 5. CONTAINER: safety commands
```bash
ant1_watchdog                                                            # own terminal, keep running
ros2 topic pub -w 1 -r 10 -t 10 $NS/cmd_vel geometry_msgs/msg/Twist "{}"  # STOP (use before releasing e-stop)
ros2 topic echo --once $NS/ems                                           # true = e-stop pressed
ant1_param laser_safety_distance_cm                                      # built-in obstacle stop zone (default 19)
ant1_param laser_safety_distance_cm 30                                   # bigger margin (set back to 19 after)
ros2 service call $NS/laser_safety/enable std_srvs/srv/SetBool "data: true"   # make sure laser safety is ON
```

## 6. CONTAINER: look at the robot (like the turtlesim tutorial)
```bash
ros2 topic list | grep $NS                         # ~48 topics
ros2 topic info $NS/cmd_vel                        # geometry_msgs/msg/Twist
ros2 interface show geometry_msgs/msg/Twist
ros2 topic echo --once $NS/battery                 # %
ros2 topic echo --once $NS/status                  # CPU, disk, firmware, IP
ros2 topic hz $NS/scan                             # ~10 Hz
ros2 topic echo $NS/odom --field twist.twist       # measured velocity
ros2 topic echo $NS/cmd_vel                        # what is being commanded
```
Twist on the ANT1: `linear.x` forward/back · `linear.y` left/right (mecanum) · `angular.z` turn left (+) / right (−).

## 7. CONTAINER: move it
**By hand** (2 s each; the watchdog stops it afterwards):
```bash
ros2 topic pub -r 10 -t 20 $NS/cmd_vel geometry_msgs/msg/Twist "{angular: {z: 0.2}}"    # turn left ~23°
ros2 topic pub -r 10 -t 20 $NS/cmd_vel geometry_msgs/msg/Twist "{angular: {z: -0.2}}"   # turn right
ros2 topic pub -r 10 -t 20 $NS/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.05}}"    # forward 10 cm
ros2 topic pub -r 10 -t 20 $NS/cmd_vel geometry_msgs/msg/Twist "{linear: {x: -0.05}}"   # back 10 cm
ros2 topic pub -r 10 -t 20 $NS/cmd_vel geometry_msgs/msg/Twist "{linear: {y: 0.05}}"    # sideways left
ros2 topic pub -r 10 -t 20 $NS/cmd_vel geometry_msgs/msg/Twist "{linear: {y: -0.05}}"   # sideways right
```
**Arrow keys** (recommended; moves only while a key is held, 0.05 m/s / 0.2 rad/s, hard cap 0.15 / 0.5):
```bash
ant1_keys                                    # ↑↓ drive · ←→ turn · a/d sideways · +/- faster/slower · space stop · q quit
ant1_keys -p speed:=0.1 -p turn:=0.3         # a bit faster
```
**Timed moves** (our node, zeros at the end / on Ctrl-C / closed terminal):
```bash
ant1_drive -p vx:=0.05 -p secs:=2.0          # forward 10 cm
ant1_drive -p vy:=0.05                       # sideways left
ant1_drive -p wz:=0.2                        # turn left
ant1_drive -p demo:=true                     # fwd, back, left, right, turn L, turn R (20 cm each)
```
**Other drivers** (need `ant1_watchdog`; they don't stop by themselves):
```bash
ant1_teleop                                  # teleop_twist_keyboard: i/,/j/l, Shift+keys sideways, k stop
ant1_steer                                   # GUI sliders: type $NS/cmd_vel into its topic box first
```

## 8. CONTAINER: see it (GUI windows appear on your screen)
```bash
ant1_rviz                                    # top-down view: robot axes, red odom trail, cyan lidar
ros2 run plotjuggler plotjuggler             # ROS2 Topic Subscriber → $NS/odom; drag x+y together = path plot
rqt                                          # Topic Monitor, Plot, Console (robot logs), TF Tree, Bag
ros2 run tf2_tools view_frames               # PDF of the TF tree
```
TF frames (global `/tf`, `/tf_static`): `olive_olixRobot_ant1_id001_odom → _base_link → _laser → _laser_fl/fr/bl/br`.

## 9. CONTAINER: sensors and recording
```bash
ros2 topic echo --once --no-arr $NS/scan                 # fused 360°, 1441 rays, −π..π (front = middle)
ros2 topic echo --once --no-arr $NS/scan_fl              # raw corner lidar with intensities (fl/fr/bl/br)
ros2 topic hz $NS/s1/bm/imu                              # IMUs ~105 Hz (fl/fr/bl/br/bm)
python3 challenges/01_autonomous_navigation/src/obstacle_stop.py --ros-args -r __ns:=$NS   # drive + turn at obstacles
ros2 bag record -o ant1_run1 $NS/scan $NS/odom $NS/cmd_vel /tf /tf_static              # record every run
ros2 bag play ant1_run1                                  # replay (watch in ant1_rviz)
ros2 service call $NS/STL27L_bl/change_state lifecycle_msgs/srv/ChangeState "{transition: {id: 4}}"   # lidar off (3 = on)
ros2 topic pub --once $NS/s1/bl/user/led_rgb std_msgs/msg/Float32MultiArray "{data: [1.0, 0.0, 0.0]}"  # LED red
ros2 topic pub --once $NS/s1/bl/user/led_rgb std_msgs/msg/Float32MultiArray "{data: [0.0, 1.0, 0.0]}"  # LED green
```

## 10. Wi-Fi (robot + laptop on one private network)
Not eduroam: it needs a username login, which the robot can't do, and it blocks device-to-device traffic. The robot stays still during setup.
```bash
# HOST, option A (recommended): both join your PHONE hotspot (iPhone: "Maximize Compatibility"); laptop keeps internet
nmcli device wifi connect "<phone-ssid>" password "<password>"
# HOST, option B: LAPTOP hotspot (most reliable). Internet via phone USB tethering (plug phone in, enable USB tethering)
nmcli device wifi hotspot ifname wlp3s0 ssid ant1-net password 'pick-8+-chars' band bg
```
Browser (cable still plugged in): http://192.168.7.100/network → Wi-Fi Configuration → enable `wlan0` → **Scan SSIDs** → phone SSID or `ant1-net` + password → **Test** → **Apply & Restart**.
Robot IP: shown on that page, or in the phone's device list (A), or via `ip neigh show dev wlp3s0` (B, 10.42.0.x).
If A gives ping but no topics: check `wlan0` is in the robot's DDS config, then try `ANT1_PEER`; only then use B. Option C, staying on the cable, is fine while developing.
```bash
# HOST: check the robot
ping -c 3 <robot-wifi-ip>
```
**The robot's DDS must have `wlan0` enabled** (Web UI → Configuration → CycloneDDS file; mentor OK first; original in `docs/ant1_cyclonedds_original.xml`). Then Restart Services.
Unplug the cable, then in **every** container terminal (restart `ant1_watchdog` and `ant1_rviz` too):
```bash
ANT1_IFACE=wlp3s0 source scripts/ant1_env.sh                             # Wi-Fi (tested OK on the phone hotspot)
ANT1_IFACE=wlp3s0 ANT1_PEER=<robot-wifi-ip> source scripts/ant1_env.sh   # fallback if a network drops multicast
ros2 topic list | grep -c $NS                # ~48
ros2 topic hz $NS/scan                       # ~10 Hz
```
Back to normal:
```bash
source scripts/ant1_env.sh                   # CONTAINER: cable again (plug it back in)
nmcli connection up eduroam                  # HOST: back to eduroam (ends option B's hotspot)
```
If the Wi-Fi drops while the robot is moving, nothing can stop it except the e-stop or its laser safety zone. Drive slowly and stay within about 10 m.

## 11. Map and drive to coordinates (robot's onboard SLAM + Nav2)
1. Web UI → **SLAM** → Robot Control → **Mapping** → start. It needs all lidars active; see the last bullet if only manual driving is allowed.
2. CONTAINER:
```bash
ant1_watchdog                       # terminal 1, as always
ant1_rviz                           # terminal 2: map, green planned path, costmap, yellow footprint
ant1_nav_speed                      # terminal 3: once per robot boot, robot STANDING STILL (restarts Nav2 ~10 s, map kept)
ant1_goto 1.0 0.5                   # drive to x=1.0, y=0.5 (map frame, metres), keeping its heading; Ctrl-C = cancel + stop
ant1_goto 1.0 0.5 90                # ... and end facing 90° (+y)
ant1_goto 1.0 0.5 face              # ... and end facing the direction it travelled
ant1_goto 2.7 1.0                   # a box at (2.7, 1.0): goes to the closest reachable point next to it
ant1_nav_speed 0.1 0.3              # slower (default 0.2 m/s, 0.5 rad/s)
ant1_nav_speed --static-map         # plan on the stored SLAM map again (static rooms); default = live lidar
ant1_nav_speed 0.3 0.6 --live       # change speed ON THE FLY, also mid-goal (no restart; ~8 s over Wi-Fi to connect)
ant1_nav_speed +0.1 --live          # relative: +0.1 m/s on top of the current speed (turn unchanged); -0.1 = slower
ant1_nav_speed +0.1 +0.2 --live     # relative speed AND turn; capped at 0.5 m/s, 1.0 rad/s
```
**What `ant1_nav_speed` sets** (Olive default in brackets; all reset on reboot):

| Setting | Value |
|---|---|
| speed / turn | 0.2 m/s / 0.5 rad/s [0.3 / 0.65] |
| driving directions | forward, **reverse, sideways** [forward + turn only] |
| "nose along the path" scoring | off [on], so it slides instead of turning |
| obstacle clearance | 0.25 m, steeper cost [0.325 m], so it passes closer |
| goal reached within | 0.3 m / 0.3 rad [0.25 m / 0.1 rad] |
| controller may fail for | 1 s [0.3 s] |
| progress check | 0.25 m in 10 s [0.5 m in 2 s, which aborts slow drives] |
| recovery spin | at most 0.5 rad/s [1.0 rad/s] |
| robot laser safety stop | 19 cm (Olive's default) |
| **planner obstacles** | **live lidar** in a 25×25 m window around the robot, marked up to 10 m and cleared up to 12 m [the stored SLAM map + lidar within 2.5 m]. In this room 22 % of the SLAM map's obstacles were ghosts (moved chairs, people) on 10 Oct; the planner detoured around them or found no path. `ant1_nav_speed --static-map` goes back to Olive's map-based planning. |

**`ant1_goto`:**
- **It checks reachability first** on the robot's costmap: is there a gap wide enough for the 60×40 cm body all the way? If the goal is inside an object, in a closed-off pocket, or outside the map, it drives to the **closest reachable point** and says so. Unreachable goals were the cause of "rotates on the spot and gives up" (10 Oct): the planner finds no path, and Nav2 only spins, waits and backs up.
- When Nav2 gives up, it retries 3 times (`-p retries:=N`).
- It re-sends goals lost over Wi-Fi, and it prints Nav2's warnings.

**Map frame:** the origin is where the robot stood when Mapping started; +x is the way it faced, +y is to its left.

**Use `ant1_goto` rather than goal clicks in rviz:** the robot clock is ~76 s behind the laptop, and `ant1_goto` sends stamp 0. The Web UI's "Set Goal Pose" also works.

Nav2 runs on the robot itself, so a Wi-Fi dropout doesn't stop a running goal, and the robot's own velocity smoother stops the robot if Nav2 stops.

**Lidars "inactive" (only manual driving allowed):** power-cycle with the e-stop pressed for ~10 s after power-on.

## 12. Fixes
```bash
# topics stuck after a network change (CONTAINER)
pgrep -f "ros2cli.daemon|ros2-daemon" | xargs -r kill -9; rm -rf ~/.ros/daemon; ros2 daemon start
# a container named "hackathon" is already running / stuck (HOST)
docker ps
docker stop hackathon
# close a stray rviz container (HOST)
docker stop ant1_rviz
```
| Symptom | Fix |
|---|---|
| no `$NS` topics | `source scripts/ant1_env.sh` in this terminal; check the cable / `ping`; right `ANT1_IFACE` |
| command sent, robot still | `ems` true (e-stop)? orange LEDs (obstacle in safety zone)? joystick manual mode (L1)? |
| `ant1_keys` not found | `colcon build --symlink-install && source install/setup.bash` in `/hackathon/ws` |
| `ros2 param` / `ros2 node list` show nothing | Humble can't see Jazzy nodes: use `ant1_param` |
| GUI window doesn't open | HOST: `xhost +local:docker` |
