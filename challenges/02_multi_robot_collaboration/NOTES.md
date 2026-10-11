# NOTES: Challenge 02 · Multi-Robot Collaboration (BetterTogether)

Priority for you: ★ (secondary). Read this so you can join or pivot if your team picks it. Plan: `ROADMAP.md`.

## 1. The challenge in plain words
Several robots (drones, wheeled robots, mixed fleets) must **work together in real time**: share mission-critical information, avoid colliding with each other, adapt when objectives change, and complete tasks that a single robot could not. You build the **coordination framework**, not a single robot's skill.

Hardware: **20 Crazyflie** nano-drones (via `crazyswarm2`), TurtleBots, ROSbot XL, Robomasters, Jackal, PX4 drones.

## 2. Concepts
**Architectures**
- *Centralised*: one coordinator computes everything and commands all robots. Simple, optimal, but a single point of failure and bandwidth-heavy.
- *Decentralised*: each robot decides from its own state + messages from neighbours. Robust, scalable, harder to get right (consensus, convergence).
- *Hybrid*: central task assignment, local collision avoidance (most practical).

**Fleet communication**: namespaced topics `/robot1/pose`, `/robot1/cmd_vel`; shared topics for state (`/fleet/state`) and tasks (`/fleet/tasks`). DDS discovery means all robots on the same `ROS_DOMAIN_ID` see everything: you may want *namespaces* to separate them.

**Task allocation**: assign tasks to robots minimising cost. *Greedy nearest* (fast, suboptimal); *Hungarian* (`scipy.optimize.linear_sum_assignment`, optimal one-to-one); *auction/CBBA* (decentralised: robots bid). Re-allocate when tasks appear or robots fail (heartbeat + timeout).

**Formation control**: consensus on relative offsets; leader-follower; virtual structure. Used for drone shows and convoying.

**Collision avoidance**: potential fields (repulsion), velocity obstacles/ORCA (reciprocal), control barrier functions (safety filters), priority/right-of-way rules, time-space reservation.

**Multi-robot SLAM/Nav**: each robot runs its own Nav2 in its namespace; share maps or use a common prior map.

**Drone specifics**: Crazyflies localize with the **Lighthouse** system or optical flow; `crazyswarm2` provides `goTo`, takeoff/land services and trajectory upload. Battery ≈ 5-7 min; always have a land-now behaviour.

## 3. Packages
| Package | Role |
|---|---|
| `turtlesim` | zero-hardware multi-agent playground (used by `turtlesim_swarm.py`) |
| `scipy` | Hungarian assignment, optimisation, KD-trees |
| `cflib` (pip, installed) | Crazyflie Python library |
| `crazyswarm2` (not installed) | ROS 2 stack for Crazyflie swarms; build from source (https://imrclab.github.io/crazyswarm2) |
| `turtlebot3_gazebo` | spawn several robots with namespaces (needs a multi-robot launch; community `turtlebot3_multi_robot`) |
| `navigation2` | one stack per robot |
| `rosbridge_suite` | web dashboard for the fleet |
| `pyrvo2` (on demand) | ORCA collision avoidance |

## 4. The code
`src/turtlesim_swarm.py`: N turtles, each runs a decentralised controller using only others' poses: **formation** (rotating circle) or **rendezvous**, with **repulsion** collision avoidance. Run: terminal A `ros2 run turtlesim turtlesim_node`; terminal B `python3 challenges/02_multi_robot_collaboration/src/turtlesim_swarm.py --n 4 --mode formation`.

## 5. What to DO (≈6 h)
1. Run the swarm script; read it until you understand each line.
2. Do the six experiments in `ROADMAP.md` (leader-follower, Hungarian task allocation, failure injection, limited comms, heterogeneous fleet).
3. Read `crazyswarm2` docs (config `crazyflies.yaml`, services, simulation modes).
4. Try 2 namespaced TurtleBots in Gazebo only if you have spare time (setup is fiddly).

## 6. Preparation for the venue
- Ask: network type (5G? multicast?), robot namespaces, how many robots per team, positioning system for drones, safety net/cage rules.
- Design the **mission story** (warehouse, search-and-rescue, light show) and a dashboard so judges see coordination.
- Always give each robot a **heartbeat** and a safe-stop on message loss.

## 7. Pitfalls
| Problem | Fix |
|---|---|
| Robots see everybody's topics | namespaces, unique domain ID |
| Messages drop on Wi-Fi/5G | RELIABLE QoS for commands; sequence numbers; tolerate loss |
| Oscillation in formation | lower gains; add damping; limit speed |
| Deadlocks in narrow passages | priorities / waiting rules |
| Drone crashes | geofence, velocity limits, takeoff checks, land-on-lost-link |

## 8. Glossary
ORCA · Hungarian algorithm · consensus · CBBA · formation · heartbeat · namespace · rendezvous · swarm.

## 9. Checklist
- [ ] I ran `turtlesim_swarm.py` in both modes.
- [ ] I implemented one extension (Hungarian allocation or failure recovery).
- [ ] I know how namespaces and domain IDs separate robots.
- [ ] I can sketch a centralised vs decentralised design and their trade-offs.
