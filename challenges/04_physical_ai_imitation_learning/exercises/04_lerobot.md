# Exercise 4: LeRobot (Hugging Face)

Installed on the **host** by `scripts/setup_host_ml.sh` (`.venv-ml`, Python 3.12). CLI names and flags have changed across LeRobot versions, so **always check `--help` and the docs for the installed version**:

```bash
source .venv-ml/bin/activate
pip show lerobot | head -3
python -c "import lerobot, sys; print(lerobot.__file__)"
lerobot-train --help | head -50        # (older versions: python -m lerobot.scripts.train --help)
lerobot-eval  --help | head -50
lerobot-record --help | head -50       # for real robots with teleop; needs supported hardware
```
Docs: https://huggingface.co/docs/lerobot

## Path 1: sim only (no hardware): PushT
```bash
uv pip install "lerobot[pusht]"          # gym-pusht simulator
# Evaluate a pretrained Diffusion Policy checkpoint from the hub (needs internet; do this at home)
lerobot-eval --policy.path=lerobot/diffusion_pusht --env.type=pusht --eval.n_episodes=10 --eval.batch_size=10
```
Then train your own ACT/Diffusion model on the `lerobot/pusht` dataset for a short run (a few thousand steps fit a 4 GB GPU with a small batch). Copy the exact flags from the current docs "Training" section:
```bash
lerobot-train --dataset.repo_id=lerobot/pusht --policy.type=act --output_dir=outputs/train/act_pusht --steps=2000 --batch_size=8
```
(if a flag is rejected, the `--help` output is the source of truth).

## Path 2: your own robot data
Convert `data/*.npz` to a `LeRobotDataset` (write `experiments/npz_to_lerobot.py`; see `LeRobotDataset.create(...)` + `add_frame(...)` + `save_episode()` in the docs), then train with the same CLI pointing at the local dataset (`--dataset.repo_id=local/my_dataset --dataset.root=...`).

## 4 GB VRAM survival
- small batch (4–16), `--policy.use_amp=true` if available, lower image resolution, fewer workers.
- If OOM: train on the Jetson AGX Orin at the venue or CPU for smoke tests; use Colab/Kaggle at home for bigger runs.

## What to understand by the end
- Where the dataset lives on disk, and its schema.
- Which config key sets chunk size (`n_action_steps`/`chunk_size`) and observation steps.
- How eval rolls out the policy and computes success.
