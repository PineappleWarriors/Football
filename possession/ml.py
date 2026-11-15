"""Small learned emission models (numpy logistic regression), trained on EXTERNAL games only.

team model: P(home in possession | live) from ball-free team-shape cues.
dead model: P(dead) from ball-gap structure, last-ball position and player stillness.
"""
import json
import warnings

import numpy as np

from possession import params as P


def _smooth(x, k):
    """Centred moving average along axis 0 ignoring NaN (k samples)."""
    ker = np.ones(k)
    v = np.nan_to_num(x, nan=0.0)
    c = ~np.isnan(x)
    if x.ndim == 1:
        num = np.convolve(v, ker, "same")
        den = np.convolve(c.astype(float), ker, "same")
    else:
        num = np.stack([np.convolve(v[:, i], ker, "same") for i in range(x.shape[1])], 1)
        den = np.stack([np.convolve(c[:, i].astype(float), ker, "same") for i in range(x.shape[1])], 1)
    return num / np.maximum(den, 1e-9)


def attack_dirs(players, team):
    """(+1/-1 for team 0, same for team 1): +1 = attacks towards +x. Team with the smaller mean
    'leftmost player' x defends the left goal."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        mins = [np.nanmean(np.nanmin(players[:, team == t, 0], axis=1)) for t in (0, 1)]
    left = int(np.argmin(mins))                      # this team defends x=0 -> attacks +x
    d = [0, 0]
    d[left], d[1 - left] = 1, -1
    return d


def team_shape_features(trk, pitch):
    """[T, 6] home-minus-away shape cues (attack-axis oriented), NaN-free."""
    L = pitch[0]
    pl, team = trk["players"], trk["team"]
    dirs = attack_dirs(pl, team)
    T = len(pl)
    feats = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        per = []
        for t in (0, 1):
            x = pl[:, team == t, 0] * dirs[t] / L                 # attack axis, own->opp goal
            y = pl[:, team == t, 1]
            cent = np.nanmean(x, axis=1)
            srt = np.sort(np.where(np.isnan(x), np.inf, x), axis=1)
            nv = np.sum(~np.isnan(x), axis=1).clip(1)
            low = np.array([srt[i, :4].mean() if np.isfinite(srt[i, :4]).all() else np.nan
                            for i in range(T)])                   # deepest 4 = defensive line
            high = np.array([np.sort(x[i][~np.isnan(x[i])])[-3:].mean() if nv[i] >= 3 else np.nan
                             for i in range(T)])                  # most advanced 3
            width = np.nanstd(y, axis=1) / pitch[1]
            vel = np.gradient(_smooth(cent, 5)) * P.HZ            # attack-axis centroid speed
            per.append((cent, low, high, width, _smooth(vel, 10)))
    for k in range(5):
        feats.append(per[0][k] - per[1][k])
    feats.append(_smooth(feats[0], 25))                          # slower trend of centroid diff
    X = np.stack(feats, 1)
    return np.nan_to_num(_smooth(X, 5), nan=0.0)


def dead_features(trk, feat, pitch):
    """[T, k] ball-gap + stillness + last-ball-position cues for the dead-ball model."""
    L, W = pitch
    seen = feat["observed"]
    T = len(seen)
    gap_len = np.zeros(T)
    since = np.zeros(T)
    i = 0
    while i < T:
        if not seen[i]:
            j = i
            while j < T and not seen[j]:
                j += 1
            gap_len[i:j] = j - i
            since[i:j] = np.arange(1, j - i + 1)
            i = j
        else:
            i += 1
    ball = trk["ball"]
    last = np.full((T, 2), np.nan)
    cur = np.array([np.nan, np.nan])
    for t in range(T):
        if seen[t]:
            cur = ball[t]
        last[t] = cur
    edge = np.minimum.reduce([last[:, 0], L - last[:, 0], last[:, 1], W - last[:, 1]])
    edge = np.nan_to_num(edge, nan=30.0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        mean_sp = np.nanmean(trk["pspeed"], axis=1)
        still_frac = np.nanmean(trk["pspeed"] < 1.0, axis=1)
    sp_s = _smooth(np.nan_to_num(mean_sp, nan=3.0), 25)
    still_s = _smooth(np.nan_to_num(still_frac, nan=0.0), 25)
    bs = np.nan_to_num(feat["ball_speed"], nan=0.0)
    X = np.stack([
        np.log1p(gap_len) , (~seen).astype(float), np.log1p(since), np.exp(-edge / 5.0),
        np.nan_to_num(feat["player_speed"].clip(0, 8), nan=3.0), sp_s, still_s,
        np.minimum(bs, 30) / 10.0, feat["oob"].astype(float),
        (~seen) * np.exp(-edge / 5.0), (~seen) * sp_s, (~seen) * still_s], 1)
    return X


def fit_logistic(X, y, l2=1.0, iters=30, w=None):
    n, k = X.shape
    mu, sd = X.mean(0), X.std(0) + 1e-6
    Z = np.c_[np.ones(n), (X - mu) / sd]
    w_ = np.ones(n) if w is None else w
    beta = np.zeros(k + 1)
    R = np.eye(k + 1) * l2
    R[0, 0] = 0
    for _ in range(iters):
        p = 1 / (1 + np.exp(-Z @ beta))
        g = Z.T @ (w_ * (p - y)) + R @ beta
        H = (Z * (w_ * p * (1 - p))[:, None]).T @ Z + R
        step = np.linalg.solve(H, g)
        beta -= step
        if np.abs(step).max() < 1e-6:
            break
    return {"mu": mu.tolist(), "sd": sd.tolist(), "beta": beta.tolist()}


def predict_logit(model, X):
    Z = (X - np.array(model["mu"])) / np.array(model["sd"])
    return np.array(model["beta"])[0] + Z @ np.array(model["beta"])[1:]


def save(models, path):
    with open(path, "w") as fh:
        json.dump(models, fh)


def load(path):
    with open(path) as fh:
        return json.load(fh)
