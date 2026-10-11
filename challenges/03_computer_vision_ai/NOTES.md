# NOTES: Challenge 03 · Computer Vision & AI (SmartSight · Insight AI)

Read top to bottom for the full picture. Hands-on steps in `exercises/`, plan in `ROADMAP.md`.

## 1. The challenge in plain words
Build a **perception application** that solves a real problem with robot sensors: object detection, semantic understanding, visual localization, vision-language reasoning, or foundation models: your choice. It is open-ended, so the quality of the **problem statement, the demo and the evaluation** decide the result. A detector alone is a notebook; a detector that makes a robot *do something* is a demo.

## 2. Concepts you must understand
**Image topics**: `sensor_msgs/Image` (raw) or `CompressedImage`. Encodings: `bgr8`/`rgb8`/`mono8`/`16UC1` (depth in mm). OpenCV expects **BGR**. `cv_bridge` converts between ROS images and numpy arrays.

**Latency budget**: control loops need perception < ~100 ms. Drop frames instead of queueing (`busy` flag in `yolo_node.py`), use small models, resize inputs.

**Detection / segmentation / tracking**
- *Detection* (YOLO): boxes + class + confidence. *Segmentation*: pixel masks. *Tracking* (ByteTrack/BoT-SORT via `model.track`): persistent IDs → follow the *same* object.
- Metrics: precision, recall, mAP, IoU; confidence threshold trades false positives vs misses.
- *Open-vocabulary* (YOLO-World, OWL-ViT, GroundingDINO): detect classes you name in text, with no retraining.

**Foundation models**
- *CLIP*: image/text embeddings; zero-shot classification and semantic search by cosine similarity.
- *VLMs* (SmolVLM, Moondream, Qwen2-VL): answer questions about an image. Slow (seconds), use event-triggered.
- *Depth models* (Depth-Anything): relative depth from one image.

**Camera geometry** (pinhole): pixel `(u,v)` + depth `Z` → 3D point: `X=(u−cx)Z/fx`, `Y=(v−cy)Z/fy`. Intrinsics from `CameraInfo`. Without a depth camera, get `Z` from lidar at the same bearing, or from the known object size.
**Camera → map**: transform the 3D point through TF (`camera_optical_frame → map`) with the *image's timestamp*.

**Classical CV**: HSV colour thresholding, contours, morphology, Hough lines, AprilTags (`solvePnP`). Frequently more robust and faster than a neural net for a coloured cube, tape line or marker, and it needs no GPU.

**Visual servoing**: control the robot directly from image error: turn until the object is centred, drive until the box is big enough (`follow_object.py`).

**Domain shift**: models trained on COCO see venue lighting, odd angles, blur. Test on venue data early; fine-tune with ~100 labelled images if needed.

## 3. Packages: what each does
| Package | Role |
|---|---|
| `ultralytics` | YOLOv8/YOLO-World/segmentation/tracking; `.predict()`, `.track()`, `.train()` |
| `torch`, `torchvision` | Deep learning (CPU in container, CUDA on host venv) |
| `opencv-python-headless` (`cv2`) | Image processing (no GUI windows in the container: use `rqt_image_view` or save files) |
| `cv_bridge`, `image_transport`, `vision_opencv` | ROS ↔ OpenCV; compressed/raw transport |
| `v4l2_camera` | ROS driver for USB webcams (`ros2 run v4l2_camera v4l2_camera_node`) |
| `apriltag_ros` | AprilTag detection → TF poses |
| `rqt_image_view` | View image topics |
| `tf2_ros`, `tf2_geometry_msgs` | Transform points between frames |
| `numpy` (<2!) | NumPy 2 breaks Humble's `cv_bridge` |
| (on demand) `open_clip_torch`, `transformers`, `mediapipe` | CLIP / VLMs / pose-hands |

## 4. The code in `src/`
| File | Teaches | Run |
|---|---|---|
| `opencv_basics.py` | HSV segmentation, contours, pixel→bearing | `python3 src/opencv_basics.py` |
| `standalone_yolo.py` | YOLO on image/video/webcam + FPS, no ROS | `python3 src/standalone_yolo.py --source img.jpg` |
| `image_source.py` | publishes webcam/video/synthetic frames as `/image_raw` (no robot needed) | `python3 src/image_source.py --source clip.mp4` |
| `yolo_node.py` | YOLO as a ROS node: `/detections` (JSON) + `/image_annotated` | `python3 src/yolo_node.py --topic /camera/image_raw` |
| `follow_object.py` | closed loop: detection → `cmd_vel`, with watchdog | `python3 src/follow_object.py --label person` |

