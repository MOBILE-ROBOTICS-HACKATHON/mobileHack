#!/usr/bin/env python3
"""Gesture teleop: your hand drives the robot (webcam -> MediaPipe -> cmd_vel).

Controls (right hand in front of camera):
  hand centre y  -> forward / backward speed     (up = forward)
  hand centre x  -> turn left / right
  closed fist    -> stop (safety!)

Install (inside Docker, once):  pip3 install mediapipe "numpy<2"
Run:   python3 gesture_teleop.py --source 0 [--no-ros]
--no-ros prints commands only, so you can test the vision part anywhere.
Replace the mapping with whatever feels intuitive: judged on usability/latency, not model complexity.
"""
import argparse
import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands


def is_fist(lm):
    """fingertips below their PIP joints (in image y) => fingers curled."""
    tips, pips = [8, 12, 16, 20], [6, 10, 14, 18]
    return sum(lm[t].y > lm[p].y for t, p in zip(tips, pips)) >= 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="0")
    ap.add_argument("--no-ros", action="store_true")
    ap.add_argument("--max-v", type=float, default=0.2)
    ap.add_argument("--max-w", type=float, default=1.0)
    a = ap.parse_args()

    pub = None
    if not a.no_ros:
        import rclpy
        from geometry_msgs.msg import Twist
        rclpy.init()
        node = rclpy.create_node("gesture_teleop")
        pub = node.create_publisher(Twist, "cmd_vel", 10)

    cap = cv2.VideoCapture(int(a.source) if a.source.isdigit() else a.source)
    with mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.6) as hands:
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            res = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            v = w = 0.0
            if res.multi_hand_landmarks:
                lm = res.multi_hand_landmarks[0].landmark
                if not is_fist(lm):
                    cx = sum(p.x for p in lm) / len(lm)
                    cy = sum(p.y for p in lm) / len(lm)
                    v = max(-1, min(1, (0.5 - cy) * 3)) * a.max_v          # dead-zone would improve feel
                    w = max(-1, min(1, (0.5 - cx) * 3)) * a.max_w
            print(f"v={v:+.2f} w={w:+.2f}", end="\r")
            if pub:
                from geometry_msgs.msg import Twist
                t = Twist(); t.linear.x, t.angular.z = v, w
                pub.publish(t)
            cv2.imshow("gesture teleop (q to quit)", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    if pub:
        pub.publish(Twist())     # stop on exit
        rclpy.shutdown()


if __name__ == "__main__":
    main()
