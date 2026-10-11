# ANT1 + drones: step-by-step guide (which command in which terminal)

This is the **practical checklist**:
- the background (how the bridge, the calibration and the recall work) is in [08_ANT_DRONE_MISSIONS.md](08_ANT_DRONE_MISSIONS.md);
- single-robot details are in [05](05_ANT1_HANDOFF_AND_LESSONS.md) / [04](04_ANT1_COMMANDS.md) (ANT1) and [07](07_CRAZYFLIE.md) (drone).

**Missions:**

| Mission | What happens | Program |
|---|---|---|
| **1 Follow** | you fly the drone, the ANT follows under it | `cf_keys` + `mission_follow` |
| **2 Scout** | the ANT patrols; drones **escort** (around the ANT), **scout** (ahead), or **roam** (anywhere in an area, independent of the ANT). On your call / low battery they come back and land on the ANT | `mission_scout` |
| **Hop** | the ANT carries the drone close to a target it can't reach; the drone hops over and back | `mission_hop` |

Everything works with **one drone** (default) or **two drones** (`CF_DRONES=2`). **Tested only on the simulation so far.**

---

## A. Terminal cheat-sheet

How to open terminals (on the **host**, in the Hackathon folder):
```bash
./docker/run.sh        # the FIRST terminal: starts the container. Keep it open all session
./docker/exec.sh       # every further terminal
```
**Shortcut:** `bash scripts/mission_tmux.sh 1|2|hop` opens all of them as tmux windows. Use `Ctrl-b n` for the next window, then press Enter in each.

The first line in each terminal sets up its environment:

| Kind | First line in that terminal |
|---|---|
| **ANT** | `ANT1_IFACE=wlp3s0 ANT1_PEER=10.66.76.31 source scripts/ant1_env.sh` |
| **Drone / mission** | `source scripts/cf_env.sh` (**two drones:** `CF_DRONES=2 source scripts/cf_env.sh`) |
| **Bridge** (only one) | `ANT1_IFACE=wlp3s0 ANT1_PEER=10.66.76.31 source scripts/mission_env.sh` (**two drones:** prefix `CF_DRONES=2`) |

| # | Name | Command (after its first line) | Keep running? |
|---|---|---|---|
| 1 | ANT watchdog | `ant1_watchdog` | yes, all session |
| 2 | ANT view | `ant1_rviz` | optional |
| 3 | ANT commands | `ant1_nav_speed 0.1 0.3 --live` (then `ant1_keys` for the calibration) | |
| 4 | drone server | `cf_check` → `cf_server` | yes |
| 5 | **bridge** | `mission_link` | yes |
| 6 | **drone guard** | `cf_guard -p leash:=2.0` (escort/scout/follow/hop) **or** `cf_guard -p area:="xmin,xmax,ymin,ymax"` (roam) | yes, all flight |
| 7 | calibration | `mission_calib` | once per session |
| 8 | 3D view | `mission_rviz` | optional |
| 9 | mission | `mission_follow` + `cf_keys` / `mission_scout ...` / `mission_hop` | |

---

## B. Once, before the first real session

### B1. Find YOUR drone(s) on the radio (the scanning problem)
**What went wrong on 10 Oct:**
- The scan of the factory address `E7E7E7E7E7` found **nothing**: the drones carry **team-assigned addresses**.
- Ours turned out to be `E7E7E7E702` on channel 70. **Another team's drone** (`E7E7E7E704`) answers too.
- A drone often shows up on **neighbouring channels** as well (79 + 80 + 81).

**With two drones it gets worse:** you must tell *your two* apart from each other and from everybody else's.

**Do this (container terminal; `cf_server` and cfclient CLOSED, since only one program can use the radio):**
1. **Ask the mentors which addresses belong to your team.** The numbering (…02, …04) looks assigned per team.
2. Run:
   ```bash
   source scripts/cf_env.sh
   cf_identify
   ```
   It scans, asks you to **switch only YOUR drone(s) off**, then scans again. The addresses that **vanished** are yours; the ones still answering belong to other teams. Then you switch yours back on, and it re-checks them and suggests the URI (middle channel).
