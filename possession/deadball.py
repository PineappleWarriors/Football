"""Dead-ball evidence s = P(dead | cues). Missing ball is NOT dead: it only counts with stillness."""
import numpy as np

from possession import params as P


def dead_evidence(feat):
    still = feat["player_speed"] < P.STILL_PLAYER_MPS
    slow = ~feat["have"] | (np.nan_to_num(feat["ball_speed"], nan=0.0) < P.SLOW_BALL_MPS)
    s = np.full(len(still), P.S_BASE)
    s[still] = P.S_STILL_ONLY
    s[still & slow] = P.S_STILL_NOBALL_OR_SLOW
    s[feat["oob"]] = P.S_OOB
    return s


def restart_anchors(events, n, step=P.STEP):
    """Boolean[n]: samples where a set piece starts/ends, so a switch is free there.

    Tag semantics (does the interval cover the dead time?) are unverified; off by default.
    """
    free = np.zeros(n, dtype=bool)
    for ev in events:
        if "SET PIECE" in ev["code"].upper():
            for f in (ev["start_frame"], ev["end_frame"]):
                i = int(round(f / float(step)))
                if 0 <= i < n:
                    free[i] = True
    return free
