# Exercise 3: Run perception in ROS + close the loop in the sim

## A. Detector on the fake camera (no robot needed)
```bash
# T1
python3 challenges/03_computer_vision_ai/src/image_source.py
# T2
python3 challenges/03_computer_vision_ai/src/yolo_node.py
# T3
ros2 topic hz /image_raw /image_annotated
ros2 run rqt_image_view rqt_image_view     # choose /image_annotated
```
Synthetic shapes won't trigger YOLO classes; use a real video: `--source clip.mp4` (download any street/people clip) or a webcam.

## B. Simulated robot follows an object
The TB3 **waffle** has a camera (`/camera/image_raw`).
```bash
# T1 sim
ros2 launch turtlebot3_gazebo turtlebot3_house.launch.py     # richer scene w/ furniture
# T2 detector on the sim camera
python3 challenges/03_computer_vision_ai/src/yolo_node.py --topic /camera/image_raw
# T3 view
ros2 run rqt_image_view rqt_image_view
# T4 follow (in Gazebo insert a person/ball model; label must match a COCO class)
python3 challenges/03_computer_vision_ai/src/follow_object.py --label person
```
Tasks:
1. Measure end-to-end latency: image stamp vs. time the detection is published. Add that to the node.
2. Add a tracker (ByteTrack: `model.track(frame, persist=True)`) so the robot follows the *same* object when several are in view.
3. Replace the P-controller by a PID + low-pass filter on detections; show the robot trace is smoother.
4. Failure analysis: blur the image, lower brightness, or add noise (`cv2.GaussianBlur`). At what point does detection fail? What's your fallback?
