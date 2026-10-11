# Tutorial: first drive of the ANT1 (like turtlesim, on a real robot)

Goal: move the ANT1 slowly from your laptop by publishing to a topic, first by hand and then with the arrow keys.
In turtlesim you drove `/turtle1/cmd_vel`; here it is `/olive/olixRobot/ant1/id001/cmd_vel` (`$NS/cmd_vel`).
Speeds stay at **0.05 m/s and 0.2 rad/s**. That's 5 cm per second, slower than walking.

## Step 0: Physical safety (before any command)
- Robot on the floor (never on a table), about 1 m of free space all around.
- **E-stop within reach.** Pressing it cuts motor power instantly; twist it to release.
- **The Ethernet cable is a leash.**
  - Lay 1–2 m of slack on the floor and keep the laptop on a table next to the robot.
  - **Don't turn more than about 90° in one direction**, or the cable wraps around the robot. Turn back the same amount.
  - Alternatively, secure the laptop on the robot's top plate.
- Charger cable disconnected (the robot must not move while charging).

## Step 1: HOST, check the link
```bash
ip -br addr show enp2s0          # must show 192.168.7.200/24
ping -c 3 192.168.7.100          # robot answers
```

## Step 2: HOST, terminal 1: enter the ROS container
```bash
cd ~/Desktop/University/Masters/semester2/Hackathon
./docker/run.sh                  # prompt becomes hack@...:/hackathon$
```

## Step 3: CONTAINER, terminal 1: robot settings and build (once per session)
```bash
source scripts/ant1_env.sh       # domain 0, CycloneDDS on Ethernet, $NS, helpers
cd ws && colcon build --symlink-install && source install/setup.bash && cd ..
```
The `serdata.cpp ... not null-terminated` messages are harmless noise (Humble talking to Jazzy).

## Step 3b: HOST, terminal 2: start the watchdog (keep it running all session)
**The ANT1 has no command timeout.** It keeps executing the last `cmd_vel` forever. We found this on 10 Oct: after a `-t 20` turn command ended, it kept turning until the e-stop. The watchdog sends STOP when commands stop arriving for 0.5 s.
```bash
./docker/exec.sh
source scripts/ant1_env.sh
ant1_watchdog
```
It can't help if the laptop or the cable or Wi-Fi dies, because then no message reaches the robot. **The e-stop stays in reach.**
**Before releasing the e-stop, always send a stop first**, or the robot may resume its last command:
`ros2 topic pub -w 1 -r 10 -t 10 $NS/cmd_vel geometry_msgs/msg/Twist "{}"`

## Step 4: Look before you drive (as in the turtlesim tutorial)
```bash
ros2 topic list | grep cmd_vel                    # /olive/olixRobot/ant1/id001/cmd_vel
ros2 topic info $NS/cmd_vel                       # type geometry_msgs/msg/Twist, robot subscribes
ros2 interface show geometry_msgs/msg/Twist       # linear x/y/z, angular x/y/z
ros2 topic echo --once $NS/battery                # charge %
ros2 topic echo --once $NS/ems                    # must be "data: false" (e-stop released)
```
Twist on the ANT1: `linear.x` = forward (+) / back (−), `linear.y` = left (+) / right (−) (mecanum), `angular.z` = turn left (+) / right (−).

**Optional extra margin:** make the built-in obstacle stop zone bigger (default 19 cm). Restore it afterwards with the same command and `19`.
```bash
ant1_param laser_safety_distance_cm 30
```

## Step 5: HOST, terminal 3: watch it in rviz
```bash
./docker/exec.sh                 # second terminal into the same container
source scripts/ant1_env.sh
ant1_rviz                        # robot axes, red odometry trail, cyan lidar
```

## Step 6: CONTAINER, terminal 1: move with single topic commands
Each command publishes 20 messages at 10 Hz (2 s) and exits. **The robot would keep going after that.** The watchdog from Step 3b stops it 0.5 s later. Without the watchdog, send the stop line yourself right after each command.
```bash
# turn left in place: 0.2 rad/s × 2 s ≈ 23°
ros2 topic pub -r 10 -t 20 $NS/cmd_vel geometry_msgs/msg/Twist "{angular: {z: 0.2}}"
# turn back
ros2 topic pub -r 10 -t 20 $NS/cmd_vel geometry_msgs/msg/Twist "{angular: {z: -0.2}}"
# forward 10 cm, then back 10 cm
ros2 topic pub -r 10 -t 20 $NS/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.05}}"
ros2 topic pub -r 10 -t 20 $NS/cmd_vel geometry_msgs/msg/Twist "{linear: {x: -0.05}}"
# sideways left 10 cm, then right (only a mecanum robot can do this)
ros2 topic pub -r 10 -t 20 $NS/cmd_vel geometry_msgs/msg/Twist "{linear: {y: 0.05}}"
ros2 topic pub -r 10 -t 20 $NS/cmd_vel geometry_msgs/msg/Twist "{linear: {y: -0.05}}"
# explicit stop (always safe to send)
ros2 topic pub --once $NS/cmd_vel geometry_msgs/msg/Twist "{}"
```
Always stream commands at 5 Hz or more (`-r 10`). A slower stream looks like "commands stopped" to the watchdog.

## Step 7: HOST, terminal 4: see what you send and what the robot does
```bash
./docker/exec.sh
source scripts/ant1_env.sh
ros2 topic echo $NS/cmd_vel                         # commands (yours)
# or the robot's measured velocity:
ros2 topic echo $NS/odom --field twist.twist
```

## Step 8: Arrow keys (like `turtle_teleop_key`)
In terminal 1:
```bash
ant1_keys
```
```
  Up/Down    forward / backward        a / d   sideways left / right
  Left/Right turn left / right         space   stop        q   quit
```
- It moves **only while you hold a key**, and stops 0.6 s after you release it. Space stops instantly.
- Speed 0.05 m/s and turn 0.2 rad/s by default. Faster, only once you're comfortable: `ant1_keys -p speed:=0.1 -p turn:=0.3` (hard cap 0.15 m/s and 0.5 rad/s).
- Why not `ros2 run turtlesim turtle_teleop_key`? It sends one message per key press and has no stop key. On a real robot that can mean "keeps driving".

## Step 9: Finish
- `q` (or Ctrl-C) in `ant1_keys`; it sends zeros on exit.
- If you changed it: `ant1_param laser_safety_distance_cm 19`.
- `exit` in terminal 1 stops the container. All terminals close with it.

## If something is off
| Symptom | Fix |
|---|---|
| `grep cmd_vel` shows nothing | Forgot `source scripts/ant1_env.sh` in this terminal; or check the cable, `ping`. |
| Commands sent, robot doesn't move | Check `ems` (e-stop pressed?). Corner LEDs orange means something is within the safety zone. Is the joystick in manual mode (L1)? |
| Moves then stops by itself near things | That's the laser safety zone working. |
| `ant1_keys: command not found` / package not found | Run Step 3's `colcon build` and `source install/setup.bash`. |
| Arrow keys print `^[[A` | You're not in `ant1_keys`. Run it in a container terminal, not via a pipe. |
