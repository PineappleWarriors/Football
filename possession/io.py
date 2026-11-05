"""Read the raw ATD at 5 Hz into arrays (metres). Parsing mirrors starter/baseline.py."""
import numpy as np

from possession.params import STEP


def _xy_speed(group, length, width):
    if group[0] == "N":
        return np.nan, np.nan, np.nan
    a, b, c = group.split(",")
    return float(a) * length, float(b) * width, float(c)


def load_tracking(raw_path, team_of_track, pitch, step=STEP):
    """-> dict(frames, players[N,S,2], pspeed[N,S], team[S], ball[N,2]); frames are video frames."""
    length, width = pitch
    frames, players, speeds, balls = [], [], [], []
    slots = len(team_of_track)
    with open(raw_path) as handle:
        for line in handle:
            parts = line.split(":")
            if len(parts) != 3:
                continue
            video = int(parts[0]) - 1
            if video % step:
                continue
            row = np.full((slots, 2), np.nan)
            spd = np.full(slots, np.nan)
            for slot, group in enumerate(parts[1].split(";")):
                if slot >= slots:
                    break
                x, y, s = _xy_speed(group, length, width)
                row[slot] = (x, y)
                spd[slot] = s
            bx, by, _ = _xy_speed(parts[2].strip(), length, width)
            frames.append(video)
            players.append(row)
            speeds.append(spd)
            balls.append((bx, by))
    return {"frames": np.array(frames), "players": np.array(players), "pspeed": np.array(speeds),
            "team": np.asarray(team_of_track), "ball": np.array(balls)}