## 5. What you should DO, in order (≈8 h)
1. `opencv_basics.py` (30 min): change HSV range, print bearings.
2. `standalone_yolo.py` on a few images and a video (45 min): measure CPU FPS; try `yolov8n/s`, confidences.
3. ROS wrapping (1.5 h): `image_source.py` + `yolo_node.py` + `rqt_image_view`.
4. `exercises/03_sim_follow.md` (1.5 h): detector on the simulated camera and robot following the object.
5. `exercises/04_geometry_3d.md` (1 h): pixel → bearing/3D → map frame; write `object_to_map.py`.
6. `exercises/05_foundation_models.md` (1.5 h): YOLO-World/CLIP; pick one.
7. `exercises/06_apriltags.md` (30 min).
8. Pre-download weights (see below).

## 6. How to prepare for the real robot
- First hour: find the real image topic (`ros2 topic list -t | grep -i image`), its encoding, rate, and whether only `compressed` exists (then `ros2 run image_transport republish compressed raw --ros-args -r in/compressed:=/cam/image_raw/compressed -r out:=/image_raw`).
- Record a 1-2 minute bag of the arena camera → develop offline.
- Compute: laptop (CPU in container or GPU in host venv). The venue also offers a Jetson AGX Orin: ask mentors how to use it.
- Re-tune thresholds in venue lighting; collect a few images of your target objects and fine-tune if the stock model fails.
- Pre-download **all** weights now; the venue network will be busy.

```bash
# HOST venv or CONTAINER
python3 -c "from ultralytics import YOLO; [YOLO(m) for m in ['yolov8n.pt','yolov8s.pt','yolov8n-seg.pt','yolov8s-worldv2.pt']]"
mv *.pt challenges/03_computer_vision_ai/models/    # then pass --model path
```

## 7. Idea menu (choose one before Saturday)
| Idea | Effort | Impact |
|---|---|---|
| Follow-me robot with tracking | low | medium |
| Text-commanded fetch: "go to the red cup" (open-vocab → map goal → Nav2) | medium | high |
| Semantic map of the arena with object labels, queryable by text | med-high | very high |
| Safety monitor: people near the robot → slow/stop | low-med | medium |
| AprilTag docking / relocalization | medium | medium |
| VLM scene reporting ("is the corridor blocked?") | medium | high |
Make it measurable: precision/recall on a small labelled set, FPS, end-to-end latency, task success rate over N trials.

## 8. Common failures and fixes
| Symptom | Fix |
|---|---|
| `_ARRAY_API not found` | numpy 2 installed → `pip3 install "numpy<2"` |
| No image received | QoS: use `qos_profile_sensor_data`; wrong topic; compressed only |
| Colours wrong | RGB vs BGR |
| Detection lags / huge latency | busy-flag frame dropping, smaller model, resize, GPU |
| Object 3D position off | wrong frame (optical vs link), wrong timestamp, wrong intrinsics |
| Works at home, fails on site | lighting/background shift → collect venue data, tune thresholds, fine-tune |
| Out of GPU memory (4 GB) | use `n`/`s` models, batch 1, fp16, or CPU/Jetson |

## 9. Glossary
bbox · BGR · CLIP · confidence · cv_bridge · depth · FPS · FoV · IoU · intrinsics · mAP · NMS · optical frame · open-vocabulary · tracking · VLM · zero-shot.

## 10. Readiness checklist
- [ ] YOLO runs on my machine, I know the FPS, and weights are saved locally.
- [ ] `yolo_node` publishes annotated images I can see in rqt.
- [ ] The simulated robot follows an object using `follow_object.py`.
- [ ] I can compute a bearing and a 3D/map position from a pixel and explain the maths.
- [ ] I have one chosen demo idea with a measurable success metric.
- [ ] Weights + docs downloaded for offline use.

## 11. Resources
Ultralytics docs · OpenCV tutorials (colour spaces, contours, camera calibration) · "Multiple View Geometry" ch.6 (camera model, skim) · CLIP / YOLO-World GitHub pages · AprilRobotics GitHub.
