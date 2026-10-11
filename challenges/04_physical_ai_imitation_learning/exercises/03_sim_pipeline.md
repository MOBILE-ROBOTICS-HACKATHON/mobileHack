# Exercise 3: Full imitation-learning pipeline in simulation (TurtleBot3)

Goal: teach the simulated robot to drive around the TB3 world **without hitting walls**, by demonstration only.

**T1: sim** (inside Docker)
```bash
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```
**T2: teleop** (you are the expert)
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
**T3: record**
```bash
cd challenges/04_physical_ai_imitation_learning
python3 src/record_demos.py --out data/demos_run1.npz      # Ctrl-C to save when done
```
Drive laps for ~5–10 min. Smooth, consistent driving: keep ~0.4 m from walls, avoid stopping. Deliberately steer toward a wall and correct a few times.

**Train** (host GPU or container CPU)
```bash
python3 src/train_policy.py --data data/demos_run1.npz --out models/bc_policy.pt
```
**Deploy** (stop teleop first!)
```bash
python3 src/run_policy.py --model models/bc_policy.pt --max-v 0.15
```

## Evaluate properly
- Write `experiments/eval.py`: reset the robot (`ros2 service call /reset_simulation std_srvs/srv/Empty`), run 60 s, count collisions (min lidar range < 0.12) and distance travelled. 10 trials.
- Compare: a) 2 min of demos vs. 10 min; b) with/without recovery demos; c) MLP vs. a 1-D conv on lidar; d) adding the last action as input (does it fix jitter or cause copycat-lag?).

## DAgger on the real pipeline (human-gated)
1. Run the policy; whenever it drifts toward a wall, **take over** with teleop (publish on `cmd_vel`; mux with `twist_mux` or just override manually) and log those corrective segments.
2. Append the new data → retrain → repeat. Typically 2–3 rounds beat 3× more initial demos.

## Known pitfalls
- Policy outputs mean-reverted slow speed (idle samples dominate): `train_policy.py` drops idle samples: check that it's still right for your task.
- Training/inference mismatch: lidar preprocessing is *shared* via import; keep it that way.
- Latency: the sim runs in sim-time; real robot over 5G adds delay: re-test with artificial delay.
- Never run the policy without the safety clamp + hard stop in `run_policy.py`.