3. **To tell drone 1 from drone 2:** run `cf_identify` again and switch **only one** of them off. The address that vanishes is that drone. **Put a sticker "1" / "2" on each.**
4. **Write the URIs into the config:**
   - one drone: `ws/src/team_pkg/config/crazyflies.yaml` → `cf1: uri:` (already `radio://0/70/2M/E7E7E7E702`);
   - two drones: `ws/src/team_pkg/config/crazyflies_two.yaml` → `cf1:` and `cf2: uri:`. **cf2 is currently a placeholder** (`…E7E7E7E703`).
5. **Check each one** (drone ON, flat on the floor):
   ```bash
   CF=cf1 cf_check                                    # one drone
   CF_DRONES=2 source scripts/cf_env.sh
   CF=cf1 cf_check && CF=cf2 cf_check                 # two drones
   ```
   Each must say **READY**. With Lighthouse that needs ≥ 2 base stations seen.

**Rules for two drones:**
- **Different addresses, and the same channel + datarate** (e.g. both on 70/2M): one Crazyradio then serves both efficiently.
- **If both have the SAME address,** one of them has to change. Only **with mentor OK**: cfclient → connect to it → *Connect → Configure 2.x* → new address (e.g. `E7E7E7E703`), same channel → *Write* → power-cycle. Never pick an address another team uses (scan first).
- **`cf_server` needs EVERY configured drone ON.** If one is missing or flat, it fails at start. Then use the one-drone config (`source scripts/cf_env.sh` without `CF_DRONES=2`).
- **`cf_find`:** just lists what answers (no off/on step).

### B2. Measure and check (on site)
1. **Plate height:** tape from the floor to the top of the ANT's plate (e.g. 0.146 m). Use it as `-p ant_height:=` in `mission_calib`.
2. **Where the drones sit:**
   - **one drone:** in the **centre** of the plate, nose = ANT front;
   - **two drones:** cf1 **15 cm in front** of the centre, cf2 **15 cm behind**, noses forward.
3. **Lighthouse coverage:** the ANT's driving area must be covered (`cf_check` with the drone on the ANT in a few places).
4. **For roam:** decide the **area** box in the Lighthouse frame. Fly or carry a drone to two opposite corners and read `cf_pose --once`, or read it off `mission_rviz` (grid = 0.5 m). Example: `-2.5,1.0,0.5,3.5` (xmin,xmax,ymin,ymax).

---

## C. Every session: bring-up (do it in this order)

| Step | Terminal | Commands | You should see |
|---|---|---|---|
| C1 | 1 (`./docker/run.sh`) | `ANT1_IFACE=wlp3s0 ANT1_PEER=10.66.76.31 source scripts/ant1_env.sh` → `ant1_watchdog` | watchdog running |
| C2 | 3 | ANT env; **after a robot reboot:** `ant1_nav_speed` (ANT standing still); then always `ant1_nav_speed 0.1 0.3 --live` | `OK` |
| C3 | 2 (optional) | ANT env → `ant1_rviz` | map + lidar |
| C4 | 4 | `source scripts/cf_env.sh` (or `CF_DRONES=2 ...`) → `cf_check` (two: `CF=cf1 cf_check && CF=cf2 cf_check`) → `cf_server` | READY, then the server connects |
| C5 | 5 | `ANT1_IFACE=wlp3s0 ANT1_PEER=10.66.76.31 source scripts/mission_env.sh` → `mission_link` | `ANT OK (0.0 s) map (...)`. `NO CALIB` until C7 |
| C6 | 6 | `source scripts/cf_env.sh` (or `CF_DRONES=2 ...`) → `cf_guard -p leash:=2.0` (roam: `-p area:="..."`) | one status per drone, `landed`, battery |
| C7 | 7 | `source scripts/cf_env.sh` → `mission_calib -p ant_height:=0.146` → drive the ANT with `ant1_keys` (terminal 3) **~40 cm, STOP 2 s, repeat 4–6×, with a turn** → `w` | `fit RMS` **< 3 cm = GOOD**; terminal 5 shows `room (...)` |
| C8 | 8 (optional) | `source scripts/cf_env.sh` → `mission_rviz` | the drone(s) inside the orange ANT box |

