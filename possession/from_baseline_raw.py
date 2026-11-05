"""STOPGAP when the tactical ATD .txt is unavailable: fuse the organisers' published per-frame
nearest-player output (evaluation/results/baseline_raw.csv; D == ball untracked, H/A == team of the
nearest player) with Smart Tagging votes, then run the same Viterbi spell decode.

Disclosure: baseline_raw.csv is automatic output of the organisers' baseline on the tactical
tracking, shipped in the repo; it contains no ground-truth information. The final submission should
be regenerated from the raw ATD with possession.pipeline so it is reproducible from the data bundle.
Constants are fixed a priori.
"""
import numpy as np
import pandas as pd

from possession import params as P
from possession.decode import H, A, D, merge_short, viterbi
from possession.tags_only import tag_series

NEAREST_WEIGHT = 0.6          # nats per sample bin; nearest-player is right ~65-70% of the time
TAG_WEIGHT = 0.2              # tags are 15-35 s windows: a weak prior, capped at one vote
LONG_MISSING_S = 5.0          # ball untracked this long -> weak dead-ball evidence only
LONG_MISSING_DEAD = 0.25


def nearest_series(csv_path, n_frames, step=P.STEP):
    codes = pd.read_csv(csv_path)["label"].values[:n_frames]
    n = n_frames // step + 2
    vote = np.zeros(n)
    seen = np.zeros(n, bool)
    h = np.add.reduceat((codes == "H").astype(float), np.arange(0, n_frames, step))
    a = np.add.reduceat((codes == "A").astype(float), np.arange(0, n_frames, step))
    m = len(h)
    tot = h + a
    vote[:m] = np.where(tot > 0, (h - a) / np.maximum(tot, 1), 0.0)
    seen[:m] = tot > 0
    return vote, seen


def long_missing(seen, min_len):
    out = np.zeros(len(seen), bool)
    i = 0
    while i < len(seen):
        if not seen[i]:
            j = i
            while j < len(seen) and not seen[j]:
                j += 1
            if j - i >= min_len:
                out[i:j] = True
            i = j
        else:
            i += 1
    return out


# Geometric duration prior: switch cost = ln(expected run length in samples). Possessions ~14 s
# (CHALLENGE.md), dead-ball runs ~20 s. Derived, not fitted.
LAM_TEAM = float(np.log(14 * P.HZ))
LAM_DEAD = float(np.log(20 * P.HZ))


def run(csv_path, events, blocks, n_frames, step=P.STEP, lam_team=LAM_TEAM, lam_dead=LAM_DEAD):
    nv, seen = nearest_series(csv_path, n_frames, step)
    tv, dead = tag_series(events, len(nv), step)
    dead = np.where(long_missing(seen, int(LONG_MISSING_S * P.HZ)),
                    np.maximum(dead, LONG_MISSING_DEAD), dead)
    z = NEAREST_WEIGHT * nv + TAG_WEIGHT * np.clip(tv, -1.0, 1.0)
    e = np.empty((len(nv), 3))
    e[:, H] = np.log1p(-dead) - np.logaddexp(0.0, -z)
    e[:, A] = np.log1p(-dead) - np.logaddexp(0.0, z)
    e[:, D] = np.log(dead)
    letters = np.array(["H", "A", "D"])
    labels = np.full(n_frames, "X", dtype="<U1")
    for _, lo, hi in blocks:
        i0, i1 = int(round(lo / float(step))), int(round(hi / float(step))) + 1
        path = merge_short(viterbi(e[i0:i1], lam_team, lam_dead))
        f = np.arange(lo, hi + 1)
        labels[lo:hi + 1] = letters[path[np.clip(np.rint(f / float(step)).astype(int) - i0, 0, len(path) - 1)]]
    return labels
