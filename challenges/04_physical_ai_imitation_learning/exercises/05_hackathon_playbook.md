# Exercise 5: Hackathon playbook for this track

## Before Saturday (decide)
- Primary plan: **AGV imitation learning** (lidar/camera → `cmd_vel`). It needs no special hardware and matches your sim pipeline.
- Stretch: whatever humanoid/arm is offered: confirm interfaces with mentors at 10:00.
- Prepare a **dataset schema** and **recording script** you can adapt in 10 min (topics are the only thing that changes).

## Timeline on the day (Sat)
| Time | Do |
|---|---|
| 10:45–12:30 | Pick platform; bring up teleop + sensor topics; adapt `record_demos.py` (topic names, scaling). Record a first 2-min dataset. |
| 12:30–15:00 | Train a first model (should take minutes). Deploy at **low speed** in a taped-off area. Write down failure modes. |
| 15:00–19:00 | Round 2: collect demos targeting failures (DAgger-style). Build the evaluation script (N trials, metrics). |
| Evening | Freeze the best model. Record videos of success + failure. Draft slides. |

## Sun
- 09:15–14:00: improve (augmentation, more data, chunking), final eval run (≥10 trials), save numbers.
- 14:00–16:00: demo rehearsal + backup video.
- 16:00 final preparation → 17:00 present.

## Pitch structure (5 min)
1. Problem: "programming robot skills is slow; show it instead".
2. Live demo or video: policy driving; teleop baseline for comparison.
3. Numbers: demos used (count + minutes), collisions/trial, success rate vs. hand-coded.
4. What we learned: data quality > model size; DAgger rounds gained X%.
5. Next steps.

## Safety (non-negotiable)
Velocity caps · watchdog · e-stop within reach · a human spotter · test in an empty area · never deploy a new model at full speed.