**Calibration rules:**
- the drone(s) **not flying**;
- for two drones, calibrate with **cf1 in the CENTRE** of the plate, then move it to its front slot;
- redo after a SLAM reset / new map.

---

## D. Method 1: the ANT follows the drone you fly (one drone)

| Terminal | Commands |
|---|---|
| 9a | `source scripts/cf_env.sh` → `cf_keys` |
| 9b | `source scripts/cf_env.sh` → `mission_follow` |

1. **In 9a:** `t`, then type `FLY` + Enter: arms, takes off 0.3 m above the plate. **Refused if the ANT is driving.**
2. **In 9b:** `f`: follow ON.
3. **Fly in 9a:** arrows / `w` / `s` (10 cm steps), or `g` + `1.0 0 0.4` + Enter (metres from home). The ANT drives under the drone.
4. **In 9a:** `h` = back above the ANT, then SPACE: lands **on the plate** (on the floor if not above the ANT).
5. **End:** `q` in 9b (stops the ANT), `q` in 9a.

**Second drone:** run `CF=cf2 cf_keys` and `mission_follow -p cf:=cf2`.

---

## E. Method 2: patrol + escort / scout / roam + recall (one or two drones)

| Terminal | Commands |
|---|---|
| 9 | `source scripts/cf_env.sh` (two: `CF_DRONES=2 source scripts/cf_env.sh`) → `mission_scout -p waypoints:="1.0,0.0; 1.0,1.0; 0.0,0.5"` (roam: add `-p area:="xmin,xmax,ymin,ymax"`) |

Waypoints are **ANT map** coordinates (read them in `ant1_rviz`), or click them in `mission_rviz` with "Publish Point".

1. **`t` + FLY:** every drone sitting on the standing ANT takes off; **cf2 4 s after cf1**.
2. **`p`:** ANT patrol ON.
3. **Formations** (switch any time):

   | Key | Formation |
   |---|---|
   | `e` | **ESCORT:** random points 0.6–1.1 m around the ANT, following it |
   | `s` | **SCOUT:** 1 m ahead of the ANT (two drones side by side) |
   | `f` | **ROAM:** random points in the area, **nothing to do with the ANT** (no area given: 0.8 m around its takeoff spot) |
   | `o` | **HOLD** |
   | `1` or `2`, then a key | that command for **one drone only**. Example: `1` `s`, `2` `f` = cf1 scouts, cf2 roams |

4. **`r`:** the ANT **calls the drones back** (or `1` `r` / `2` `r` for one). Each comes back:
   - **one at a time** on the plate; the other waits 0.9 m **beside** the ANT;
   - the ANT **pauses for the touchdowns**;
   - each drone lands on **its slot**, then disarms;
   - the patrol **resumes by itself**.
5. **Automatic recall:** battery < 3.55 V for 3 s, or more than 240 s of flight.
6. **`x`:** stop everything (the ANT stops, drones land where they are). **`q`:** recall all, quit when down.

**Heights:** one drone 0.6 m; two drones 0.55 m (cf1) and 0.90 m (cf2). Their paths may cross but stay 35 cm apart vertically, and roam targets keep ≥ 0.6 m between the drones.

**ROAM + guard:** the leash (2 m to the ANT) would land a roaming drone that goes far from the ANT. **For roam, run the guard with the same area:**
```bash
cf_guard -p area:="xmin,xmax,ymin,ymax"
mission_scout -p waypoints:="..." -p area:="xmin,xmax,ymin,ymax"
```

---

## F. Carrier hop (one drone)

| Terminal | Commands |
|---|---|
| 9 | `source scripts/cf_env.sh` → `mission_hop` (options: `-p hop_z:=0.8 -p dwell:=5.0 -p max_hop:=1.8`) |

