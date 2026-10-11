# Challenge 03: Computer Vision & AI (SmartSight · Insight AI)

> Brief: build an innovative perception application: object detection, semantic understanding, visual localization,
> vision-language reasoning, or foundation models. Intelligent perception that solves real-world problems.

You know ML, so your edge is **integration speed**. Perception that never touches the robot is a notebook, not a demo.
Aim for: *camera → model → decision → robot does something visible.*

## Pipeline mental model
```
camera (sensor_msgs/Image, BEST_EFFORT)
  → cv_bridge → numpy BGR
  → model (YOLO / CLIP / VLM / depth)         ← latency budget < 100 ms per frame
  → geometry (pixel → bearing / 3D point in camera frame → TF → map frame)
  → action (cmd_vel / NavigateToPose / alert / dashboard)
```
Drop frames rather than queue them (see `busy` flag in `yolo_node.py`). Latency kills control loops.

## Study order (≈8 h)
| # | Time | What | Where |
|---|---|---|---|
| 1 | 1h | Classical CV: HSV threshold, contours, pixel→bearing | `src/opencv_basics.py` |
| 2 | 1h | YOLO standalone: models, thresholds, FPS on CPU vs GPU | `src/standalone_yolo.py` |
| 3 | 1.5h | YOLO as a ROS 2 node + fake camera | `src/image_source.py`, `src/yolo_node.py` |
| 4 | 1.5h | Close the loop: robot follows detected object in the TB3 sim | `src/follow_object.py`, `exercises/03_sim_follow.md` |
| 5 | 1h | Camera geometry: intrinsics, depth, pixel→3D→map frame | `exercises/04_geometry_3d.md` |
| 6 | 1.5h | Foundation models: CLIP / open-vocab (YOLO-World) / VLM | `exercises/05_foundation_models.md` |
| 7 | 0.5h | AprilTags (visual localization) | `exercises/06_apriltags.md` |

## Choose a demo idea (pick before the hackathon starts, adapt on-site)
| Idea | Difficulty | Wow | Needs |
|---|---|---|---|
| Robot follows a person/object | Easy | ★★ | camera + cmd_vel |
| "Go to the red cup": open-vocab detection → Nav2 goal | Med | ★★★★ | detector + depth/lidar + Nav2 (Challenge 01) |
| Semantic map: robot patrols, labels objects on the map, answers "where's the chair?" | Med-Hard | ★★★★★ | detections + TF + map |
| Safety monitor: detect people near moving robot → slow/stop | Easy-Med | ★★★ | camera + lidar |
| AprilTag-based visual localization/docking | Med | ★★★ | tags + camera calib |
| VLM scene description of what the robot sees ("is the door open?") | Med | ★★★★ | small VLM, GPU/Jetson or API (is internet there?) |

**Compute reality:** your laptop has an RTX 3050 (4 GB). YOLOv8n/s run realtime; CLIP ViT-B fine; big VLMs won't fit: use a small one (e.g. SmolVLM, Moondream) or a hosted API if the network allows. A Jetson AGX Orin is available at the venue.
Install GPU PyTorch on the *host* (`scripts/setup_host_ml.sh`) and ship results over ROS from the container, or install nvidia-container-toolkit (see `PACKAGES.md`).

## Hackathon rules of thumb
- Download all model weights **now** (offline/crowded Wi-Fi). Put in `models/`.
- Start with the robot's real image topic ASAP: check encoding (`rgb8`/`bgr8`/`mono8`/compressed!). Compressed-only cameras need `image_transport republish`.
- Record a bag of the arena camera early; build against it.
- Test in venue lighting: re-tune thresholds; show the confusion matrix honestly in the pitch.
- Fine-tuning a detector on 100 labelled images of the venue objects (Roboflow / CVAT) in 20 min often beats a bigger model.

## Folder layout
```
src/          runnable scripts (see table)
exercises/    step-by-step guides
models/       put weights here (gitignored if large)
experiments/  YOUR notebook + LOG.md
```
