# NOTES: Challenge 04 · Physical AI & Imitation Learning

Read top to bottom for the full picture. Hands-on steps in `exercises/`, plan in `ROADMAP.md`.

## 1. The challenge in plain words
**Teach a robot a skill by showing it, not by writing rules.** A human demonstrates (teleoperation); you record observations and actions; you train a neural network to reproduce the behaviour; the robot then performs it alone. Platforms mentioned: **humanoid and AGV**. "Open-ended: surprise us" = judges reward creativity + a working result + honest evaluation.

Realistic scope in a weekend: **one narrow task**, ~30-100 consistent demos, a small policy, safe deployment. Don't promise generalist robot intelligence.

## 2. Concepts you must understand
**Imitation learning (IL)**: learn a policy π(action | observation) from expert demos.
- **Behaviour cloning (BC)** = supervised regression/classification on (obs, action). Simple, fast, strong baseline.
- **Compounding error / covariate shift**: small mistakes put the robot in states the expert never showed; errors grow ~quadratically with horizon. Fixes: more diverse data (include *recoveries*), noise augmentation, **DAgger**, action chunking.
- **DAgger**: let the learner drive, ask the expert to label the states it visits, add to dataset, retrain. Human-gated variants on hardware: intervene when it fails and record the correction.
- **Multimodality**: if demos go left *or* right around an obstacle, an MSE regressor outputs the **average** (straight into the obstacle). Solutions: mixture density networks, **action chunking (ACT)**, **diffusion policies**, discretised actions (VQ-BeT), conditioning.
- **ACT (Action Chunking with Transformers)**: predicts a chunk of the next k actions at once from images + state; smoother; ~50 demos for fine tasks (ALOHA).
- **Diffusion Policy**: denoising diffusion on action sequences; handles multimodality; slower inference.
- **VLA (Vision-Language-Action)** models (OpenVLA, π0, SmolVLA): large pretrained policies conditioned on language; heavy; usable zero-shot/few-shot only with a good GPU; fine-tuning is beyond a hackathon.
- **Reinforcement learning** is a different route (needs rewards + huge sim time): out of scope for 2 days.

**Data pipeline**: choose observation (lidar bins, image, joint state), action (`cmd_vel` or joint targets), control rate (10 Hz), record with timestamps, normalise, split train/val **by episode/time** (not random frames), train, evaluate in closed loop (open-loop loss ≠ task success!).

**Evaluation**: success rate over N≥10-20 trials, collisions, time, smoothness; compare to a baseline (hand-coded or Nav2). Report failures honestly.

**Safety for learned policies**: velocity clamps, hard obstacle stop, watchdog, e-stop, first test at low speed, human spotter.

## 3. Packages: what each does
| Package | Where | Role |
|---|---|---|
| `torch` | host venv (CUDA) + container (CPU) | the learning framework |
| `lerobot` | host venv | Hugging Face robotics library: datasets (`LeRobotDataset`), policies (ACT, Diffusion, VQ-BeT, SmolVLA), training/eval/record CLIs, robot drivers |
| `gymnasium` | host venv | RL/IL environments API (toy envs, PushT sim via `lerobot[pusht]`) |
| `numpy`, `matplotlib`, `tqdm` | both | data handling, plots, progress |
| `teleop_twist_keyboard` / `teleop_twist_joy` | container | you are the expert: generate `cmd_vel` demos |
| `rosbag2` (`ros2 bag`) | container | alternative recording format (replayable, richer) |
| `ultralytics` | both | if observations are images → pretrained features (optional) |
| `uv` | host | fast Python package manager used by `setup_host_ml.sh` |

## 4. The code in `src/`
| File | Teaches | Where it runs |
|---|---|---|
| `toy_bc.py` | BC vs DAgger from scratch in a 2D reaching task; data scaling; covariate shift | host venv or container (no ROS needed) |
| `record_demos.py` | ROS node recording `(lidar bins, cmd_vel)` at 10 Hz to `.npz` | container (sim running + teleop) |
| `train_policy.py` | MLP behaviour cloning, normalisation, validation split, best-checkpoint | host venv (GPU) or container (CPU) |
| `run_policy.py` | deploy: `/scan` → network → `/cmd_vel` with clamps + hard stop | container |
Pipeline in one picture:
`teleop keys → /cmd_vel` + `/scan` → **record_demos** → `data/*.npz` → **train_policy** (venv) → `models/*.pt` → **run_policy** → robot drives itself.

