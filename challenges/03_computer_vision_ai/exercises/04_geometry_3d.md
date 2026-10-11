# Exercise 4: Camera geometry: from pixel to map coordinates

Needed for "go to the object", semantic maps, visual localization.

## Pinhole model
```
u = fx·X/Z + cx        X = (u − cx)·Z / fx
v = fy·Y/Z + cy        Y = (v − cy)·Z / fy        (camera frame: x right, y down, z forward)
```
Get intrinsics from `/camera/camera_info` (`K = [fx 0 cx; 0 fy cy; 0 0 1]`).
```bash
ros2 topic echo /camera/camera_info --once
```

## Getting Z (distance) – three options
1. **Depth camera** (RealSense etc.): sample depth at the bbox centre (median of a small patch; ignore zeros/NaN).
2. **Lidar fusion**: bearing from pixel → read the `/scan` range at that angle (works on a TB3, which has no depth cam). Rotate bearing by the TF `base_link ← camera` offset.
3. **Known object size**: Z ≈ fx · real_width / pixel_width (cheap and surprisingly OK for a known cube/cup).

## Pixel → map frame with TF2 (skeleton)
```python
import tf2_ros, tf2_geometry_msgs
from geometry_msgs.msg import PointStamped
buf = tf2_ros.Buffer(); tf2_ros.TransformListener(buf, node)
p = PointStamped(); p.header.frame_id = "camera_rgb_optical_frame"; p.header.stamp = img_msg.header.stamp
p.point.x, p.point.y, p.point.z = X, Y, Z
p_map = buf.transform(p, "map", timeout=rclpy.duration.Duration(seconds=0.2))
```
Use the **image's timestamp** (not `now()`) so the transform matches where the robot *was*.

## Task
Write `experiments/object_to_map.py`: subscribe to `detections` + `/scan`, compute the object's `(x,y)` in `map`, publish a `visualization_msgs/Marker` and view it in rviz. Then send it to Nav2 with `BasicNavigator.goToPose`, stopping 0.5 m in front. This is the hackathon "wow" demo (Challenges 01 + 03).