1. **`g`:** type the target `x y` in the **ANT map** (read it in `ant1_rviz`), e.g. a point on or behind a table. Or click it with "Publish Point" in `mission_rviz`.
2. **`h`:** the ANT drives toward the target. If it can't get there, `mission_link` sends it to the **closest reachable point** (it prints `going to the closest REACHABLE point`).
3. **READY:** shows how far the target still is. More than `max_hop` (1.8 m, inside the 2 m leash) → refused.
4. **`t` + FLY:**
   1. takeoff;
   2. climb to `hop_z` (0.8 m above the floor);
   3. fly over to the target;
   4. hover `dwell` s;
   5. come back, land on the ANT (align, 5 cm/s descent);
   6. disarm;
   7. **the ANT drives back** to where it started.
5. **Higher obstacles:** raise `hop_z` only if the obstacle is taller **and** the guard's `fence_z` (1.2 m above home) allows it. Start low.
6. **`x`:** abort (the ANT stops, the drone lands where it is). **`q`:** land and quit.

---

## G. Practise everything WITHOUT hardware (do this first)
```bash
# container terminal
bash scripts/mission_diag/sim_all.sh start              # one fake drone   (CF_DRONES=2 ... for two)
bash scripts/mission_tmux.sh sim2                       # or sim1 / simhop;  CF_DRONES=2 / AREA="-3,1.5,0,4" also work
```
In the simulation the fake ANT starts at room `(-1.23, 1.87)`, already calibrated.

| To test | Do |
|---|---|
| Method 2, one drone | window `scout`: Enter → `t` + FLY → `p` → `e` → `s` → `f` → `r` |
| two drones | `CF_DRONES=2 bash scripts/mission_diag/sim_all.sh start`, then `CF_DRONES=2 bash scripts/mission_tmux.sh sim2` → `t` + FLY → `1` `s` → `2` `f` → `r` (watch the queue) |
| roam with area | `AREA="-3.0,1.5,0.0,4.0" bash scripts/mission_tmux.sh sim2` |
| hop | `bash scripts/mission_tmux.sh simhop` → `g` + `2.75 1.0` (inside a fake wall) → `h` → `t` + FLY |
| battery recall | `FAKE_BAT_DROP=0.02 bash scripts/mission_diag/sim_all.sh start` |
| calibration | `bash scripts/mission_diag/sim_all.sh drive` + `MISSION_CALIB=/tmp/sim_calib.yaml mission_calib` → `w` (expects 30.0°, (2.00, −1.00)) |

Stop: `bash scripts/mission_diag/sim_all.sh stop`, then `tmux kill-session -t mission`.

---

## H. First real runs (order)
1. **C1–C8 without flying:** calibration only; check `mission_rviz`.
2. **Method 1**, one drone, ANT 1 m away.
3. **Method 2**, one drone: 2 waypoints close together, `e`, then `r`.
4. **Roam**, one drone, with the area, then `r`.
5. **Two drones:** takeoff, `o` (hold), `r`. Watch the landing queue.
6. **Hop** with a low obstacle (a box), `hop_z` 0.6–0.8.

---

## I. Emergencies

| Situation | Do |
|---|---|
| a drone misbehaves | **SPACE in the guard** (terminal 6): lands ALL flying drones. The missions **stop commanding** a drone the guard lands (they show `GUARD`). The guard **re-lands** if its landing is overridden (not descending 1.5 s later) |
| a drone is about to hit something | `K` in the guard (motors off, it falls; power-cycle afterwards), or catch it and turn it over |
| radio link lost (`LINK LOST`) | the drone keeps hovering: catch it and turn it over |
| the ANT misbehaves | ANT **e-stop**. Before releasing it: `python3 scripts/ant1_diag/cancel_all_goals.py` (ANT env) |
| stop the ANT from the drone side | `s` in `mission_link`, or `ros2 topic pub --once /ant/stop std_msgs/msg/Empty "{}"` |
| everything | `x` in the mission terminal (the ANT stops, all drones land) |

---

## J. Shut down
1. **Land** all drones (`q` in the mission), check they show `IDLE ... disarmed`.
2. **Mission terminals:** `q`; **guard:** `q` (it lands anything still flying).
3. **`mission_link`:** `q` (stops the ANT); **`cf_server`:** Ctrl-C; **`ant1_watchdog`:** Ctrl-C.
4. **Drones off,** batteries out to charge.
