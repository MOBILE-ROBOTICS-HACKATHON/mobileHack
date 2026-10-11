# Crazyflie 2.1: complete guide (setup, terminals, every command, safety)

Same idea as the ANT1: **one terminal guards, one shows, one commands.** Everything runs in the `hackathon-ros:humble` container and talks to the drone through the **Crazyradio USB dongle**.

---

## 0. TL;DR: the terminal layout

| # | Terminal | Command | Job |
|---|---|---|---|
| 1 | **server** | `cf_server` (or `cf_fake` to practice) | the radio link. The ROS 2 bridge to the drone (crazyswarm2). Without it nothing works |
| 2 | **guard** | `cf_guard` | **safety, all flight.** SPACE = land, `K` = kill motors. Auto-lands on fence / battery / lost link |
| 3 | **view** | `cf_rviz` | 3D view: drone, position trail, takeoff frame, fence box |
| 4 | **commands** | `cf_keys` | keyboard flying + typed go-to. Or `cf_takeoff` / `cf_goto` / `cf_move` / `cf_land` |

Every terminal starts with:
```bash
source scripts/cf_env.sh
```

**Slow and controlled by default (for now):**

| What | Default | Change with |
|---|---|---|
| Speed of every move (keys, go-to, helpers, takeoff) | **0.15 m/s** (hard cap 0.3 in our tools) | `CF_SPEED=0.2 source scripts/cf_env.sh` |
| Firmware speed cap (position controller) | **0.3 m/s** | `posCtlPid` in `crazyflies.yaml` |
| Takeoff height | **0.3 m** above the floor (≥ 3 s climb), like the organisers' example | `cf_takeoff 0.4`, `cf_keys -p takeoff_height:=0.4` |
| Max height for commands | **1.0 m** | `CF_ZMAX=1.2 source scripts/cf_env.sh` |
| Guard fence | **±1.0 m** sideways, **1.2 m** high | `cf_guard -p fence_xy:=1.5 -p fence_z:=1.5` |
| Landing | ≥ 5 s (keys, helpers, guard); `cf_descend` 5 cm/s | |
| Arming | **automatic** before takeoff (`t` in `cf_keys`, `cf_takeoff`); disarm after landing | `cf_arm` / `cf_disarm` |
| Takeoff confirmation | `t` asks you to **type FLY** | |
| Key step | 0.1 m per press (0.05–0.2 with `+`/`-`), ≥ 0.7 s each | |

---

## 1. How it works

```
 Terminal 1  cf_server (crazyswarm2, cflib backend)
      │  services /cf1/takeoff, land, go_to, emergency ...   topics /cf1/pose, odom, status
      │
 Crazyradio PA / 2 (USB, 2.4 GHz, channel 80) ─────radio─────►  Crazyflie 2.1 + Flow deck v2
      ▲                                                           (stabilizes and holds position ONBOARD)
 Terminals 2-4 (cf_guard, cf_rviz, cf_keys) talk ROS 2 to cf_server, only on this laptop
```

- **Stabilizing:** the drone does this itself. Its IMU keeps it level, and with a positioning deck its Kalman filter keeps it in place. We only send **targets**: "take off to 0.5 m", "go to (x, y, z)", "land". Between commands it **hovers in place**.
- **Position needs a positioning deck.**
  - **OUR drone has a Lighthouse deck** (checked 10 Oct with `cf_check`). It measures its position from the infrared sweeps of **Lighthouse base stations**: small black boxes, high on tripods or walls around the flight area.
    - It needs **≥ 2 stations in view**, otherwise the position is garbage and it must not fly.
    - Its positions are **room coordinates** of that system: fixed axes, and the floor may not be exactly z = 0.
    - The drone has a 4-station setup stored, so it belongs to a specific arena. Ask the mentors where it is.
  - **A Flow deck v2** (camera plus height sensor) would also work without base stations. Positions are then relative to where it was at connect.
  - **Our tools work with both, using HOME:**
    - home = where the drone stands still on the ground before takeoff;
    - `cf_keys` targets (`g`, `h`) and the guard's fence are measured from home, and z means height above the floor;
    - `cf_keys` **refuses takeoff** while the position jumps on the ground.
  - The position is zeroed when `cf_server` connects, so **put the drone at the takeoff spot before starting the server.**
  - The Flow deck needs a **textured, well-lit floor**: not glossy, not plain white. It drifts a few cm per metre.
- **Lighthouse or Loco deck:** absolute room coordinates. The config needs another `robot_types` entry (ask).

