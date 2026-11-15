"""Train the dead-ball logistic model on EXTERNAL games only and save coefficients.

    python experiments/train_dead_model.py [game ...]      (default: all external games)
"""
import json
import os
import sys
import warnings

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "experiments"), os.path.join(ROOT, "evaluation")]
warnings.simplefilter("ignore", RuntimeWarning)

import eval_external as E  # noqa: E402
from possession import external_metrica as em, ml  # noqa: E402
from possession.features import build_features  # noqa: E402
from possession.model import DEAD_MODEL_PATH  # noqa: E402


def collect(game):
    d = E.prepare(game)
    gt5 = d["gt"][d["frame"]]
    X, y = [], []
    for p in np.unique(d["period"]):
        m = d["period"] == p
        trk = {k: d[k][m] for k in ("players", "pspeed", "ball")}
        trk["team"] = d["team"]
        f = build_features(trk, em.PITCH)
        X.append(ml.dead_features(trk, f, em.PITCH))
        y.append(gt5[m])
    return np.concatenate(X), np.concatenate(y)


if __name__ == "__main__":
    games = sys.argv[1:] or list(E.GAMES)
    parts = [collect(g) for g in games]
    X = np.concatenate([p[0] for p in parts])
    y = np.concatenate([p[1] for p in parts])
    k = y < 3
    model = ml.fit_logistic(X[k], (y[k] == 2).astype(float), l2=1.0)
    model["provenance"] = {"trained_on": games, "source": "Metrica sample-data (public), labels "
                           "derived from its event data", "n_samples": int(k.sum())}
    os.makedirs(os.path.dirname(DEAD_MODEL_PATH), exist_ok=True)
    with open(DEAD_MODEL_PATH, "w") as fh:
        json.dump(model, fh)
    print("saved", DEAD_MODEL_PATH, "trained on", games, "n=", int(k.sum()))
