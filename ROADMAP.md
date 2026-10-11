# Overall Roadmap: Mobile Robotics Hackathon (TU Dresden, 10–11 Oct 2026)

Profile: Linux ✔, Python ✔, ML ✔. Focus tracks: **01 Navigation · 03 Computer Vision · 04 Imitation Learning**.
Your gap is **ROS 2 + robot-specific debugging**, not algorithms. Everything here is about closing that gap.

## 0. The strategy
1. ROS 2 fluency is the multiplier. Every track needs it. Spend ~40% of prep on it.
2. Build **one integrated skill chain** across your three tracks:
   `camera → detector (03) → map-frame target → Nav2 (01) → learned/hand-coded behaviour (04)`.
   Each piece is a separate exercise, but the demo that wins combines them.
3. Everything must run **offline**, in **Docker**, with weights **pre-downloaded**.
4. A small, reliable, *measured* demo beats an ambitious broken one.

## 1. Time budget (today Tue 6 Oct → Fri 9 Oct)
| Day | Hours | Block | Deliverable |
|---|---|---|---|
| **Tue 6** (tonight) | 3 | Register · Docker image built · `scripts/check_env.sh` all green · ROS 2 tutorials 1–4 · run `team_pkg` | Terminal: `ros2 topic echo /hello` works |
| **Wed 7** | 5 | ROS 2 core (TF2, QoS, launch, bags) · Nav track: exercises 01–03 (sim, TF/odom, SLAM) · pre-download all models | A saved SLAM map in `challenges/01_*/maps/` |
| **Thu 8** | 6 | Nav2 (ex. 04–05) · CV nodes (YOLO node, follow object) · IL toy + sim pipeline | `follow_object` + `waypoint_patrol` working; BC policy trained |
| **Fri 9** | 3 | Integrate the chain (object → map → Nav2), rehearse a 3-min pitch, pack, sleep early | Backup video of the integrated demo in the sim |
| **Sat 10** | – | See §3 | End-to-end skeleton by evening |
| **Sun 11** | – | See §3 | Pitch 17:00 |

If time is short, cut in this order: HRI/multi-robot (not your focus) → LeRobot (ex. 04) → foundation models (CV ex. 05) → SLAM tuning. **Never cut:** ROS 2 core, Nav2 basics, YOLO node.

## 2. Preparation phases (detailed)

### Phase A: Environment (Tue, ~2 h)
- [ ] Register: Eventbrite link on https://mobile-robotics.eu (75 seats!). 
- [ ] Docker image: `docker build -t hackathon-ros:humble -f docker/Dockerfile docker` (already started; log: `docker/build.log`).
- [ ] `./docker/run.sh`, then `bash scripts/check_env.sh` → all `[ok]`.
- [ ] GUI test inside the container: `rviz2` and `gazebo` windows open. (If not: `xhost +local:docker` on the host, see README troubleshooting.)
- [ ] Host ML env: `bash scripts/setup_host_ml.sh` → `torch.cuda.is_available()` is `True`.
- [ ] Optional: install the NVIDIA container toolkit so the container sees the GPU (see PACKAGES.md).