Measured on this machine: `toy_bc.py` BC success 23% (5 demos) → 48% (20) → 95% (80); DAgger ~94% with ~2000 samples.

## 5. What you should DO, in order (≈9 h)
1. Read the concepts above and `exercises/02_concepts_reading.md` (ACT + Diffusion Policy abstracts/figures; 1 h).
2. `exercises/01_toy_bc.md` (1.5 h): run `toy_bc.py`, plot data scaling, break it (multimodal expert), fix it.
3. `exercises/03_sim_pipeline.md` (3 h): record 5-10 min of teleop in the TB3 sim → train → deploy → evaluate → DAgger round.
4. `exercises/04_lerobot.md` (2 h): `lerobot` install check, PushT eval, short ACT/diffusion run; read the dataset format.
5. `exercises/05_hackathon_playbook.md` (30 min): timeline and pitch.
6. Log metrics in `experiments/LOG.md`.

## 6. How to prepare for the real robot
- Ask on arrival: which robot, control interface (`cmd_vel`? joint trajectories?), sensors, is a leader arm / VR teleop available, GPU access.
- **Define observation and action spaces before recording**; they're expensive to change.
- Use the *same preprocessing code* for record, train and deploy (`lidar_features` is imported by `run_policy.py` for this reason).
- Collect demos with variety: different start poses, plus recovery manoeuvres. Aim for 30+ short episodes or 10+ minutes continuous.
- Keep the policy small first (MLP). Only go to ACT/Diffusion if images/manipulation require it and you have GPU time.
- Train on the host GPU in the venv; copy only the `.pt` file.
- Record video of every deployment for the pitch.

## 7. Idea menu
| Idea | Notes |
|---|---|
| AGV imitates a human driving a course using lidar | fits in hours; baseline vs. Nav2 comparison |
| AGV visual navigation (image → v, ω) | needs more data; use a small CNN + augmentation |
| Imitation + DAgger comparison with metrics | strong "science" pitch |
| Foundation-model-driven behaviour: VLM chooses a subgoal, classical controller executes | no training needed; good if time is short |
| Humanoid/arm pick-and-place (if hardware is offered) | high risk; use ACT in LeRobot and only a single fixed task |

## 8. Common failures and fixes
| Symptom | Fix |
|---|---|
| Policy just stands still / creeps | idle samples dominate: filter them; check action normalisation |
| Great val loss, poor driving | covariate shift: add recovery data + DAgger; open-loop loss is misleading |
| Jerky | smooth demos; predict chunks; low-pass filter outputs |
| Works in sim, not on robot | different latency, rate, sensor noise: record real data; add noise augmentation |
| Different behaviour each run | seed, but mostly inconsistent demos: be consistent |
| CUDA OOM (4 GB) | small batch/model, AMP, lower image resolution, use Jetson/Colab |
| LeRobot CLI flag errors | versions differ: `lerobot-train --help` is the truth |

## 9. Glossary
action chunking · behaviour cloning · covariate shift · DAgger · diffusion policy · episode · multimodal · observation · policy · teleoperation · VLA · LeRobotDataset.

## 10. Readiness checklist
- [ ] I can explain covariate shift and why DAgger helps.
- [ ] I ran `toy_bc.py` and understand each result line.
- [ ] I completed record → train → deploy in the TB3 sim and measured it.
- [ ] `.venv-ml` works: `torch.cuda.is_available()` is `True`.
- [ ] I checked `lerobot-train --help` and ran at least one LeRobot example.
- [ ] I have a safety wrapper and an evaluation protocol ready.
- [ ] I can pitch my idea in 3 minutes with numbers.

## 11. Resources
LeRobot docs https://huggingface.co/docs/lerobot · ACT paper (Zhao et al. 2023) · Diffusion Policy (Chi et al. 2023) · DAgger (Ross et al. 2011) · "A survey of imitation learning" (Hussein et al.) · Mobile ALOHA project page.
