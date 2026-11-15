"""Metrica public sample games (CSV format) -> tracking arrays + event-derived possession labels.

Used ONLY as external data to validate/tune the model (RULES.md: other games are fine). Source:
https://github.com/metrica-sports/sample-data (README asks to acknowledge the source).

Event-derived labels approximate the challenge definition: possession persists through loose
balls/duels and changes only on a controlled action by the other team; dead ball runs from the
event that ends play (ball out, foul, goal) to the next restart.
"""
import numpy as np
import pandas as pd

PITCH = (105.0, 68.0)
OWN = {"PASS", "SHOT", "RECOVERY"}          # team of these events controls the ball
DEAD_START = {"BALL OUT", "FAULT RECEIVED"}


def load_tracking(folder, game):
    base = "{}/{}/{}_RawTrackingData_{}_Team.csv"
    out = {}
    for side in ("Home", "Away"):
        df = pd.read_csv(base.format(folder, game, game, side), header=None, skiprows=3,
                         low_memory=False)
        out[side] = df
    home, away = out["Home"], out["Away"]
    n_h = (home.shape[1] - 5) // 2
    n_a = (away.shape[1] - 5) // 2
    frame = home[1].astype(int).values
    xy_h = home.iloc[:, 3:3 + 2 * n_h].values.astype(float).reshape(len(home), n_h, 2)
    xy_a = away.iloc[:, 3:3 + 2 * n_a].values.astype(float).reshape(len(away), n_a, 2)
    ball = home.iloc[:, 3 + 2 * n_h:5 + 2 * n_h].values.astype(float)
    players = np.concatenate([xy_h, xy_a], axis=1)
    team = np.array([0] * n_h + [1] * n_a)
    return {"frame": frame, "period": home[0].astype(int).values, "players": players,
            "team": team, "ball": ball}


def event_labels(folder, game, n_frames_by_frame):
    """Per-frame codes (0=H,1=A,2=D,3=X) indexed by tracking row (frame-1)."""
    ev = pd.read_csv("{}/{}/{}_RawEventsData.csv".format(folder, game, game))
    ev = ev.sort_values(["Start Frame", "End Frame"], kind="mergesort").reset_index(drop=True)
    n = n_frames_by_frame
    codes = np.full(n, 3, dtype=np.int8)
    team_code = {"Home": 0, "Away": 1}
    periods = {}
    for p, g in ev.groupby("Period"):
        periods[p] = (int(g["Start Frame"].min()), int(g["End Frame"].max()))
    for p, (lo, hi) in periods.items():
        lo = max(lo - 1, 0)
        hi = min(hi, n)
        cur, dead = None, True
        events = ev[ev["Period"] == p]
        marks = []                                   # (frame_index, state)
        for _, r in events.iterrows():
            f = int(r["Start Frame"]) - 1
            t = team_code.get(r["Team"])
            typ = r["Type"]
            if typ == "SET PIECE" and t is not None:
                marks.append((f, t))                  # restart: that team has the ball, play live
            elif typ in OWN and t is not None:
                marks.append((f, t))
            elif typ in DEAD_START:
                marks.append((f, 2))
            elif typ == "SHOT" and str(r["Subtype"]).upper().find("GOAL") >= 0:
                marks.append((int(r["End Frame"]) - 1, 2))
        marks.sort(key=lambda m: m[0])
        state, pos = 2, lo
        for f, s in marks:
            f = min(max(f, lo), hi)
            codes[pos:f] = state
            pos = f
            state = s
        codes[pos:hi] = state
    return codes
