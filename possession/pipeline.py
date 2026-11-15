"""End-to-end: ATD (+ optional Smart Tagging) -> frame,label CSV.

    python -m possession.pipeline --out evaluation/results/viterbi_v1.csv [--use-tags]
"""
import argparse
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "starter"))

from games import GAME, GAMES, half_video_blocks, require, source_frames  # noqa: E402
from possession import params as P  # noqa: E402
from possession.deadball import restart_anchors  # noqa: E402
from possession.model import decode_period, load_dead_model  # noqa: E402

LETTERS = np.array(["H", "A", "D"])


def to_frames(samples_frames, path, lo, hi, out):
    """Write sample labels into the 25 fps output for frames [lo, hi]."""
    f = np.arange(lo, hi + 1)
    pos = np.searchsorted(samples_frames, f)
    pos = np.clip(pos, 1, len(samples_frames) - 1)
    left_closer = (f - samples_frames[pos - 1]) <= (samples_frames[pos] - f)
    pos = np.where(left_closer, pos - 1, pos)
    out[lo:hi + 1] = LETTERS[path[pos]]


def run(game=GAME, data_dir=None, use_tags=False):
    from baseline import team_of_each_track
    from possession.io import load_tracking
    meta, raw = require(["atd_meta", "atd_raw"], game, data_dir)
    pitch = GAMES[game]["pitch"]
    trk = load_tracking(raw, team_of_each_track(meta), pitch)
    frames = trk["frames"]
    dead_model = load_dead_model()
    events = []
    if use_tags:
        import load_smart_tagging
        events = load_smart_tagging.load(game, data_dir)
    n = source_frames("tactical", game)
    labels = np.full(n, "X", dtype="<U1")
    for _, lo, hi in half_video_blocks(game):
        m = (frames >= lo) & (frames <= hi)
        free = restart_anchors(events, len(frames))[m] if use_tags else None
        half = {k: trk[k][m] for k in ("players", "pspeed", "ball")}
        half["team"] = trk["team"]
        path = decode_period(half, pitch, dead_model, free)
        to_frames(frames[m], path, lo, hi, labels)
    return labels


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--use-tags", action="store_true",
                    help="free H/A/D switches at set-piece boundaries (tag semantics unverified)")
    args = ap.parse_args()
    lab = run(use_tags=args.use_tags)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as fh:
        fh.write("frame,label\n")
        fh.writelines("{},{}\n".format(i, l) for i, l in enumerate(lab))
    print("wrote", args.out, {k: int((lab == k).sum()) for k in "HADX"})
