"""3-state Viterbi (H, A, D) with switch penalties = a duration prior, then short-spell merging."""
import numpy as np

from possession import params as P

H, A, D = 0, 1, 2


def emissions(feat, s_dead):
    """Log-likelihood matrix [T,3]. Team evidence only when the ball is near someone."""
    dh, da = feat["dh"], feat["da"]
    near = np.minimum(dh, da) < P.CONTROL_RADIUS_M
    diff = np.where(near, da, 0.0) - np.where(near, dh, 0.0)
    margin = np.clip(diff, -P.MARGIN_CLIP_M, P.MARGIN_CLIP_M)
    w = np.where(feat["observed"], 1.0, P.BRIDGED_WEIGHT)
    z = P.TEAM_SLOPE * margin * w
    log_ph = -np.logaddexp(0.0, -z)
    log_pa = -np.logaddexp(0.0, z)
    e = np.empty((len(dh), 3))
    e[:, H] = np.log1p(-s_dead) + log_ph
    e[:, A] = np.log1p(-s_dead) + log_pa
    e[:, D] = np.log(s_dead)
    return e


def viterbi(e, lam_team=P.LAMBDA_TEAM, lam_dead=P.LAMBDA_DEAD, free=None):
    T = len(e)
    if T == 0:
        return np.zeros(0, dtype=np.int8)
    cost = np.array([[0, lam_team, lam_dead], [lam_team, 0, lam_dead], [lam_dead, lam_dead, 0]],
                    dtype=float)
    score = e[0].copy()
    back = np.zeros((T, 3), dtype=np.int8)
    for t in range(1, T):
        c = np.zeros((3, 3)) if (free is not None and free[t]) else cost
        cand = score[:, None] - c                      # [from, to]
        back[t] = np.argmax(cand, axis=0)
        score = cand[back[t], np.arange(3)] + e[t]
    path = np.empty(T, dtype=np.int8)
    path[-1] = int(np.argmax(score))
    for t in range(T - 1, 0, -1):
        path[t - 1] = back[t, path[t]]
    return path


def _runs(path):
    cuts = np.flatnonzero(np.diff(path)) + 1
    starts = np.concatenate(([0], cuts))
    stops = np.concatenate((cuts, [len(path)]))
    return list(zip(starts.tolist(), stops.tolist()))


def merge_short(path, min_len=int(round(P.MIN_SPELL_S * P.HZ))):
    """Relabel live runs shorter than min_len to the longer neighbouring run's label."""
    path = path.copy()
    for _ in range(len(path)):
        runs = _runs(path)
        changed = False
        for k, (a, b) in enumerate(runs):
            if path[a] != D and b - a < min_len and len(runs) > 1:
                left = runs[k - 1] if k > 0 else None
                right = runs[k + 1] if k + 1 < len(runs) else None
                best = max([r for r in (left, right) if r], key=lambda r: r[1] - r[0])
                path[a:b] = path[best[0]]
                changed = True
                break
        if not changed:
            break
    return path