### The drone's weak spots (read this)
1. **Radio loss:** the drone **keeps hovering at its last target**. The firmware has no timeout for takeoff/go_to, like the ANT1's missing cmd_vel timeout.
   - `cf_guard` raises **LINK LOST** and keeps trying to land.
   - **Physical stop:** catch the drone from below and **turn it upside down**. Tumble detection stops the motors. A Crazyflie weighs 27 g, so its props are harmless to fingers.
2. **Kill (`K` / `cf_kill`)** = motors off in the air: **it falls.** After a kill the drone stays **LOCKED** until you power-cycle it (switch off and on).
3. **Battery:** about 5–7 min of flight. It loses power fast at the end, so the guard lands below 3.3 V under load.

---

## 2. Network / internet: what needs to be connected?

| Link | Needed? | Notes |
|---|---|---|
| **Crazyradio USB dongle** | **yes, always** | in the laptop's USB port. It's the only link to the drone (2.4 GHz radio, **not Wi-Fi**) |
| **Laptop Wi-Fi / internet** | **no** for flying | everything runs on this laptop. **Internet is only for** installs (done) and **firmware updates** in cfclient (it downloads from GitHub) |
| Phone hotspot (ANT1) | no | can stay on. `cf_env.sh` sets `ROS_LOCALHOST_ONLY=1`, so the drone's ROS traffic never leaves the laptop |
| Ethernet | no | |

