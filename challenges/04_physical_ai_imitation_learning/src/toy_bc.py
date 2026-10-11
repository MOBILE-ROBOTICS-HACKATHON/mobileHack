#!/usr/bin/env python3
"""Imitation learning in 100 lines, no robot, no ROS: behaviour cloning vs DAgger.

Task: a 2D point must reach a goal while avoiding a circular obstacle.
Expert = hand-written potential-field controller. Learner = MLP trained to copy the expert
from (goal - pos, obstacle - pos). Compare:
  * BC     : train once on expert demonstrations.
  * DAgger : roll out the *learner*, ask the expert what it would have done in the states the
             learner visits, aggregate, retrain. Fixes compounding error (covariate shift).

    python3 toy_bc.py              # runs on CPU in ~1 min, prints success rates
Experiments: fewer demos, noise in the expert, bigger/smaller network, add a 2nd obstacle,
             multimodal expert (go left OR right of the obstacle) -> watch MSE-BC average the modes.
"""
import numpy as np
import torch
import torch.nn as nn

rng = np.random.default_rng(0)
torch.manual_seed(0)
OBS_R, GOAL_TOL, MAX_STEP, T = 0.18, 0.06, 0.06, 80


def sample_task():
    start = rng.uniform(-1, 1, 2)
    goal = rng.uniform(-1, 1, 2)
    while np.linalg.norm(goal - start) < 0.8:
        goal = rng.uniform(-1, 1, 2)
    mid = (start + goal) / 2 + rng.normal(0, 0.08, 2)          # obstacle near the straight line
    return start, goal, mid


def features(p, g, o):
    return np.concatenate([g - p, o - p]).astype(np.float32)


def expert(p, g, o):
    to_g = g - p
    a = to_g / (np.linalg.norm(to_g) + 1e-6)
    d = p - o
    dist = np.linalg.norm(d)
    if dist < 0.45:                                              # repulsion + tangential swirl
        rep = d / (dist + 1e-6) * (0.45 - dist) * 4
        tang = np.array([-d[1], d[0]]) / (dist + 1e-6) * 0.8
        a = a + rep + tang
    a = a / (np.linalg.norm(a) + 1e-6)
    return a * min(MAX_STEP, np.linalg.norm(to_g))


def rollout(policy=None, beta=0.0, record=False):
    """policy: callable(features)->action. beta: prob. of executing the expert action instead."""
    p, g, o = sample_task()
    X, Y, ok, collided = [], [], False, False
    for _ in range(T):
        f = features(p, g, o)
        a_exp = expert(p, g, o)
        if record:
            X.append(f); Y.append(a_exp)
        a = a_exp if (policy is None or rng.random() < beta) else policy(f)
        n = np.linalg.norm(a)
        if n > MAX_STEP:
            a = a / n * MAX_STEP
        p = p + a
        if np.linalg.norm(p - o) < OBS_R:
            collided = True
        if np.linalg.norm(p - g) < GOAL_TOL:
            ok = True
            break
    return X, Y, ok and not collided


def make_net():
    return nn.Sequential(nn.Linear(4, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU(), nn.Linear(128, 2))


def train(net, X, Y, epochs=300):
    X, Y = torch.tensor(np.array(X)), torch.tensor(np.array(Y), dtype=torch.float32)
    opt = torch.optim.Adam(net.parameters(), 1e-3)
    for _ in range(epochs):
        perm = torch.randperm(len(X))
        for i in range(0, len(X), 256):
            idx = perm[i:i + 256]
            loss = nn.functional.mse_loss(net(X[idx]), Y[idx] * 10)       # scale actions up
            opt.zero_grad(); loss.backward(); opt.step()
    return net


def policy_of(net):
    def pi(f):
        with torch.no_grad():
            return net(torch.tensor(f)).numpy() / 10
    return pi


def success_rate(policy, n=100):
    return float(np.mean([rollout(policy)[2] for _ in range(n)]))


def collect_expert(n):
    X, Y = [], []
    for _ in range(n):
        x, y, _ = rollout(None, record=True)
        X += x; Y += y
    return X, Y


if __name__ == "__main__":
    print(f"expert success rate : {success_rate(None):.2f}")
    for n_demos in (5, 20, 80):
        X, Y = collect_expert(n_demos)
        net = train(make_net(), X, Y)
        print(f"BC     ({n_demos:3d} demos, {len(X):5d} samples): success {success_rate(policy_of(net)):.2f}")

    # DAgger: start with 5 expert demos, then 5 iterations of 10 learner-driven episodes each
    X, Y = collect_expert(5)
    net = train(make_net(), X, Y)
    for it in range(5):
        for _ in range(10):
            x, y, _ = rollout(policy_of(net), beta=0.0, record=True)   # learner drives, expert labels
            X += x; Y += y
        net = train(make_net(), X, Y)
        print(f"DAgger iter {it + 1} ({len(X):5d} samples): success {success_rate(policy_of(net)):.2f}")
