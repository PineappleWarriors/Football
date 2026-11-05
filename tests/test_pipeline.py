"""Synthetic-data checks of the decoder and loader. Not a measure of real-match performance."""
import os
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "evaluation"))

from possession import params as P  # noqa: E402
from possession.decode import emissions, merge_short, viterbi  # noqa: E402
from possession.deadball import dead_evidence  # noqa: E402
from possession.io import load_tracking  # noqa: E402
import possession_metrics as pm  # noqa: E402


def simulate(seed, minutes=20, acc=0.65, p_missing=0.41):
    """Truth: lognormal live spells (~14 s) with dead gaps. Obs: noisy nearest-team distances."""
    rng = np.random.RandomState(seed)
    truth = []
    team = rng.randint(2)
    while len(truth) < minutes * 60 * 5:
        n = int(np.clip(rng.lognormal(np.log(11), 0.6), 3, 80) * 5)
        truth += [team] * n
        if rng.rand() < 0.5:
            truth += [2] * int(rng.uniform(8, 30) * 5)
            team = rng.randint(2)
        else:
            team = 1 - team
    truth = np.array(truth, dtype=np.int8)
    T = len(truth)
    miss = np.zeros(T, bool)                       # bursty ball dropout, ~41%
    t = 0
    while t < T:
        L = int(rng.exponential(25))
        if rng.rand() < p_missing:
            miss[t:t + L] = True
        t += L + 1
    right = rng.rand(T) < acc
    sign = np.where(truth == 0, 1.0, -1.0) * np.where(right, 1.0, -1.0)
    margin = sign * np.abs(rng.normal(3, 3, T))
    dh, da = 10 - margin / 2, 10 + margin / 2
    dead = truth == 2
    feat = {"dh": np.where(miss, np.inf, np.clip(dh, 0.5, None)),
            "da": np.where(miss, np.inf, np.clip(da, 0.5, None)),
            "have": ~miss, "observed": ~miss,
            "oob": dead & (rng.rand(T) < 0.3),
            "ball_speed": np.where(dead, 0.2, 8.0),
            "player_speed": np.where(dead, 0.8, 3.0) + rng.normal(0, 0.3, T)}
    return truth, feat


def baseline_vote(feat, w):
    code = np.where(feat["have"], np.where(feat["dh"] < feat["da"], 0, 1), 2)
    out = np.empty(len(code), np.int8)
    for i in range(len(code)):
        win = code[max(0, i - w):i + w + 1]
        h, a = (win == 0).sum(), (win == 1).sum()
        out[i] = 2 if h + a == 0 else (0 if h >= a else 1)
    return out


def score(truth, pred):
    runs = [(0, len(truth))]
    return pm.spell_scores(truth.astype(np.int8), pred.astype(np.int8), runs)["mean_f1"]


def test_decoder_beats_vote_baseline_on_simulator():
    wins = []
    for seed in range(3):
        truth, feat = simulate(seed)
        pred = merge_short(viterbi(emissions(feat, dead_evidence(feat))))
        wins.append(score(truth, pred) - score(truth, baseline_vote(feat, 10)))
    assert np.mean(wins) > 0.05, wins


def test_missing_ball_is_not_dead():
    truth, feat = simulate(0)
    feat["player_speed"][:] = 3.0                  # players moving, ball gone
    feat["oob"][:] = False
    feat["have"][:], feat["observed"][:] = False, False
    feat["dh"][:], feat["da"][:] = np.inf, np.inf
    s = dead_evidence(feat)
    assert (s < 0.1).all()


def test_loader_roundtrip():
    lines = ["{}:{}:{}\n".format(fid, "0.5,0.5,1.0;N,N,N;0.2,0.4,2.0",
                                 "0.5,0.5,0.0" if fid % 2 else "NaN,NaN,NaN")
             for fid in range(1, 12)]
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
        fh.writelines(lines)
    trk = load_tracking(fh.name, np.array([0, 1, 1]), (100.0, 50.0))
    os.unlink(fh.name)
    assert list(trk["frames"]) == [0, 5, 10]
    assert np.isclose(trk["players"][0, 0, 0], 50.0) and np.isnan(trk["players"][0, 1, 0])


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
