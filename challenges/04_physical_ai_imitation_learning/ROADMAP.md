# Challenge 04: Physical AI & Imitation Learning

> Brief: teach a robot a new skill by *showing* rather than programming. Imitation learning, teleoperation demonstrations,
> or foundation-model-driven behaviours on the **humanoid and AGV platforms**. Open-ended: surprise us.

You know ML: the new part is **data collection on hardware, covariate shift, and safe deployment**.
The honest truth: in 2 days, real-robot IL succeeds only with a **tiny, well-scoped task, consistent demos, and a safety wrapper.**

## Mental model
```
teleoperate (keyboard / joystick / VR / leader arm)
   → record (observation, action) pairs @ fixed rate, with timestamps
   → train policy π(a | o)     BC (MLP) → ACT (transformer, action chunks) → Diffusion Policy
   → deploy in closed loop + safety layer
   → look at failures → collect more data *where it failed* (DAgger-style) → retrain
```
Key concepts (read in this order, ~1 h):
1. **Behaviour cloning** = supervised learning on demonstrations; breaks from **compounding error / covariate shift**.
2. **DAgger**: learner drives, expert relabels visited states.
3. **Multimodality**: two valid demos (go left or right) → MSE regression averages them → crash into the middle. Fixes: action chunking (ACT), diffusion policies, mixture density, discrete tokens (VQ-BeT).
4. **Action chunking (ACT)**: predict the next k actions at once → smoother, fewer compounding errors. Paper: *Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware* (Zhao et al. 2023).
5. **Diffusion Policy** (Chi et al. 2023): denoise an action sequence; strong on multimodal data, slower.
6. **VLA / foundation-model-driven behaviour**: pretrained vision-language-action models (OpenVLA, π0, SmolVLA in LeRobot). Inference is heavy: only viable with GPU/Jetson, and fine-tuning is out of scope for a hackathon: *use it zero-shot or skip*.

## Study order (≈9 h)
| # | Time | What | Where |
|---|---|---|---|
| 1 | 1.5h | BC vs DAgger from scratch (no ROS) | `src/toy_bc.py` + `exercises/01_toy_bc.md` |
| 2 | 1h | Read ACT + Diffusion Policy summaries; dataset format | `exercises/02_concepts_reading.md` |
| 3 | 3h | **Full sim pipeline**: record teleop → train → deploy on TB3 | `src/record_demos.py`, `train_policy.py`, `run_policy.py`, `exercises/03_sim_pipeline.md` |
| 4 | 2h | LeRobot: install, run pretrained policy on PushT sim, understand the dataset/training loop | `exercises/04_lerobot.md` |
| 5 | 1.5h | Design your hackathon task + safety + evaluation protocol | `exercises/05_hackathon_playbook.md` |

## Which tasks are realistic at the hackathon?
| Platform | Realistic IL task | Obs → action |
|---|---|---|
| AGV (TurtleBot, ROSbot, Jackal) | Corridor/obstacle-course driving; "follow the tape"; docking | lidar or camera → (v, ω) |
| AGV + camera | Visual navigation to a coloured target | image → (v, ω) |
| Humanoid / arm (if offered) | Pick-and-place of one object at a fixed location | camera + joint state → joint targets |
| Any | **Language-conditioned** or **foundation-model-driven**: VLM picks the subgoal, simple controller executes | text + image → subgoal |

A strong, low-risk pitch: *"We compare hand-coded Nav2 vs. a policy learned from 10 min of human demos on the same course (collisions, time, smoothness) and show DAgger improvement."* Metrics + honesty impress juries more than a lucky run.

## Hardware-day checklist
- [ ] Ask mentors on arrival: which platform, which control interface (`cmd_vel`? joint trajectory?), is a leader arm/VR teleop available, how many GPUs?
- [ ] Define observation + action spaces **first** (the one design decision you can't change cheaply).
- [ ] Fix the control rate (10 Hz typical) in both record and deploy.
- [ ] Use identical preprocessing code for train and deploy (see `lidar_features` shared import).
- [ ] 30+ demos for a simple task; vary start poses; include **recovery** demos.
- [ ] Safety: velocity caps, watchdog, hard e-stop override independent of the policy.
- [ ] Always train on the host GPU (`.venv-ml`); copy only the `.pt` into the container/robot.
- [ ] Save every dataset + model + a video of every deployment run (evidence for the pitch).

## Folder layout
```
src/          toy_bc.py, record_demos.py, train_policy.py, run_policy.py
exercises/    guides
data/         recorded demos (.npz)  -> git-ignored if big
models/       trained policies
experiments/  YOUR notebook + LOG.md
```
