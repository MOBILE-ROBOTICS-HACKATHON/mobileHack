# ANT1 + Crazyflie missions: complete guide

Two joint missions for the Olive ANT1 (ground robot) and our Crazyflie 2.1 `cf1` (drone). Both start with the drone sitting on the ANT's top plate.

| Method | Who moves what | Program |
|---|---|---|
| **1: Follow** | **You fly the drone** (`cf_keys`). The ANT drives under it by itself (Nav2, avoids obstacles) | `mission_follow` |
| **2: Escort / Scout + recall** | The ANT **patrols waypoints** (Nav2). The drone flies **by itself** around it (**escort**) or ahead of it (**scout**), switchable in flight. On your call, low battery or a time limit, it **comes back and lands on the ANT**; the ANT pauses only for the touchdown | `mission_scout` |

Prerequisites, the single-robot guides:
- `docs/05_ANT1_HANDOFF_AND_LESSONS.md` + `docs/04_ANT1_COMMANDS.md` (ANT1);
- `docs/07_CRAZYFLIE.md` (drone).

**Everything here was tested on fakes (10–11 Oct). Nothing has run on the real robots yet:** see section 11.

> **Terminal-by-terminal checklist: [09_MISSION_STEP_BY_STEP.md](09_MISSION_STEP_BY_STEP.md).**
> Added on 11 Oct (evening): **ROAM** (drones fly independently of the ANT), **two drones** (`CF_DRONES=2`), **carrier hop** (`mission_hop`), finding / identifying drones on the radio (`cf_identify`), and the guard taking over (section 7).

---

## 0. TL;DR

```
 DOMAIN 0  (robot network: hotspot Wi-Fi)              DOMAIN 42  (localhost only: drone safety never needs Wi-Fi)
 ANT1: Nav2, SLAM, lidar, TF  ◄──────►  ant_link  ◄──────►  cf_server (radio) · cf_guard · cf_keys
 laptop: ant1_watchdog, ant1_rviz      (the ONLY process        mission_calib · mission_follow · mission_scout · mission_rviz
                                         in both domains)
```

**Session order:**
1. ANT terminals;
2. drone server;
3. **`mission_link`** (bridge);
4. `cf_guard -p leash:=2.0`;
5. **`mission_calib`** (once per session);
6. `mission_rviz`;
7. then **Method 1** (`cf_keys` + `mission_follow`) or **Method 2** (`mission_scout`).

Shortcut: `bash scripts/mission_tmux.sh 1|2` opens all terminals as tmux windows.

**Practise without hardware:**
```bash
bash scripts/mission_diag/sim_all.sh start
bash scripts/mission_tmux.sh sim2
```

---

## 1. How it fits together

