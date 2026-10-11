# Exercise 6: AprilTags (cheap, robust visual localization)

Use cases: dock alignment, landmark relocalization in feature-poor spaces, marking goals ("tag 3 = charging station").

```bash
ros2 pkg prefix apriltag_ros     # installed in the Docker image
```
1. Print tags (family `tag36h11`): https://github.com/AprilRobotics/apriltag-imgs (ID 0–10, ~10 cm square for tests).
2. **Calibrate the camera** (or use `camera_info` from the sim/driver); tag pose accuracy depends on it.
3. Run `apriltag_ros` on `/image_raw` + `/camera_info` (see the package README for the params YAML: set `tag.size`).
4. It publishes TF `camera → tag_<id>`. Look it up with `tf2_echo`.
5. **Task:** place a tag at a known map pose; when seen, compute `map → base_link` and publish it as `/initialpose` to snap AMCL back to the truth (Challenge 01 differentiator).

Alternative without ROS packages: `pip install pupil-apriltags` + OpenCV `solvePnP`.
