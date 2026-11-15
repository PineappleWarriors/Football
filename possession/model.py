"""One decode path for a period (half): used by the real pipeline and the external evaluation."""
import os

import numpy as np

from possession import ml
from possession import params as P
from possession.deadball import dead_evidence
from possession.decode import emissions, merge_short, viterbi
from possession.features import build_features

DEAD_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models",
                               "dead_ext_v1.json")
FLOOR = 0.02


def load_dead_model(path=DEAD_MODEL_PATH):
    return ml.load(path) if os.path.exists(path) else None


def dead_probability(trk, feat, pitch, model):
    if model is None:
        return dead_evidence(feat)
    p = 1.0 / (1.0 + np.exp(-ml.predict_logit(model, ml.dead_features(trk, feat, pitch))))
    return np.clip(p, FLOOR, 1.0 - FLOOR)


def decode_period(trk, pitch, dead_model=None, free=None):
    """trk: dict(players[T,S,2] m, pspeed[T,S], ball[T,2] m, team[S]) at 5 Hz -> path of 0/1/2."""
    feat = build_features(trk, pitch)
    s = dead_probability(trk, feat, pitch, dead_model)
    return merge_short(viterbi(emissions(feat, s), free=free))
