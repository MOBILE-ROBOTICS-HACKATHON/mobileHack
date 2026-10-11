# Exercise 5: Foundation models for robot perception

Fits a 4 GB GPU / Jetson. Run these on the **host ML venv** (`source .venv-ml/bin/activate`) or in the container (CPU).

## 1. Open-vocabulary detection (no retraining: "find the blue backpack")
```python
from ultralytics import YOLO
m = YOLO("yolov8s-worldv2.pt")        # YOLO-World
m.set_classes(["red cup", "backpack", "person with helmet"])
m.predict("img.jpg", conf=0.2, save=True)
```
Wrap it exactly like `yolo_node.py` (swap the model; add a `/set_classes` String subscriber so a UI can change targets at runtime).

## 2. CLIP zero-shot classification / semantic search
```bash
uv pip install open_clip_torch      # or: pip install transformers
```
Embed crops/frames once; query with text ("kitchen", "an open door") by cosine similarity. Use it for *place recognition*: store embedding + robot pose per keyframe → "go to the kitchen".

## 3. Small VLM for scene questions
Candidates that fit ~4 GB in fp16/int4: SmolVLM-256M/500M, Moondream2, Qwen2-VL-2B (int4). Throughput is ~1–3 s/frame → use *event-triggered* queries ("describe what you see"), never in the control loop.

## 4. Depth from a single image (when you have no depth camera)
Depth-Anything-V2-small (ONNX/TensorRT) → relative depth; calibrate scale with lidar at the centre pixel.

## 5. Segmentation
`YOLO("yolov8n-seg.pt")` for masks → drivable-area / floor segmentation → cost map layer for Nav2.

## Mini-project (2–3 h)
"Text-commanded navigation": type "go to the <thing>" → open-vocab detector locates it → geometry (Exercise 4) → Nav2 goal. Log failure cases: occlusion, lighting, similar objects.

**Pre-download before the event:** `yolov8n.pt`, `yolov8s.pt`, `yolov8n-seg.pt`, `yolov8s-worldv2.pt`, CLIP weights, your VLM → copy to `models/`.
