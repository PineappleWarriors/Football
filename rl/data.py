"""Download the external games, build per-period feature tensors (cached)."""
import os
import pickle
import sys
import time
import urllib.request

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for extra in (ROOT, os.path.join(ROOT, "experiments"), os.path.join(ROOT, "evaluation")):
    if extra not in sys.path:
        sys.path.insert(0, extra)

import eval_external as E  # noqa: E402
from possession import external_metrica as em, ml  # noqa: E402
from possession import params as P  # noqa: E402
from possession.features import build_features  # noqa: E402

BASE = "https://raw.githubusercontent.com/metrica-sports/sample-data/master/data"
FOLDER = os.path.join(ROOT, "external_data", "metrica")
CACHE = os.path.join(ROOT, "external_data", "cache")
GAMES = ("Sample_Game_1", "Sample_Game_2")
FILES = ("{g}_RawTrackingData_Home_Team.csv", "{g}_RawTrackingData_Away_Team.csv",
         "{g}_RawEventsData.csv")
N_FEATURES = None   # set after first build


def _download(url, dest, retries=6):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                total = int(r.headers.get("Content-Length", 0))
                tmp = dest + ".part"
                with open(tmp, "wb") as fh:
                    while True:
                        chunk = r.read(1 << 20)
                        if not chunk:
                            break
                        fh.write(chunk)
                if total and os.path.getsize(tmp) != total:
                    raise IOError("partial download")
                os.replace(tmp, dest)
                return
        except Exception as exc:  # noqa: BLE001
            print("  download retry {} ({}): {}".format(attempt + 1, os.path.basename(dest), exc))
            time.sleep(min(60, 3 * 2 ** attempt))
    raise RuntimeError("could not download " + url)


def ensure_data():
    for g in GAMES:
        for pattern in FILES:
            name = pattern.format(g=g)
            dest = os.path.join(FOLDER, g, name)
            if not os.path.exists(dest):
                print("downloading", name)
                _download("{}/{}/{}".format(BASE, g, name), dest)


def sample_features(feat):
    dh = np.clip(np.where(np.isfinite(feat["dh"]), feat["dh"], 40.0), 0, 40) / 10.0
    da = np.clip(np.where(np.isfinite(feat["da"]), feat["da"], 40.0), 0, 40) / 10.0
    margin = np.clip(da - dh, -0.8, 0.8)
    dmin = np.minimum(dh, da) * 10.0
    ctrl = 1.0 / (1.0 + np.exp(np.clip((dmin - P.CONTROL_RADIUS_M) / P.CONTROL_SOFT_M, -50, 50)))
    bs = np.nan_to_num(feat["ball_speed"], nan=0.0)
    return np.stack([dh, da, margin, ctrl, (bs < P.SPEED_GATE_MPS).astype(float),
                     feat["observed"].astype(float), feat["have"].astype(float),
                     np.minimum(bs, 30) / 10.0, feat["oob"].astype(float),
                     np.clip(feat["player_speed"], 0, 8) / 8.0], 1)


def build_game(game):
    """-> {'periods': {p: {'X','y','frame'}}, 'gt25', 'n', 'raw': prepared dict}"""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, game + "_feat_v1.pkl")
    d = E.prepare(game)
    if os.path.exists(path):
        with open(path, "rb") as fh:
            periods = pickle.load(fh)
    else:
        periods = {}
        for p in np.unique(d["period"]):
            m = d["period"] == p
            trk = {k: d[k][m] for k in ("players", "pspeed", "ball")}
            trk["team"] = d["team"]
            feat = build_features(trk, em.PITCH)
            X = np.concatenate([sample_features(feat), ml.dead_features(trk, feat, em.PITCH),
                                ml.team_shape_features(trk, em.PITCH)], axis=1).astype(np.float32)
            periods[int(p)] = {"X": X, "y": d["gt"][d["frame"][m]].astype(np.int64),
                               "frame": d["frame"][m]}
        with open(path, "wb") as fh:
            pickle.dump(periods, fh)
    return {"periods": periods, "gt25": d["gt"], "n": d["n"], "raw": d}
