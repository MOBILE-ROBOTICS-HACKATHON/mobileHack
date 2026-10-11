# Exercise 2: Concepts reading list (prioritised; skim, don't deep-read)

| Priority | Paper / resource | Take-away |
|---|---|---|
| ★★★ | ALOHA / **ACT**: Zhao et al., 2023 (arXiv 2304.13705) | action chunking + CVAE; ~50 demos suffice for fine tasks |
| ★★★ | **Diffusion Policy**: Chi et al., 2023 (arXiv 2303.04137) | handles multimodal demos; receding-horizon control |
| ★★ | A Reduction of Imitation Learning to No-Regret Online Learning (**DAgger**), Ross 2011 | why BC compounds errors (error ∝ T²) |
| ★★ | LeRobot docs + `lerobot/pusht` dataset card (huggingface.co/docs/lerobot) | dataset format, training CLI |
| ★ | **π0 / OpenVLA / SmolVLA** blogs | what a VLA is; what is realistic to run locally |
| ★ | Mobile ALOHA | demo collection tips for mobile manipulation |

## Dataset anatomy (LeRobotDataset)
Per-frame: `observation.image` / `observation.state`, `action`, `timestamp`, `episode_index`, `frame_index`.
Stored as parquet + mp4 videos; `fps` global. Episodes are variable length. Your `record_demos.py` `.npz` is the minimal version of the same idea. Think about how you'd convert it (a nice exercise: write `npz_to_lerobot.py`).

## Design vocabulary
- **Observation space:** raw images vs. low-dim state; use 1-2 cameras, low-res (96–224 px).
- **Action space:** absolute vs. delta, joint vs. end-effector, `cmd_vel` for AGVs. Normalise (mean/std).
- **Horizon / chunk size:** k=10–100 steps at 10–50 Hz.
- **Temporal ensembling:** average overlapping chunk predictions for smoothness (ACT).
- **Evaluation:** success rate over N≥20 trials with randomised starts; report confidence intervals.

## Questions to answer in your notes
1. Why does ACT predict chunks instead of one action?
2. Why does a diffusion head fix the multimodal averaging problem?
3. What breaks first when you deploy a policy at a different control rate than demos?
4. How many demos would you collect for (a) lidar corridor driving, (b) pick-and-place of one block?
