# Exercise 1: Behaviour cloning vs DAgger (no robot)

```bash
source .venv-ml/bin/activate      # or inside docker: python3 (CPU is fine, it's tiny)
python3 challenges/04_physical_ai_imitation_learning/src/toy_bc.py
```
Expected: BC success rises with the number of demos but plateaus below the expert; DAgger closes the gap with *fewer* total demos.

## Experiments (write results in `experiments/LOG.md`)
1. **Data scaling:** demos ∈ {2, 5, 10, 20, 50, 100}. Plot success vs. demos.
2. **Noisy expert:** add `rng.normal(0, 0.02)` to the expert action. How much does BC degrade?
3. **Covariate shift:** during evaluation add random pushes (`p += rng.normal(0, 0.03, 2)` each step). Compare BC vs. DAgger robustness.
4. **Multimodality:** make the expert pass the obstacle on the left *or* the right at random (50/50), keep the MSE net. Plot trajectories: the policy goes straight into the obstacle. Fix it with (a) a mixture density head, or (b) predicting a chunk of 5 future actions and executing it open-loop, or (c) conditioning on a latent "mode".
5. **Architecture:** 1 hidden layer vs. 3; with/without dropout; add observation noise augmentation.
6. **Loss:** MSE vs. L1 (Huber). Which handles multimodality better?

Questions: why can DAgger *not* be run directly on a human expert on real hardware cheaply? (answer: the human must label states the robot visits; use HG-DAgger / intervention-based data instead)
