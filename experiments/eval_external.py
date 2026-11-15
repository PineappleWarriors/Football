"""Validate/tune the possession model on EXTERNAL games (Metrica public samples) with the repo scorer.

    python experiments/eval_external.py            # default params, all games, vs baselines
Tuning is allowed here because the data is from other games (RULES.md). Never on the BAR-ATH GT.
"""
import os
import sys
import warnings

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "evaluation"), os.path.join(ROOT, "starter")]

import possession_metrics as pm  # noqa: E402
from possession import external_metrica as em  # noqa: E402
from possession import params as P  # noqa: E402
from possession.features import build_features  # noqa: E402
from possession.decode import emissions, merge_short, viterbi  # noqa: E402
from possession.deadball import dead_evidence  # noqa: E402
from possession import ml  # noqa: E402
from possession.model import decode_period  # noqa: E402

FOLDER = os.path.join(ROOT, "external_data", "metrica")
GAMES = ("Sample_Game_1", "Sample_Game_2")
STEP = P.STEP


def prepare(game):
    """-> dict(trk5 per period, gt codes, ...) with metres and per-player speeds at 5 Hz."""
    raw = em.load_tracking(FOLDER, game)
    gt = em.event_labels(FOLDER, game, len(raw["frame"]))
    L, W = em.PITCH
    pl = raw["players"] * np.array([L, W])
    ball = raw["ball"] * np.array([L, W])
    # per-player speed (m/s) from +-2 frame difference at 25 Hz
    sp = np.full(pl.shape[:2], np.nan)
    d = np.linalg.norm(pl[4:] - pl[:-4], axis=2)
    sp[2:-2] = d / (4 / 25.0)
    idx = np.arange(0, len(gt), STEP)
    return {"frame": idx, "players": pl[idx], "pspeed": sp[idx], "ball": ball[idx],
            "team": raw["team"], "period": raw["period"][idx], "gt": gt, "n": len(gt)}


def predict(data, decode_fn):
    """Per-period decode_fn(trk, features)->path -> 25 Hz codes (3 = X outside graded spans)."""
    out = np.full(data["n"], 3, dtype=np.int8)
    for p in np.unique(data["period"]):
        m = data["period"] == p
        trk = {k: data[k][m] for k in ("players", "pspeed", "ball")}
        trk["team"] = data["team"]
        path = decode_fn(trk)
        fr = data["frame"][m]
        lo, hi = fr[0], min(fr[-1] + STEP, data["n"])
        pos = np.clip(np.rint(np.arange(lo, hi) / float(STEP)).astype(int)
                      - int(round(fr[0] / float(STEP))), 0, len(path) - 1)
        out[lo:hi] = path[pos]
    return out


def model_decode(dead_model=None):
    return lambda trk: decode_period(trk, em.PITCH, dead_model)


def baseline_decode(window_samples):
    def fn(trk):
        feat = build_features(trk, em.PITCH)
        code = np.where(feat["have"], np.where(feat["dh"] < feat["da"], 0, 1), 2)
        if window_samples == 0:
            return code.astype(np.int8)
        h = np.concatenate(([0], np.cumsum(code == 0)))
        a = np.concatenate(([0], np.cumsum(code == 1)))
        i = np.arange(len(code))
        lo, hi = np.maximum(0, i - window_samples), np.minimum(len(code), i + window_samples + 1)
        hh, aa = h[hi] - h[lo], a[hi] - a[lo]
        return np.where(hh + aa == 0, 2, np.where(hh >= aa, 0, 1)).astype(np.int8)
    return fn


def score(data, pred):
    gt = data["gt"]
    runs = pm.valid_runs(gt)
    cm3 = pm.scored_confusion(pm.confusion(gt, pred))
    sp = pm.spell_scores(gt, pm.fill_abstentions(pred, runs), runs)
    ps = pm.possession_stats(pm.fill_abstentions(pred, runs), runs)
    return {"spellF1": sp["mean_f1"], "macroF1": pm.macro_f1(cm3), "n_pred": sp["n_pred"],
            "n_gt": sp["n_gt"]}


def fit_dead_on(game):
    from experiments_train import collect
    X, y = collect(game)
    k = y < 3
    return ml.fit_logistic(X[k], (y[k] == 2).astype(float), l2=1.0)


if __name__ == "__main__":
    warnings.simplefilter("ignore", RuntimeWarning)
    sys.path.insert(0, os.path.join(ROOT, "experiments"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("experiments_train",
                                                  os.path.join(ROOT, "experiments", "train_dead_model.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["experiments_train"] = mod
    spec.loader.exec_module(mod)
    datas = {g: prepare(g) for g in GAMES}
    cross = {g: fit_dead_on([o for o in GAMES if o != g][0]) for g in GAMES}   # trained on the OTHER game
    systems = [("model, rule dead-ball", lambda g: model_decode(None)),
               ("model, learned dead (x-game)", lambda g: model_decode(cross[g]))] + [
        ("baseline smooth +-%ds" % (w // 5), (lambda w: lambda g: baseline_decode(w))(w))
        for w in (0, 5, 10, 25)]
    print("%-30s" % "system" + "".join("%30s" % g for g in GAMES))
    for name, mk in systems:
        row = ""
        for g in GAMES:
            r = score(datas[g], predict(datas[g], mk(g)))
            row += "  spell %.3f macro %.3f n=%3d/%3d" % (r["spellF1"], r["macroF1"], r["n_pred"], r["n_gt"])
        print("%-30s%s" % (name, row))
