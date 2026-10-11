# Exercise 3: SLAM (build a map)

```bash
# T1
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py use_sim_time:=true
# T2 – slam_toolbox (online async = the standard choice)
ros2 launch slam_toolbox online_async_launch.py use_sim_time:=true
# T3 – rviz (Fixed Frame = map; add Map /map, LaserScan, TF)
rviz2
# T4 – drive slowly around the whole world
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
Alternative: `ros2 launch turtlebot3_cartographer cartographer.launch.py use_sim_time:=true`.

## Save the map
```bash
mkdir -p challenges/01_autonomous_navigation/maps
ros2 run nav2_map_server map_saver_cli -f challenges/01_autonomous_navigation/maps/tb3_world
```
Produces `tb3_world.pgm` (image) + `tb3_world.yaml` (resolution, origin).

## Questions
1. Drive fast / spin quickly: what happens to the map? (scan matching fails → duplicated walls)
2. Where does `map → odom` come from now? `ros2 run tf2_ros tf2_echo map odom`.
3. Open the .pgm: what do white / black / gray mean? What's `occupied_thresh` in the yaml?
4. Try a long featureless corridor (build one in Gazebo): what breaks? Why? (this is the "feature-poor" hint in the brief)

## Real-robot tips
- Drive 0.1–0.2 m/s, rotate slowly, close loops (return to start) so the graph corrects.
- Save the map early and often. Save a serialized pose-graph too: slam_toolbox service `/slam_toolbox/serialize_map`.