### Phase B: ROS 2 core (Tue–Wed, ~8 h)
Official tutorials (docs.ros.org → Humble → Tutorials), in this order:
1. Configuring environment · turtlesim & rqt · Nodes · Topics · Services · Parameters · Actions
2. Launch files · **tf2** (static + dynamic broadcaster, listener) · `rosbag2`
3. Writing publisher/subscriber (Python) · custom service/action (read, don't write)
4. **QoS** (concept page) · DDS config (`RMW_IMPLEMENTATION`, `ROS_DOMAIN_ID`, `ROS_LOCALHOST_ONLY`)

Verification tasks (do from memory in `ws/src/team_pkg`):
- [ ] Node: subscribe `/scan` → publish `/cmd_vel` (`challenges/01_*/src/obstacle_stop.py` is the reference answer: try first, peek later).
- [ ] Add a parameter and a launch file with a remap.
- [ ] Record a bag, replay with `--clock`, plot a topic with PlotJuggler.
- [ ] Explain `map → odom → base_link` aloud.

### Phase C: Track skills (Wed–Thu, ~12 h)
Follow each folder's `ROADMAP.md`. Order: **01 → 03 → 04**.
- **01 Navigation:** sim → TF/odom → SLAM → Nav2 → Python waypoints → tuning/failures.
- **03 CV:** OpenCV → YOLO standalone → YOLO node + fake camera → follow object → geometry → foundation models.
- **04 Imitation:** toy BC/DAgger → reading → record/train/deploy in sim → LeRobot.
- 02/05/06: read the ROADMAP only; run `turtlesim_swarm.py` and `gesture_teleop.py --no-ros` for 20 minutes each, in case you're pulled toward them.

### Phase D: Integration (Thu–Fri, ~5 h)
Build `experiments/integration/` (or in `ws/src/team_pkg`): launch file that starts Gazebo + Nav2 + YOLO node + `object_to_map` + a mission script. Target mission: *"find the <object>, drive to it, report"*. See `challenges/03_*/exercises/04_geometry_3d.md`.

### Phase E: Logistics (Fri)
- [ ] Laptop: charger, power strip, Ethernet/USB-C adapter, headphones, mouse.
- [ ] Offline: Docker image saved (`docker save hackathon-ros:humble | gzip > hackathon-ros.tar.gz` on a USB stick for teammates), model weights in `challenges/03*/models/`, `yolov8*.pt`, LeRobot caches (`~/.cache/huggingface`), PDFs of docs.
- [ ] Travel: Barkhausenbau (BAR), Georg-Schumann-Str. 11, Dresden. Doors 09:00 Sat; team formation 09:30 in Schönfeldhörsaal.
- [ ] Prepare a 30-second self-introduction listing your skills for team formation, and what you want from teammates (hardware/embedded, 3D/CAD, frontend, pitch).

## 3. The weekend plan

### Saturday
| Time | Action |
|---|---|
| 09:30 | Team formation. Look for: someone with real-robot experience, someone for UI/pitch. Aim for 3–4 people with mixed skills. |
| 09:30–10:45 | Pick the challenge **and the platform**. Ask mentors: topic names, ROS distro, DDS settings, Wi-Fi/5G, safety rules, e-stop. |
| 10:45–13:00 | **Milestone 1 (≤2 h):** can drive the robot from your laptop (`cmd_vel`) and see sensors in rviz. Everything else is blocked until then. |
| 13:00–17:00 | **Milestone 2:** core algorithm on real data (map built / detections streaming / demos recorded). Always record bags. |
| 17:00–19:00 | **Milestone 3:** end-to-end skeleton (ugly but complete). Commit. |
| 19:00–21:00 | BBQ; the party starts at 21:00. Sleep or hack: decide as a team. Record a **backup video** of the best run tonight. |

### Sunday
| Time | Action |
|---|---|
| 09:15–13:00 | Robustness: re-run 10 trials, fix the top 2 failure modes. Collect numbers (success rate, time, collisions, FPS, latency). |
| 13:00–16:00 | Feature freeze at ~14:00. Slides, rehearsal, backup video. Optional business pitch for LaunchHub42: market/use case/scalability. |
| 16:00 | Final preparation. Charge everything; test the demo at the presentation room; confirm network. |
| 17:00 | Present: problem → live demo (or video) → numbers → what we learned → next steps. |

## 4. Rules for working with real robots
1. **Domain ID**: pick a team-specific `ROS_DOMAIN_ID` (e.g. 10–50) and `export` it in every terminal. Others' robots on the same network are real.
2. Check distro compatibility: the Docker image is **Humble**; if a robot is Foxy/Jazzy, use matching images or rosbridge.
3. `use_sim_time:=false` on hardware.
4. Slow first: 0.1 m/s. Test next to the e-stop.
5. `ros2 bag record -a` on every run.
6. Commit every hour; push to a shared remote (bring a GitHub repo ready).
7. If stuck >20 min: ask a mentor. That's what they are there for.

## 5. Self-test (can you answer these by Friday?)
- What does `map→odom` represent, and who publishes it?
- Why can a subscriber receive no messages even though `ros2 topic list` shows the topic?
- How do you pass the initial pose to Nav2 from code?
- How do you convert a detection pixel to a map-frame coordinate?
- What is covariate shift, and how does DAgger address it?
- How do you make a learned policy safe on hardware?
