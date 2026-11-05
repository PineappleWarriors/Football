"""Fallback when no tracking is available: Smart Tagging (+ Viterbi spell decode) only.

Evidence per 5 Hz sample (constants fixed a priori, not fitted):
  * attacking-phase tags (Team = X)        -> X in possession
  * defending-phase tags (Team = X)        -> the other team in possession
  * set piece with a Team tag (not N/A)    -> that team is the restarting (next-possessing) team
  * set-piece windows                      -> weak dead-ball evidence
Windows are ~15-35 s long and only approximately placed, so each vote is weak; the Viterbi
switching penalty turns many overlapping weak votes into whole spells.
"""
import numpy as np

from possession import params as P
from possession.decode import H, A, D, merge_short, viterbi

ATTACK = {"PROGRESSION", "BUILD UP", "BALL IN FINAL THIRD", "BALL IN THE BOX", "CREATING CHANCES",
          "PLAYERS IN THE BOX", "LONG BALL", "ATTACKING TRANSITION"}
DEFEND = {"DEFENDING IN MIDDLE THIRD", "DEFENDING IN ATTACKING THIRD",
          "DEFENDING IN DEFENSIVE THIRD", "DEFENSIVE TRANSITION"}
TEAM_SIGN = {"Barcelona": 1.0, "Atletic Club": -1.0}   # +1 = home
VOTE_WEIGHT = 0.5          # nats per tag vote
SETPIECE_DEAD = 0.30       # P(dead) inside a set-piece window (weak)


def tag_series(events, n_samples, step=P.STEP):
    vote = np.zeros(n_samples)
    dead = np.full(n_samples, P.S_BASE)
    for e in events:
        a = max(0, int(round(e["start_frame"] / float(step))))
        b = min(n_samples, int(round(e["end_frame"] / float(step))))
        sign = TEAM_SIGN.get(e["tags"].get("Team"))
        code = e["code"].upper()
        if code in ATTACK and sign is not None:
            vote[a:b] += sign
        elif code in DEFEND and sign is not None:
            vote[a:b] -= sign
        elif code == "SET PIECES":
            dead[a:b] = np.maximum(dead[a:b], SETPIECE_DEAD)
            if sign is not None:
                vote[a:b] += sign
    return vote, dead


def decode(vote, dead):
    z = VOTE_WEIGHT * vote
    e = np.empty((len(vote), 3))
    e[:, H] = np.log1p(-dead) - np.logaddexp(0.0, -z)
    e[:, A] = np.log1p(-dead) - np.logaddexp(0.0, z)
    e[:, D] = np.log(dead)
    return merge_short(viterbi(e))


def run(events, blocks, n_frames, step=P.STEP):
    n_samples = n_frames // step + 2
    vote, dead = tag_series(events, n_samples, step)
    letters = np.array(["H", "A", "D"])
    labels = np.full(n_frames, "X", dtype="<U1")
    for _, lo, hi in blocks:
        i0, i1 = int(round(lo / float(step))), int(round(hi / float(step))) + 1
        path = decode(vote[i0:i1], dead[i0:i1])
        f = np.arange(lo, hi + 1)
        idx = np.clip(np.rint(f / float(step)).astype(int) - i0, 0, len(path) - 1)
        labels[lo:hi + 1] = letters[path[idx]]
    return labels
