# Challenge 02: Multi-Robot Collaboration (BetterTogether)

> Brief: a coordination framework so multiple robots (drones, AGVs, mixed fleets) collaborate in real time:
> exchange mission-critical info, avoid collisions, adapt to changing objectives, do tasks no single robot could.

**Hardware:** 20× Crazyflie (via `crazyswarm2`), several TurtleBots/ROSbots/Robomasters. Coordination is mostly **software + networking**, so it is very simulable.

## Mental model
```
shared state (who is where / who does what)  ←→  decentralised or centralised coordinator
      │                                                │
 per-robot namespace  /robotN/{pose,cmd_vel,...}    task allocation (auction / Hungarian)
      │                                                │
 local safety layer (collision avoidance) ◄────────── formation / path planning
```
## Study order (≈6 h)
1. **ROS 2 namespaces, remaps, per-robot launch** (`ros2 launch` with `PushRosNamespace`) · `ROS_DOMAIN_ID` vs namespaces · DDS discovery on Wi-Fi/5G (use CycloneDDS + a discovery server or unicast peer lists if multicast is blocked).
2. `src/turtlesim_swarm.py`: formation + rendezvous + collision avoidance, decentralised. Modify it (exercises below).
3. **Task allocation**: greedy nearest-task vs. Hungarian (`scipy.optimize.linear_sum_assignment`) vs. auction (CBBA concept).
4. **Collision avoidance**: potential fields (in the script) → velocity obstacles / ORCA (RVO2 lib) → control barrier functions (concept only).
5. **Multi-robot Nav2**: namespaced robots in Gazebo (`turtlebot3_multi_robot` community package; allow 1 h for config pain) or one Nav2 stack per robot.
6. **Crazyflie swarms**: `crazyswarm2` docs: `crazyflies.yaml`, trajectory/`goTo` services, Lighthouse/Mocap positioning. Practice in its simulation backends before the hackathon.

## Exercises (use `src/turtlesim_swarm.py`)
1. Run both modes; plot inter-robot minimum distance over time (record `/t*/pose`).
2. **Leader-follower:** t0 follows a keyboard teleop; others keep relative offsets in the leader's frame.
3. **Task allocation:** spawn M random "targets" (markers) mid-run; assign robots with Hungarian each time a target appears; compare total travelled distance vs. greedy.
4. **Failure injection:** kill one turtle mid-mission; the others must re-allocate (heartbeat topic + timeout).
5. **Communication limits:** each robot only sees neighbours within radius R (or messages delayed/dropped 20%). Does the formation still converge?
6. **Mixed fleet:** treat 2 turtles as "drones" (fast) and 2 as "AGVs" (slow) with a shared task list; assign by capability.

## Hackathon strategy
- Pick a **mission story**: warehouse (AGVs ferry items, drones inventory), search-and-rescue (drones scout, AGVs go to the found target), light-show formation.
- Use a **shared world model topic** (`/fleet/state` JSON) + a **central dashboard** (rviz/web) → judges see coordination.
- Network is a feature: the venue has native 5G. Measure latency/packet loss, show robustness.
- Simulate first, hardware second; keep the same code (only topic names differ).

## Packages
`ros-humble-turtlesim` (installed), `scipy` (installed), `crazyswarm2` (build from source, see its docs; `cflib` is installed), `rvo2` optional (`pip install pyrvo2`).
