"""Player-stillness cue from the broadcast tracking, mapped onto the tactical timeline."""
import warnings

import numpy as np

from possession import params as P
from possession.io import load_tracking

MIN_VISIBLE = 8     # need this many tracked players in view to say anything about 'standing'


def broadcast_speed(raw_path, team_of_track, pitch):
    """-> (median player speed m/s [Nb], visible players [Nb]) on the broadcast frame index."""
    trk = load_tracking(raw_path, team_of_track, pitch, step=1)
    sp = trk["pspeed"]
    vis = np.sum(~np.isnan(sp), axis=1)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        med = np.nanmedian(sp, axis=1)
    out_med = np.full(int(trk["frames"].max()) + 1, np.nan)
    out_vis = np.zeros(len(out_med), dtype=int)
    out_med[trk["frames"]] = med
    out_vis[trk["frames"]] = vis
    return out_med, out_vis


def still_on_tactical(med, vis, src, n_samples, step=P.STEP):
    """Per 5 Hz tactical sample: (known[bool], still[bool]) from the aligned broadcast frames."""
    known = np.zeros(n_samples, bool)
    still = np.zeros(n_samples, bool)
    for i in range(n_samples):
        f = i * step
        if f >= len(src) or src[f] < 0 or src[f] >= len(med):
            continue
        g = src[f]
        if vis[g] >= MIN_VISIBLE and not np.isnan(med[g]):
            known[i] = True
            still[i] = med[g] < P.STILL_PLAYER_MPS
    return known, still