- **Radio interference:** channel 80 = 2480 MHz, above the busy Wi-Fi channels (Wi-Fi channel 13 tops out at ~2483 MHz, so there's slight overlap at most).
  - In a room full of teams with drones, give **each drone its own address and/or channel** (cfclient → Connect → Configure 2.x).
  - If the link is bad (`rssi` above ~-70 dBm in the guard line, i.e. a weaker signal), switch the channel, e.g. to 100: `radio://0/100/2M/...`.
- **Localhost-only isolation:** nobody on the Wi-Fi can command our drone, and our commands can't reach other teams.
- **Later, for the ANT1 + drone bridge or teammates watching:** drop the localhost-only setting and use a shared domain. Not now.

---

## 3. One-time setup (already done on this laptop)

| What | Where | Status |
|---|---|---|
| Bitcraze udev rule (lets the `plugdev` group use the dongle) | host `/etc/udev/rules.d/99-bitcraze.rules` | present. Your user is in `plugdev` |
| crazyswarm2 (`ros-humble-crazyflie*`), cfclient 2025.2, cflib, rowan | image `hackathon-ros:humble` | built 10 Oct with `docker/Dockerfile.drones` (add-on). `docker/Dockerfile` also has it for full rebuilds |
| USB passthrough (`/dev/bus/usb` mount, so a dongle plugged in later appears) + `plugdev` group in the container | `docker/run.sh` | done |
| `cf_guard`, `cf_keys` nodes | `ws/src/team_pkg/team_pkg/` | built (`colcon build`) |
| drone config, rviz view | `ws/src/team_pkg/config/crazyflies.yaml`, `cf.rviz` | done |
| helpers | `scripts/cf_env.sh` | done |
| fake drone for practice | `scripts/cf_diag/fake_cf.py` (`cf_fake`) | done |

**After a change to the image or `run.sh`:** close every container terminal, then `./docker/run.sh` again. A running container keeps the old image.

**If the container image is ever rebuilt from scratch** and pytorch.org times out: build the full image when the network is better, or rebuild just the drone layer on top with `docker build -t hackathon-ros:humble -f docker/Dockerfile.drones docker`.

---

## 4. Step-by-step guide

### Step A: practice WITHOUT the drone (5 min, recommended once)
The fake drone answers like the real one and shows up in rviz.

| Terminal | Commands |
|---|---|
| 1 (`./docker/run.sh`) | `source scripts/cf_env.sh` → `cf_fake` |
| 2 (`./docker/exec.sh`) | `source scripts/cf_env.sh` → `cf_guard` |
| 3 (`./docker/exec.sh`) | `source scripts/cf_env.sh` → `cf_rviz` |
| 4 (`./docker/exec.sh`) | `source scripts/cf_env.sh` → `cf_keys` |

Try:
1. **In terminal 4:** `t` (take off), the arrows, `w`/`s`, `g` then `0.5 0 0.8` Enter, `h`, then SPACE.
2. **In terminal 2:** SPACE (land), or `K` (kill).

**The safety reactions:** restart terminal 1 with `cf_fake drift`, `cf_fake lowbat` or `cf_fake linkloss`, take off, and watch the guard land it.

### Step B: first contact with the real drone (cfclient)
**Our drone: `radio://0/70/2M/E7E7E7E702`** (found 10 Oct: it vanished from the scan when switched off). `E7E7E7E704` is **another team's** drone, so never connect to it. `cf_scan` checks our address by default. Find an unknown address the same way: scan, switch yours off, scan again.

1. **Hardware:**
   - charge the battery;
   - check the **Flow deck** is on the bottom;
   - plug the **Crazyradio** into the laptop;
   - put the drone **on the floor, at the takeoff spot, front pointing where you want +x**;
   - switch it on: it beeps, the LEDs blink, then it sits still.
2. **The container:** if it was started before these changes, close all its terminals, then:
   ```bash
   ./docker/run.sh
   cfclient
   ```
3. **In cfclient:** **Scan** → choose `radio://0/80/2M/E7E7E7E7E7` (or whatever appears) → **Connect**. Check:
   - **Battery** above 3.8 V.
   - **The deck list:** View → Tabs → Parameters, `deck` group, `bcFlow2 = 1`.
   - **Optional:** Flight tab → "Assisted mode: Hover" lets you test hover with a gamepad. Not needed.
   - **The address:** if it isn't `E7E7E7E7E7` on channel 80, write the URI into `ws/src/team_pkg/config/crazyflies.yaml` → `robots.cf1.uri`.
   - **Firmware:** if the mentors say to update it, use Connect → Bootloader. Needs internet.
4. **Close cfclient.** Only one program can use the radio.

**Without the GUI:** `source scripts/cf_env.sh; cf_scan` prints the URIs it finds.

**Pre-flight check (every session, before `cf_server`):**
```bash
source scripts/cf_env.sh
cf_check
```
It connects directly to the drone (cfclient must be closed) and reports:
- battery;
- which decks are mounted;
- the height-sensor reading;
- flow quality;
- whether the position estimate stays still for 3 s.

It ends with **READY** or **NOT READY** plus the reasons. The motors never run.

### Step C: first flight
**Area:** about 3×3 m clear, textured floor, good light, nobody under the drone, and someone ready to catch it.

| Terminal | Commands |
|---|---|
| **1** (`./docker/run.sh`) | `source scripts/cf_env.sh` → `cf_server`. Wait for it to connect (no errors; the drone's LEDs change) |
| **2** guard | `source scripts/cf_env.sh` → `cf_guard`. The status line shows `(+0.00, +0.00, +0.00) landed \| bat 4.0 V \| rssi -40 dBm` |
| **3** view | `source scripts/cf_env.sh` → `cf_rviz`. The drone model sits at the origin inside the red fence box |
| **4** commands | `source scripts/cf_env.sh` → `cf_keys` |

In terminal 4:
1. `t`, then type `FLY` + Enter: it **arms**, waits 1 s, takes off to 0.3 m (3 s) and hovers. **Watch it for 5 s:** stable? little drift?
2. `↑` once: 10 cm forward. `←` once: 10 cm left. `w`: up 10 cm. `s`: down 10 cm.
3. `g` then `0.3 0 0.5` Enter: goes to that point.
4. `h`: back above home (the takeoff spot).
5. SPACE: lands.

**If anything looks wrong:** SPACE in **terminal 2** (the guard). If it's about to hit something: `K` in terminal 2, or catch it and flip it.

### Step D: a normal session
Same 4 terminals as step C. Control it manually with `cf_keys`, and send goals with `g` (in `cf_keys`) or with `cf_goto` from any terminal.

**End of session:**
1. land;
2. Ctrl-C in `cf_keys`, then in `cf_guard`, then in `cf_server`;
3. switch the drone off and unplug the battery to charge it.

---

## 5. Command reference

### Terminal setup
```bash
./docker/run.sh                  # host: first terminal (starts the container). Keep it open: closing it stops the container
./docker/exec.sh                 # host: every further terminal
source scripts/cf_env.sh         # in EVERY container terminal (domain 42, localhost only, helpers)
CF=cf2 source scripts/cf_env.sh  # another drone name from crazyflies.yaml
```

### `cf_guard` (terminal 2)
| Key | Action |
|---|---|
| `SPACE` / `l` | land (3 s) |
| `K` (capital) | **kill**: motors off, the drone falls, LOCKED until power-cycled |
| `q` | quit. Lands first if the drone is flying (so do Ctrl-C and closing the terminal) |

Automatic: land if it leaves the **fence** (|x| or |y| > 1.0 m, or z > 1.2 m), if the **battery** stays < 3.3 V for 2 s, or if the **link is lost** (no position for 1 s, plus an alarm).
- **Options:** `cf_guard -p fence_xy:=1.5 -p fence_z:=1.5 -p vbat_land:=3.4`.
- **Status line:** position, FLYING/landed, battery, signal (`rssi`: closer to 0 = stronger), TUMBLED / LOCKED / NO DATA.

### `cf_keys` (terminal 4)
| Key | Action |
|---|---|
| `t` | asks **FLY** + Enter → **arms**, then takes off to 0.3 m above the floor (`-p takeoff_height:=0.4`). Refused while the position jumps on the ground |
| `↑` / `↓` | forward / back (x) by one step |
| `←` / `→` | left / right (y) by one step |
| `w` / `s` | up / down (z) by one step |
| `a` / `d` | turn left / right 15° |
| `+` / `-` | bigger / smaller steps (0.05–0.2 m, start 0.1) |
| `g` | **go to:** type `x y z` + Enter, metres **from home** (z = height above the floor), at 0.15 m/s |
| `h` | back above home at the current height |
| `p` | print position |
| `SPACE` / `l` | land |
| `q` | **lands (if flying), waits, disarms, quits.** Ctrl-C does the same; a second Ctrl-C stops waiting |

- **Steps, not speeds:** each press = one small go-to, and the drone holds position between presses.
- **Holding a key** takes the next step only when the current one is done (≤ 0.15 m/s), so releasing it stops within one step.
- **Height limits:** it refuses z > 1.0 m (`CF_ZMAX`) and z < 0.1 m (use land).

### Shell helpers (any terminal, after `source scripts/cf_env.sh`)
| Command | Action |
|---|---|
| `cf_scan [addr]` | find drones on the radio (default address `E7E7E7E7E7`) |
| `cf_check [uri]` | **pre-flight check** (before `cf_server`): battery, decks, sensors, estimate → READY / NOT READY |
| `cf_server` | start the ROS 2 server (terminal 1) |
| `cf_fake [normal\|drift\|lowbat\|linkloss]` | fake drone instead of `cf_server` (practice/tests) |
| `cf_guard`, `cf_keys`, `cf_rviz` | the guard, keyboard control and 3D view nodes |
| `cf_takeoff [h=0.4]` | take off (timed for `CF_SPEED`) |
| `cf_move dx dy dz` | relative move (x forward, y left, z up), timed for `CF_SPEED` |
| `cf_goto x y z [yaw_deg=0]` | absolute move in the **position system's frame** (Lighthouse: room coordinates!), timed for `CF_SPEED`; refuses z outside 0.1–1.0 m. Prefer `g` in `cf_keys` (from home) |
| `cf_arm` / `cf_disarm` | arm (needed before takeoff on this firmware; `cf_takeoff` does it) / disarm |
| `cf_pose` / `cf_pose --once` | live / single position |
| `cf_land [s=4]` | land |
| `cf_descend` | **slow descent to the floor at 5 cm/s** (`CF_DESCEND=0.1 cf_descend` for 10 cm/s) |
| `cf_kill` | emergency motors off (falls; LOCKED) |

### Raw ROS 2 (what the helpers do; for your own code)
```bash
# duration sets the speed: keep distance / duration <= 0.15 m/s
ros2 service call /cf1/takeoff crazyflie_interfaces/srv/Takeoff "{height: 0.4, duration: {sec: 3}}"
ros2 service call /cf1/go_to crazyflie_interfaces/srv/GoTo "{relative: false, goal: {x: 0.5, y: 0.0, z: 0.5}, yaw: 0.0, duration: {sec: 4}}"
ros2 service call /cf1/land crazyflie_interfaces/srv/Land "{height: 0.0, duration: {sec: 4}}"
ros2 service call /cf1/emergency std_srvs/srv/Empty
ros2 topic echo /cf1/pose        # geometry_msgs/PoseStamped, frame "world" = takeoff point, 10 Hz (+ TF world -> cf1)
ros2 topic echo /cf1/odom        # nav_msgs/Odometry, 10 Hz
ros2 topic echo /cf1/status      # battery_voltage, rssi, supervisor_info (flying/tumbled/locked bits), 2 Hz
```
- **`GoTo.yaw` is in RADIANS,** even though the `.srv` comment says deg: the server passes it straight to cflib.
- **Velocity streaming** (`/cf1/cmd_hover`, `/cf1/cmd_vel_legacy`) exists, but needs a continuous ≥ 10 Hz stream. If the stream stops, the firmware levels the drone and cuts the motors after ~2 s. Before using takeoff/go_to/land again, call `/cf1/notify_setpoints_stop`. We use go_to steps instead.

---

### The organisers' cflib example (`cf.supervisor.send_arming_request(True)`)
- **Our image has cflib 0.1.28, where the same call is `cf.platform.send_arming_request(True)`.** Newer cflib renamed it to `cf.supervisor`; it's the same radio message.
- **We can't upgrade:** cflib 0.1.34 needs numpy 2, which breaks `cv_bridge`.
- **To run their script in the container:**
  - replace `cf.supervisor.` with `cf.platform.`;
  - run it as `CFLIB_URI=radio://0/70/2M/E7E7E7E702 python3 script.py`;
  - stop `cf_server` first (one radio user only).
- **It doesn't check the position before takeoff** (our `cf_keys` does), so run `cf_check` first.

### Two drones, finding drones (11 Oct)
- **Two drones:** `CF_DRONES=2 source scripts/cf_env.sh` → `cf_server` uses `crazyflies_two.yaml` (cf1 + cf2), and `cf_guard` guards both (SPACE lands all, `K` kills all). For one of them: `CF=cf2 cf_keys`, `CF=cf2 cf_check`.
- **Finding drones** (radio free): `cf_find` lists what answers; `cf_identify` asks you to switch yours off and tells yours from other teams'. Details: docs/09 section B1.
- **Guard takeover:** when the guard lands or kills a drone, it publishes `/cfN/guard_event`. `cf_keys` and the missions then stop sending moves, and the guard re-lands if its landing doesn't make the drone descend.
- **`cf_keys` never sends moves** (arrows, `g`, `h`) to a drone that isn't flying.

## 6. Safety rules
1. **`cf_guard` runs for every flight,** in its own terminal, with your hand near SPACE.
2. **Low and slow (the defaults):** 0.15 m/s, takeoff to 0.3 m, ≤ 1.0 m high, steps of 0.1 m, and a person ready to catch it. Raise `CF_SPEED` only after several calm flights, and never above 0.3 m/s indoors.
3. **The drone at the takeoff spot before `cf_server`** (the position is zeroed at connect).
4. **Lost link:** catch it and flip it. The guard can't reach a drone that isn't listening.
5. **Battery:** land at the guard's warning or after about 5 min. Never fly a battery below 3.7 V at rest.
6. **After `K` / `cf_kill` / a crash:** power-cycle the drone (LOCKED). Restart `cf_server` so the position is zeroed again.
7. **Test code changes against `cf_fake`** before flying them, like `fake_nav2` for the ANT1.

---

## 7. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `Cannot find a Crazyradio Dongle` | dongle not plugged in, or the container was started before `run.sh` got USB passthrough → restart the container. Host check: `lsusb \| grep 1915` |
| `cf_scan`: no Crazyflie found | drone off, wrong address/channel (try cfclient Scan), battery flat |
| `cf_server` errors "Too many packets lost" / connection lost | interference or distance → other channel (`radio://0/100/2M/...`), dongle on a USB extension cable, closer |
| `cf_server` won't connect while cfclient is open | close cfclient (one radio user only) |
| guard says `(no position yet)` | `cf_server` not running / not connected; or a different `CF` name or domain in that terminal (`source scripts/cf_env.sh` everywhere) |
| takes off then drifts away / unstable | no Flow deck, a shiny or plain floor, bad light, or not zeroed (restart `cf_server` with the drone still) |
| `takeoff` does nothing | LOCKED after a kill/crash (power-cycle); or the battery is too low |
| rviz: no drone model | rviz started before `cf_server`: re-add/toggle "Drone cf1" or restart `cf_rviz` |
| `serdata` / `lo is not multicast-capable` messages | harmless (localhost-only mode) |

---

## 8. Files
| File | What |
|---|---|
| `scripts/cf_env.sh` | env (domain 42, localhost only) + all `cf_*` helpers |
| `ws/src/team_pkg/config/crazyflies.yaml` | drone name `cf1`, radio URI, Flow-deck settings (Kalman + PID), logged topics |
| `ws/src/team_pkg/team_pkg/cf_guard.py` | the safety guard |
| `ws/src/team_pkg/team_pkg/cf_keys.py` | keyboard control + typed go-to |
| `ws/src/team_pkg/config/cf.rviz` | the rviz view |
| `scripts/cf_diag/fake_cf.py` | fake drone for practice/tests |
| `docker/Dockerfile`, `docker/Dockerfile.drones`, `docker/run.sh` | image (drone layer) and USB passthrough |
