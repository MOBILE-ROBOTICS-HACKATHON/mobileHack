#!/usr/bin/env python3
"""Step 2: TRAIN a behaviour-cloning policy (lidar bins -> v, w) from recorded demos.
Pure PyTorch, no ROS needed: run on the host venv (GPU) or in the container (CPU, it's tiny).

    python3 train_policy.py --data ../data/demos_run1.npz --out ../models/bc_policy.pt

Tips: drop idle samples (cmd=0) so the policy doesn't learn to stand still; hold out the last 20%
as validation (do NOT shuffle across time before splitting: consecutive samples are near-duplicates).
"""
import argparse
import os
import numpy as np
import torch
import torch.nn as nn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", nargs="+", required=True)
    ap.add_argument("--out", default="models/bc_policy.pt")
    ap.add_argument("--epochs", type=int, default=200)
    a = ap.parse_args()

    X = np.concatenate([np.load(f)["X"] for f in a.data])
    Y = np.concatenate([np.load(f)["Y"] for f in a.data])
    keep = (np.abs(Y).sum(1) > 1e-3)
    print(f"{len(X)} samples, {keep.sum()} non-idle kept")
    X, Y = X[keep], Y[keep]

    n_val = int(0.2 * len(X))
    Xtr, Ytr, Xva, Yva = X[:-n_val], Y[:-n_val], X[-n_val:], Y[-n_val:]
    y_mean, y_std = Ytr.mean(0), Ytr.std(0) + 1e-6
    f = lambda arr, dtype=torch.float32: torch.tensor(arr, dtype=dtype)
    Xtr_t, Ytr_t = f(Xtr), f((Ytr - y_mean) / y_std)
    Xva_t, Yva_t = f(Xva), f((Yva - y_mean) / y_std)

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    net = nn.Sequential(nn.Linear(X.shape[1], 128), nn.ReLU(), nn.Dropout(0.1),
                        nn.Linear(128, 128), nn.ReLU(), nn.Linear(128, 2)).to(dev)
    opt = torch.optim.AdamW(net.parameters(), 1e-3, weight_decay=1e-4)
    best = 1e9
    for ep in range(a.epochs):
        net.train()
        perm = torch.randperm(len(Xtr_t))
        for i in range(0, len(perm), 128):
            idx = perm[i:i + 128]
            xb = Xtr_t[idx].to(dev)
            xb = xb + 0.01 * torch.randn_like(xb)                 # light noise augmentation
            loss = nn.functional.mse_loss(net(xb), Ytr_t[idx].to(dev))
            opt.zero_grad(); loss.backward(); opt.step()
        net.eval()
        with torch.no_grad():
            val = nn.functional.mse_loss(net(Xva_t.to(dev)), Yva_t.to(dev)).item()
        if val < best:
            best = val
            os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
            torch.save({"state": {k: v.cpu() for k, v in net.state_dict().items()},
                        "in_dim": X.shape[1], "y_mean": y_mean, "y_std": y_std}, a.out)
        if ep % 20 == 0:
            print(f"epoch {ep:3d} val_mse {val:.4f} (best {best:.4f})")
    print(f"saved best model -> {a.out}")


if __name__ == "__main__":
    main()
