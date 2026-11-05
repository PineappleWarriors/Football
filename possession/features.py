"""Per-sample (5 Hz) features from tracking arrays. Missing ball stays missing evidence."""
import warnings

import numpy as np

from possession import params as P


def _bridge(ball, max_gap):
    """Linearly interpolate NaN gaps of <= max_gap samples that have a ball on both sides."""
    out = ball.copy()
    seen = ~np.isnan(ball[:, 0])
    idx = np.flatnonzero(seen)
    for a, b in zip(idx[:-1], idx[1:]):
        if 1 < b - a <= max_gap + 1:
            for k in range(2):
                out[a + 1:b, k] = np.interp(np.arange(a + 1, b), [a, b], [ball[a, k], ball[b, k]])
    return out, seen


def team_distances(ball, players, team):
    """Distance (m) from the ball to the nearest tracked player of each team (inf if none)."""
    d = np.linalg.norm(players - ball[:, None, :], axis=2)         # [N,S]
    d = np.where(np.isnan(d), np.inf, d)
    dh = np.min(np.where(team[None, :] == 0, d, np.inf), axis=1)
    da = np.min(np.where(team[None, :] == 1, d, np.inf), axis=1)
    return dh, da


def build_features(trk, pitch):
    length, width = pitch
    ball_b, seen = _bridge(trk["ball"], int(round(P.BRIDGE_S * P.HZ)))
    have = ~np.isnan(ball_b[:, 0])
    dh, da = team_distances(np.nan_to_num(ball_b, nan=1e6), trk["players"], trk["team"])
    dh[~have], da[~have] = np.inf, np.inf
    speed = np.full(len(ball_b), np.nan)
    speed[1:] = np.linalg.norm(np.diff(ball_b, axis=0), axis=1) * P.HZ
    bx, by = ball_b[:, 0], ball_b[:, 1]
    m = P.OOB_MARGIN_M
    oob = have & ((bx < -m) | (bx > length + m) | (by < -m) | (by > width + m))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)   # all-NaN rows -> NaN -> 99 below
        med = np.nanmedian(trk["pspeed"], axis=1)
    return {"dh": dh, "da": da, "have": have, "observed": seen, "oob": oob,
            "ball_speed": speed, "player_speed": np.nan_to_num(med, nan=99.0)}
