"""Stopgap v2: baseline_raw + tags + broadcast-stillness (aligned algorithmically).

    python -m possession.make_stopgap2 [--out evaluation/results/stopgap_v2.csv]
"""
import argparse
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "starter")]
os.chdir(ROOT)

import games  # noqa: E402
import load_smart_tagging  # noqa: E402
import pandas as pd  # noqa: E402
from baseline import team_of_each_track  # noqa: E402
from possession.broadcast_align import build_source_map, find_lags  # noqa: E402
from possession.broadcast_features import broadcast_speed, still_on_tactical  # noqa: E402
from possession.from_baseline_raw import run  # noqa: E402
from possession.io import load_tracking  # noqa: E402,F401
from baseline import nearest_player_labels  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="evaluation/results/stopgap_v2.csv")
    ap.add_argument("--no-broadcast", action="store_true")
    args = ap.parse_args()
    g = games.GAME
    n = games.source_frames("tactical", g)
    raw = "evaluation/results/baseline_raw.csv"
    still = None
    if not args.no_broadcast:
        pb = games.asset_paths(g, source="broadcast")
        team = team_of_each_track(pb["atd_meta"])
        pitch = games.GAMES[g]["pitch"]
        b = nearest_player_labels(pb["atd_raw"], team, games.source_frames("broadcast", g), pitch)
        lab = pd.read_csv(raw)["label"].values
        t = np.where(lab == "H", 0, np.where(lab == "A", 1, -1)).astype(np.int8)
        lags = find_lags(b, t)
        src = build_source_map(b, t, lags)
        med, vis = broadcast_speed(pb["atd_raw"], team, pitch)
        still = still_on_tactical(med, vis, src, n // 5 + 2)
        print("lags", lags, "| still-known samples", int(still[0].sum()))
    labels = run(raw, load_smart_tagging.load(g), games.half_video_blocks(g), n, still=still)
    with open(args.out, "w") as fh:
        fh.write("frame,label\n")
        fh.writelines("{},{}\n".format(i, l) for i, l in enumerate(labels))
    for h, lo, hi in games.half_video_blocks(g):
        seg = labels[lo:hi + 1]
        ch = np.flatnonzero(seg[1:] != seg[:-1]) + 1
        st, en = np.r_[0, ch], np.r_[ch, len(seg)]
        live = [(y - x) / 25 for x, y in zip(st, en) if seg[x] in "HA"]
        print("half", h, {k: int((seg == k).sum()) for k in "HAD"}, "live spells", len(live),
              "mean %.1fs" % np.mean(live))