### 1.1 Two ROS worlds and one bridge
- **ANT side:** ROS 2 **Jazzy** on the robot, **domain 0**, reached over the phone hotspot (`wlp3s0`, robot `10.66.76.31`). Our ANT tools stay exactly as before: `ant1_watchdog`, `ant1_rviz`, `ant1_keys`, `ant1_nav_speed`.
- **Drone side:** `cf_server` + our drone tools in **domain 42, localhost only**. The Crazyradio is USB, so **the drone's safety never depends on Wi-Fi**.
- **`ant_link`** is a single process with **two ROS contexts**: one in domain 0, one in domain 42. Its CycloneDDS config has one `<Domain>` block per id (`scripts/mission_env.sh`). It:
  - **reads** the ANT's TF (map → base_link), odometry, global costmap and Nav2 goal status;
  - **publishes** on the drone side: `/ant/pose_map`, `/ant/pose_room` (the ANT in the drone's frame), `/ant/moving`, `/ant/nav_state`, `/ant/marker`, `/mission/calib`, plus TF `world → ant_map`;
  - **accepts** on the drone side:
    - `/ant/goal` (PoseStamped, frame `world` or `ant_map`): converted to the map, a **reachability check** on the ANT costmap (closest reachable point if blocked, as in `ant1_goto`), then `goal_pose` on the robot (stamp 0), **re-sent** up to 3× if Nav2 doesn't confirm within 5 s;
    - `/ant/stop` (Empty): **cancels every Nav2 action** (navigate_to_pose, follow_path, spin, backup, drive_on_heading, wait) and sends zero velocity. If the ANT is *still* being driven 1–2.5 s later, it **pauses Nav2**, as `ant1_goto` does since the 10 Oct runaway.
  - **On quit or crash it stops the ANT:** it never leaves a goal running behind it.

### 1.2 Frames: why we need a calibration
- **The drone** knows its position from **Lighthouse**: room coordinates in frame `world`, fixed axes. The floor isn't exactly z = 0.
- **The ANT** knows its position in its **SLAM map** (`ant_map`): its origin is wherever mapping started.
- **The link** between them is a 2D rigid transform, `map = R(θ)·room + (tx, ty)`, plus two heights in the drone frame:
  - `plate_z`: the top plate of the ANT, where the drone sits;
  - `floor_z`: `plate_z − ant_height` (`ant_height` defaults to 0.146 m; **measure ours**).
- **`mission_calib` finds them:** with the drone riding on the ANT, both systems measure the *same* point at several stops, and a least-squares fit (Kabsch) gives θ, tx, ty and the RMS error.
- **The result** goes to `data/mission_calib.yaml`. `ant_link` reloads it within 1 s and shares it on `/mission/calib`.
- **Redo the calibration** after a **SLAM reset or a new map** (the map frame moves), or when the ANT box and the drone don't line up in `mission_rviz`.

### 1.3 Landing height: plate or floor
Every landing (SPACE in `cf_keys`/`cf_guard`, `x` and the recall in `mission_scout`) picks its height:
- **the plate** (`plate_z`) if the drone is within 0.25 m (xy) of the ANT centre;
- **otherwise the floor** (`floor_z`).

Without ANT data it falls back to the drone's home height, as before. Landing at the wrong height means the drone "lands" in the air and drops, so this matters.

---

## 2. Before the first real run (on-site checks)
1. **Lighthouse coverage:** the area where the ANT drives must be inside the base stations' coverage (≥ 2 stations seen). `cf_check` with the drone on the ANT at the corners of the area.
2. **The plate:** flat and free, with the drone **centred** and its **nose pointing to the ANT's front**. A textured mat helps. If the drone can't sit at the centre, set `-p offset_x:= -p offset_y:=` in `mission_calib` (metres, ANT body frame, x forward, y left).
3. **Measure `ant_height`** (floor to the top of the plate) with a tape. Pass it to `mission_calib -p ant_height:=0.xx`.
4. **The ANT slower than the drone:** the drone flies at 0.15 m/s (`CF_SPEED`), so set the ANT to 0.1 m/s:
   ```bash
   ant1_nav_speed 0.1 0.3 --live      # live, no Nav2 restart
   ```
5. **First real tests, in this order:**
   1. calibration only (the drone never flies);
   2. Method 1 over 1 m;
   3. Method 2 with 2 waypoints close together;
   4. a recall.

---

## 3. Practise without hardware (recommended once)

**Container terminal 1:**
```bash
bash scripts/mission_diag/sim_all.sh start
```
This starts, in the background:
- a **fake ANT** (`fake_nav2.py drive`: drives to goals at 0.2 m/s, turns, stops on cancel);
- a **fake drone** (`fake_cf.py onant`: sits on the ANT and rides it, Lighthouse-like room frame);
- `ant_link` between them, with a ready calibration in `/tmp/sim_calib.yaml`. Your real `data/mission_calib.yaml` is never touched.

Then either `bash scripts/mission_tmux.sh sim2` (Method 2) or `sim1` (Method 1), or open terminals by hand with `source scripts/cf_env.sh` in each:

| Terminal | Command |
|---|---|
| guard | `cf_guard -p leash:=2.0` |
| view | `mission_rviz` |
| Method 1 | `cf_keys` (`t`, type FLY, `g` + `1.0 0 0.4`) **and** `mission_follow` (`f`) |
| Method 2 | `mission_scout -p waypoints:="1.0,0.0; 1.0,1.0; 0.0,0.5"`, then `t` + FLY, `p`, `e`, `s`, `r` |

**Extras:**
- **Calibration practice:**
  - `bash scripts/mission_diag/sim_all.sh drive` (the fake ANT drives in steps);
  - meanwhile `MISSION_CALIB=/tmp/sim_calib.yaml mission_calib`, then `w`;
  - it must find θ = +30.0°, t = (2.00, −1.00).
- **Battery recall:** `FAKE_BAT_DROP=0.02 bash scripts/mission_diag/sim_all.sh start` (the battery drains in flight).
- **Stop:** `bash scripts/mission_diag/sim_all.sh stop`.

---

## 4. Session start (both methods)

**Every ANT terminal:** `ANT1_IFACE=wlp3s0 ANT1_PEER=10.66.76.31 source scripts/ant1_env.sh && source ws/install/setup.bash`
**Every drone/mission terminal:** `source scripts/cf_env.sh` (plus `source ws/install/setup.bash`, if not already in `~/.bashrc`)
**The bridge terminal only:** `ANT1_IFACE=wlp3s0 ANT1_PEER=10.66.76.31 source scripts/mission_env.sh`

| # | Terminal | Command | Notes |
|---|---|---|---|
| A1 | ANT watchdog | `ant1_watchdog` | all session, as always |
| A2 | ANT view | `ant1_rviz` | map, costmap, lidar (ANT frame) |
| A3 | ANT commands | `ant1_nav_speed` (after a robot boot, ANT still), then `ant1_nav_speed 0.1 0.3 --live` | `ant1_keys` here for the calibration drive |
| D1 | drone server | `cf_check`, then `cf_server` | drone **on the ANT plate** |
| L1 | **bridge** | `mission_link` | status: `ANT OK ... room (...) ... nav idle`; `s` = stop the ANT, `q` = quit (stops the ANT) |
| D2 | drone guard | `cf_guard -p leash:=2.0` | lands the drone if it gets more than 2 m from the **current** ANT position |
| L2 | calibration | `mission_calib` | once per session, see 4.1 |
| V1 | 3D view | `mission_rviz` | drone, ANT box + heading arrow, leash circle, trail. "Publish Point" = a patrol waypoint (Method 2) |
| M | mission | Method 1 or 2 (sections 5 and 6) | |

**Shortcut:** `bash scripts/mission_tmux.sh 1` or `2` opens A1–M as tmux windows. A1 starts by itself; in the others the command is typed and you press Enter. Default network: `ANT1_IFACE=wlp3s0 ANT1_PEER=10.66.76.31`; waypoints for Method 2 from `WAYPOINTS="..."`.

### 4.1 Calibration (`mission_calib`, about 2 min)
1. **Set up:** drone **on the plate, centred, nose forward, NOT flying**; `cf_server` and `mission_link` running.
2. **Start:** `mission_calib -p ant_height:=0.146` (your measured value).
3. **Drive in steps** with `ant1_keys` in A3: **~40 cm, then STOP for 2 s**, repeat 4–6 times. **Include a turn** (e.g. 3 stops straight, then sideways or around a corner). Each stop prints `stop N recorded`.
   - **Why stops:** while driving, the two positions arrive with different delays. In the test that tilted the fit by 2–3°; at stops it was exact.
4. **`w`:** fit + save. Read the result:
   - `fit RMS`: **< 3 cm GOOD**, 3–5 cm OK, **> 5 cm redo** (`r`: slower, drone centred, Lighthouse in view);
   - θ / t / plate z / floor z;
   - `SLAM vs Lighthouse at N stops: mean/max`, plus a picture in `data/mission_calib.png`. That's how accurate the ANT's SLAM was on this drive (suggestion 2 in section 10).
5. **Fallback** (`s`): a single snapshot from the drone's yaw. Fast, but it needs the nose *exactly* forward.
6. **Check:** in `mission_rviz` the drone model must sit inside the orange ANT box. In L1 the status shows `room (...)`, no longer `NO CALIB`.

---

## 5. Method 1: the ANT follows the drone you fly

**Terminals:** as in section 4, plus:
- **M1:** `cf_keys`, where you fly;
- **M2:** `mission_follow`, which moves the ANT.

**Step by step:**
1. **Take off:** ANT standing still. In M1 press `t`, type `FLY` + Enter: it arms and takes off to 0.3 m above the plate. **`cf_keys` refuses takeoff while the ANT drives.**
2. **Follow on:** in M2 press `f`.
3. **Fly** with `cf_keys`: arrows / `w` / `s` steps, or `g` + `x y z` (metres **from home** = where it took off). The ANT drives under the drone.
4. **Back above the ANT:** `h` in `cf_keys` (it knows where the ANT is now).
5. **Land:** SPACE in `cf_keys`. **Above the ANT it lands on the plate**, elsewhere on the floor. When the drone stops flying, `mission_follow` stops the ANT.
6. **End:** `q` in M2 (stops the ANT), then `q` in M1 (lands if flying, disarms).

**Follow rule** (5 Hz): the target is the point under the drone. A new ANT goal is sent only when **all** of these hold:
- the ANT is > 0.4 m from it (`deadband`);
- the target moved > 0.3 m since the last goal (`min_move`);
- the last goal is ≥ 2 s old (`period`).

This avoids a flood of goals: re-sending too often made Nav2 struggle on 10 Oct. Nav2 avoids obstacles on the way, and if the point under the drone is unreachable (drone over a table), `ant_link` sends the ANT to the closest reachable point.

**The ANT is stopped** (`/ant/stop`) when:
- following is switched off (`f`/`x`/`q`);
- the drone isn't flying;
- the drone position or the ANT data is older than 1 s;
- there's no calibration.

| `mission_follow` key | Action |
|---|---|
| `f` | follow ON / OFF (starts OFF) |
| `x` | stop the ANT now (follow OFF) |
| `q` | stop the ANT + quit |

**The status line shows:**
- follow ON/OFF;
- the drone position and FLYING;
- the ANT position, its distance to the drone, moving/still;
- the Nav2 state and the age of the last goal;
- `WAITING: <reason>`.

---

## 6. Method 2: patrol + escort / scout + recall

**Terminals:** as in section 4, plus **M:**
```bash
mission_scout -p waypoints:="1.0,0.0; 1.0,1.0; 0.0,0.5"
```
- **Waypoints are ANT map coordinates.** Read them off `ant1_rviz`, or click them with "Publish Point" in `mission_rviz` (added live, in the drone frame).
- **Options:**
  - `-p speed:=0.15` (the default, from `CF_SPEED`);
  - `-p recall_v:=3.55`: battery voltage that triggers a recall;
  - `-p max_flight:=240.0`: seconds of flight before a recall.

**Step by step:**
1. **Take off:** ANT still, drone on the plate. Press `t`, type `FLY`: it arms and takes off to 0.3 m above the plate, then **HOLD**s.
2. **Patrol:** `p` starts the ANT patrol (waypoints in a loop; a waypoint that fails 3× is skipped).
3. **Formation:** `e` (escort) or `s` (scout). **Switch any time**; `o` = hover in place.
4. **Recall:** `r` (or automatically, see the table). The drone comes back and lands on the ANT; the ANT pauses for the touchdown, then **the patrol resumes by itself**.
5. **Fly again:** pause the patrol (`p`), then `t`. Takeoff only from a standing ANT.
6. **End:** `q`. If flying: recall, land on the ANT, then quit. Then `q` in `mission_link`.

| Key | Action |
|---|---|
| `t` | takeoff from the ANT (type FLY; the ANT must stand still; the drone must sit on the ANT) |
| `p` | ANT patrol ON / OFF |
| `e` | **ESCORT:** random points 0.5–1.0 m around the ANT's *current* position, 0.5–0.8 m above the floor. New point when reached or after 8 s. It moves along with the driving ANT |
| `s` | **SCOUT:** 1.0 m ahead of the ANT along its **direction of travel** (its nose when standing), 0.7 m high, following it |
| `f` | **ROAM:** random points in an AREA (`-p area:="xmin,xmax,ymin,ymax"`, drone frame) or 0.8 m around its takeoff spot. **Independent of the ANT.** Use `cf_guard -p area:=` (not the leash) |
| `1` / `2`, then a key | the next command only for cf1 / cf2 (two drones) |
| `o` | HOLD: hover where it is |
| `r` | RECALL: come back and land on the ANT (all drones, or the selected one) |
| `x` | **STOP EVERYTHING:** the ANT stops, patrol OFF, the drone lands where it is (plate if above the ANT, else floor) |
| `q` | recall (if flying), then quit |
| rviz "Publish Point" | add a patrol waypoint |

**Recall:**

| State | What happens | Next when |
|---|---|---|
| APPROACH | fly above the ANT (plate + 0.5 m), re-aimed every second **while it keeps patrolling** | ≤ 0.25 m from the ANT (xy) |
| PAUSE_ANT | `/ant/stop`: the ANT stops (patrol paused) | the ANT reports still for 1 s (re-stop after 8 s) |
| ALIGN | hover at plate centre + 0.4 m | < 8 cm off for 2 s. After 20 s: retry once, then **BESIDE**: land on the floor 0.6 m next to the ANT |
| DESCEND | slowly, **5 cm/s**, to plate + 0.15 m | ~6 s |
| LAND | `land` at `plate_z` (3 s) | touchdown; prints `touchdown ON THE ANT: N cm from its centre` |
| DISARM | disarm 2 s after touchdown | 3 s |
| (IDLE) | the **patrol resumes** if it was on | `t` = fly again |

**Recall triggers:** `r`; the battery below `recall_v` (3.55 V) for 3 s; the flight longer than `max_flight` (240 s); `q`.

**Abort:** ANT data missing for more than 2 s while flying: **hover**. Still missing after 10 s: **land on the floor** where it is. Without the ANT's position, landing on it is impossible.

**Speeds:**
- every drone move is timed for 0.15 m/s; the descent onto the plate goes at 5 cm/s;
- **keep the ANT at 0.1 m/s** (`ant1_nav_speed 0.1 0.3 --live`), otherwise the scout and the approach fall behind.

---

### 6.1 Two drones (`CF_DRONES=2`, `crazyflies_two.yaml`)
- **Plate slots:** cf1 15 cm **in front** of the centre, cf2 15 cm **behind**, noses forward. Takeoff checks that each one sits on the ANT.
- **Takeoff** is staggered: cf2 goes 4 s after cf1, to its own height.
- **Heights:** cf1 cruises at 0.55 m, cf2 at 0.90 m in every formation, so crossing paths stay 35 cm apart vertically. Escort gives each drone its own half around the ANT; scout puts them side by side, 0.7 m apart; roam targets keep ≥ 0.6 m apart.
- **Landing queue:** only the "owner" of the plate lands. The other waits 0.9 m **beside** the ANT (out of the downwash), then comes in. The ANT stays paused until both are down; then the patrol resumes.
- **The guard** (`cf_guard`) watches both. **SPACE lands all, `K` kills all**; the status line shows both.
- **Not shared:** `cf_keys`, `mission_follow` and `mission_hop` take one drone (`CF=cf2 cf_keys`, `-p cf:=cf2`, `-p cfs:=cf2`).
- **Finding the drones:** see docs/09 section B1 (`cf_identify`; a sticker "1"/"2"; same channel, different addresses).

### 6.2 Carrier hop (`mission_hop`)
- **`g`** sets a target (ANT map, or rviz click). **`h`**: the ANT drives toward it; `ant_link` redirects to the **closest reachable point** if it's blocked.
- **READY:** the remaining distance must be ≤ `max_hop` (1.8 m, inside the 2 m leash).
- **`t` + FLY:** takeoff, climb to `hop_z` (0.8 m), fly over, hover `dwell` (5 s), then the recall (land on the ANT, disarm). **The ANT drives back** to its start.
- **Interruptions:** a battery recall mid-hop jumps straight to the return leg. `x` aborts.

## 7. Safety layers (who stops what)

| Layer | Watches | Does |
|---|---|---|
| `ant1_watchdog` (A1) | the ANT's `cmd_vel` stream | STOP when commands stop while moving (laptop side) |
| Nav2 on the robot | obstacles (lidar), costmap | plans around them; its velocity smoother stops the ANT if Nav2 stops |
| `ant_link` | `/ant/stop`, its own exit | cancels **all** Nav2 actions + zeros; **pauses Nav2** if the ANT is still being driven |
| `mission_follow` / `mission_scout` | drone state, ANT data, battery, time | stop the ANT / recall / land on the floor if the ANT is lost |
| `cf_guard -p leash:=2.0` or `-p area:=...` | every drone: leash to the ANT / fixed area, battery < 3.3 V, link lost | lands the drone (plate if above the ANT, else floor); SPACE = land all, `K` = motors off for all |
| guard takeover (`/cfN/guard_event`) | a guard landing / kill | the missions and `cf_keys` **stop commanding** that drone (mode `GUARD`): a `go_to` would cancel the landing in the firmware. **The guard also re-lands** if the drone isn't descending 1.5 s after its landing (seen in a test race) |
| you | everything | **ANT: e-stop. Drone: SPACE in `cf_guard`; catch it and turn it upside down** |

**Rules:**
- **The ANT pauses for every touchdown** (recall) and must stand still for every takeoff. Both are enforced.
- **The ANT has no `cmd_vel` timeout**, so keep `ant1_watchdog` running. Before releasing the ANT e-stop: `python3 scripts/ant1_diag/cancel_all_goals.py`.
- **The drone keeps hovering if the radio link dies:** catch it and flip it.
- **Low and slow:** drone 0.15 m/s ≤ 1 m high; ANT 0.1 m/s during missions.
- **Code changes:** test against the fakes (`sim_all.sh`) before the real robots, like `fake_nav2` / `fake_cf`.

---

## 8. Command reference

| Command | Env | What |
|---|---|---|
| `mission_link` | `scripts/mission_env.sh` | the bridge (`ant_link`). Keys `s` (stop the ANT), `q` (quit, stops the ANT). Env: `ANT1_DOMAIN` (0), `CF_DOMAIN` (42), `NS`, `MISSION_CALIB` |
| `mission_calib [-p ant_height:= -p offset_x:= -p offset_y:=]` | `cf_env.sh` | calibration: `w` fit + save, `s` snapshot, `r` restart, `q` quit |
| `mission_follow [-p deadband:=0.4 -p min_move:=0.3 -p period:=2.0]` | `cf_env.sh` | Method 1 |
| `mission_scout -p waypoints:="x,y; x,y" [-p recall_v:= -p max_flight:= -p speed:=]` | `cf_env.sh` | Method 2 |
| `mission_rviz` | `cf_env.sh` | 3D view (frame `world`) |
| `cf_guard -p leash:=2.0` | `cf_env.sh` | guard with the leash to the ANT |
| `cf_keys` | `cf_env.sh` | with ANT data: `h` = above the ANT, landing on the plate, no takeoff while the ANT drives |
| `bash scripts/mission_tmux.sh 1\|2\|sim1\|sim2` | container | all terminals as tmux windows |
| `bash scripts/mission_diag/sim_all.sh start\|drive\|stop` | container | the simulation |

**Topics** (drone domain 42, for your own code):

| Topic | Type | Direction |
|---|---|---|
| `/ant/pose_room` | `geometry_msgs/PoseStamped` (frame `world`, z = plate) | from `ant_link`, 10 Hz |
| `/ant/pose_map` | `geometry_msgs/PoseStamped` (frame `ant_map`) | from `ant_link`, 10 Hz |
| `/ant/moving` | `std_msgs/Bool` | from `ant_link` |
| `/ant/nav_state` | `std_msgs/String` (idle/sent/executing/succeeded/aborted/canceled/stopped) | from `ant_link`, latched |
| `/mission/calib` | `std_msgs/String` (YAML) | from `ant_link`, latched |
| `/ant/goal` | `geometry_msgs/PoseStamped` (frame `world` or `ant_map`; orientation all 0 = keep heading) | to `ant_link` |
| `/ant/stop` | `std_msgs/Empty` | to `ant_link` |

Example: send the ANT 1 m along the room's x axis from where the drone is:
```bash
ros2 topic pub --once /ant/goal geometry_msgs/msg/PoseStamped "{header: {frame_id: world}, pose: {position: {x: 1.0, y: 0.0}}}"
ros2 topic pub --once /ant/stop std_msgs/msg/Empty "{}"
```

---

## 9. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| L1: `ANT: no pose yet` | the ANT isn't reachable from the bridge: wrong `ANT1_IFACE`/`ANT1_PEER` in `mission_env.sh`; Mapping/Navigation not running; Wi-Fi discovery flaky (use the peer, as on 10 Oct) |
| L1: `ROS_LOCALHOST_ONLY=1 would cut the ANT off` | you sourced `cf_env.sh` in the bridge terminal: open a new terminal with `mission_env.sh` |
| `NO CALIB` everywhere | run `mission_calib` and press `w` (or check that `data/mission_calib.yaml` exists) |
| the drone in rviz isn't on the ANT box | calibration stale (SLAM reset? new map?) → redo `mission_calib` |
| `mission_calib`: no stops recorded | the ANT never stood still for 0.6 s, or moved < 15 cm between stops; or the drone is flying / has no position |
| fit RMS > 5 cm | drive slower, stop longer, drone centred, Lighthouse in view, include a turn; or the SLAM map is drifting |
| `cf_keys`/`mission_scout` takeoff refused | the ANT is driving (pause the patrol), the drone isn't on the ANT, or its position jumps (Lighthouse not seen) |
| the ANT doesn't move to goals | `nav` in L1: `aborted` (unreachable?) / `never confirmed` (Navigation not running?). Also check `ant1_rviz` |
| the scout lags behind | the ANT is too fast: `ant1_nav_speed 0.1 0.3 --live` |
| the drone lands next to the ANT | ALIGN failed twice (wind, drift, calibration error): check the calibration RMS; land manually with `cf_keys` `h` then SPACE |
| `[guard] off the leash` | the drone more than 2 m from the ANT: the ANT couldn't follow (blocked?) → `mission_follow` status, Nav2 state |

---

## 10. Suggestions (next ideas)
1. **"Carrier hop":** the ANT carries the drone to the closest reachable point next to a target it can't reach (on or behind a table). The `free_goal` flood fill in `ant1_nav.py` already finds that point. The drone hops over the obstacle to the target, hovers, comes back and lands on the ANT, and the ANT drives back. This mostly reuses the recall state machine, and it shows why air plus ground beats either alone.
2. **SLAM accuracy check against Lighthouse ground truth:** already built into `mission_calib` (`SLAM vs Lighthouse` + `data/mission_calib.png`). Do a longer calibration drive around the room for a measured, presentable number.
3. **Later, with the D555:** the ANT confirms the drone visually above it before the touchdown.

---

## 11. What was tested (fakes, 10–11 Oct) and what wasn't

| Test | Result |
|---|---|
| one process in two DDS domains (domain 42 unchanged, `ROS_LOCALHOST_ONLY=1`) | received / sent on both |
| `ant_link`: pose bridging, goals (map / world frame), stop cancels all actions, stop on quit | ok |
| calibration vs the fake's hidden true transform (30°, (2, −1)) | stops: **30.0°, (2.00, −1.00), RMS 0.0 cm**; snapshot: exact. A continuous drive was biased by 2–3°, so it's now stop-based |
| Method 1: the ANT reaches under the drone (0.04 m), stops when the drone lands; drone lands on the plate | ok |
| Method 2: patrol 3 waypoints, escort → scout → escort in flight, recall `r` → touchdown 0 cm from centre → patrol resumes | ok |
| recall triggers: battery drain, flight-time limit | ok, landed on the ANT |
| `ant_link` killed mid-flight | hover, then floor landing after 10 s; ANT stopped |
| leash 2 m | the guard landed the drone on the floor at 2.13 m |
| regressions: `ant1_goto` (8 fake modes), `cf_guard`, `cf_keys` without `ant_link` | unchanged |
| roam, one drone (patrolling ANT, drone 1.4 m away, independent) → `r` | landed on its slot |
| two drones: staggered takeoff, escort, cf1 scout + cf2 roam, recall both | **queue: cf1 lands, then cf2, both 0 cm off their slots**, patrol resumes |
| guard SPACE with two drones roaming | both `GUARD`, no more commands; a landing overridden by a racing `go_to` was **re-landed by the guard** (then the race was fixed: the missions now process all messages before acting) |
| carrier hop (target inside a fake wall) | the ANT stopped 0.48 m before it (closest reachable), hop, hover, **landed on the plate**, the ANT drove home |
| `cf_keys`: moves while on the ground | refused (an armed drone on the ground could take off on a `go_to`) |

**Not tested yet:** anything on the real robots. In particular:
- the dual-domain bridge over the real hotspot;
- Lighthouse coverage over the ANT's area;
- the real plate height;
- landing precision on the real plate;
- Nav2 behaviour with goals every 2 s.

Follow section 2.5 for the first real runs.

---

## 12. Files
| File | What |
|---|---|
| `ws/src/team_pkg/team_pkg/ant_link.py` | the bridge |
| `ws/src/team_pkg/team_pkg/mission_common.py` | calibration math (`fit_2d`, `Calib`), `AntView` (ANT data for drone-side nodes), landing height |
| `ws/src/team_pkg/team_pkg/mission_calib.py` | calibration tool |
| `ws/src/team_pkg/team_pkg/mission_follow.py` | Method 1 |
| `ws/src/team_pkg/team_pkg/mission_scout.py` | Method 2 (escort / scout / roam, one or two drones) |
| `ws/src/team_pkg/team_pkg/mission_fleet.py` | per-drone machinery: plate slots, height layers, takeoff, recall state machine with the landing queue, guard takeover |
| `ws/src/team_pkg/team_pkg/mission_hop.py` | carrier hop |
| `ws/src/team_pkg/config/crazyflies_two.yaml` | two-drone config (cf2 URI is a placeholder until identified) |
| `scripts/cf_diag/find_drones.py` | `cf_find` / `cf_identify` |
| `ws/src/team_pkg/team_pkg/ant1_nav.py` | shared ANT pieces (`free_goal` reachability, the `ACTIONS` cancel list), also used by `ant1_goto` |
| `ws/src/team_pkg/team_pkg/cf_guard.py`, `cf_keys.py` | ANT-aware: leash, plate/floor landing, no takeoff while the ANT drives |
| `ws/src/team_pkg/config/mission.rviz` | the joint 3D view |
| `scripts/mission_env.sh` | env for the bridge terminal (two-domain CycloneDDS config) |
| `scripts/cf_env.sh` | `mission_*` helpers |
| `scripts/mission_tmux.sh` | all terminals in tmux |
| `scripts/mission_diag/sim_all.sh` | the simulation |
| `scripts/ant1_diag/fake_nav2.py` (mode `drive`), `scripts/cf_diag/fake_cf.py` (mode `onant`) | the fakes |
| `data/mission_calib.yaml`, `.png` | the calibration (runtime, gitignored) |
