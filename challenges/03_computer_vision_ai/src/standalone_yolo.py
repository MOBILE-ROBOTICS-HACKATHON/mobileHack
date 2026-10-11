#!/usr/bin/env python3
"""Plain-Python (no ROS) vision playground: run on any image / video / webcam.

    python3 standalone_yolo.py --source path/to/img.jpg
    python3 standalone_yolo.py --source 0                     # webcam
    python3 standalone_yolo.py --source video.mp4 --save out.mp4
Press q to quit. Use this to test models/thresholds fast, then move them into a ROS node.
Also prints latency: you need >10 FPS for a robot to react.
"""
import argparse
import time
import cv2
from ultralytics import YOLO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--model", default="yolov8n.pt")
    ap.add_argument("--conf", type=float, default=0.4)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--save", default=None)
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()

    model = YOLO(a.model)
    src = a.source
    if src.lower().endswith((".jpg", ".jpeg", ".png")):
        r = model.predict(src, conf=a.conf, device=a.device)[0]
        out = r.plot()
        cv2.imwrite(a.save or "out.jpg", out)
        print([(r.names[int(b.cls[0])], round(float(b.conf[0]), 2)) for b in r.boxes])
        return
    cap = cv2.VideoCapture(int(src) if src.isdigit() else src)
    writer = None
    n, t0 = 0, time.time()
    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break
        r = model.predict(frame, conf=a.conf, device=a.device, verbose=False)[0]
        out = r.plot()
        n += 1
        cv2.putText(out, f"{n / (time.time() - t0):.1f} FPS", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        if a.save and writer is None:
            writer = cv2.VideoWriter(a.save, cv2.VideoWriter_fourcc(*"mp4v"), 20, (out.shape[1], out.shape[0]))
        if writer:
            writer.write(out)
        if a.show:
            cv2.imshow("yolo", out)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    print(f"avg FPS: {n / (time.time() - t0):.1f}")


if __name__ == "__main__":
    main()
