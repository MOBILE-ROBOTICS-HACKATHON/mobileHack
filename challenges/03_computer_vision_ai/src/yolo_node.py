#!/usr/bin/env python3
"""YOLO detector as a ROS 2 node.

 sub:  image_raw            (sensor_msgs/Image)
 pub:  detections           (std_msgs/String, JSON list: label, conf, bbox xyxy, center)
 pub:  image_annotated      (sensor_msgs/Image)

    python3 yolo_node.py --model yolov8n.pt --topic /camera/image_raw --conf 0.4

Weights download on first run (internet needed): DO THIS AT HOME before the event
(`python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"`) and keep the .pt in ../models/.
"""
import argparse
import json
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
from ultralytics import YOLO


class YoloNode(Node):
    def __init__(self, model, topic, conf, device):
        super().__init__("yolo_node")
        self.model = YOLO(model)
        self.conf, self.device = conf, device
        self.bridge = CvBridge()
        self.create_subscription(Image, topic, self.on_image, qos_profile_sensor_data)
        self.pub_det = self.create_publisher(String, "detections", 10)
        self.pub_img = self.create_publisher(Image, "image_annotated", 10)
        self.busy = False

    def on_image(self, msg: Image):
        if self.busy:        # drop frames instead of building latency
            return
        self.busy = True
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            res = self.model.predict(frame, conf=self.conf, device=self.device, verbose=False)[0]
            dets = []
            for b in res.boxes:
                x1, y1, x2, y2 = [float(v) for v in b.xyxy[0]]
                dets.append({
                    "label": res.names[int(b.cls[0])], "conf": round(float(b.conf[0]), 3),
                    "bbox": [x1, y1, x2, y2], "center": [(x1 + x2) / 2, (y1 + y2) / 2],
                    "img_w": frame.shape[1], "img_h": frame.shape[0],
                })
            self.pub_det.publish(String(data=json.dumps(dets)))
            out = self.bridge.cv2_to_imgmsg(res.plot(), "bgr8")
            out.header = msg.header
            self.pub_img.publish(out)
        finally:
            self.busy = False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="yolov8n.pt")
    ap.add_argument("--topic", default="image_raw")
    ap.add_argument("--conf", type=float, default=0.4)
    ap.add_argument("--device", default="cpu")     # "cuda:0" if GPU torch is available
    a, _ = ap.parse_known_args()
    rclpy.init()
    rclpy.spin(YoloNode(a.model, a.topic, a.conf, a.device))


if __name__ == "__main__":
    main()
