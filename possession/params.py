"""All tunable constants in one place, fixed a priori. Do not tune on the public ground truth."""

STEP = 5                    # internal rate = 25 fps / 5 = 5 Hz
HZ = 5.0
BRIDGE_S = 1.0              # linearly bridge ball gaps up to this long (physically plausible)
CONTROL_RADIUS_M = 10.0     # beyond this the ball is "loose": no team evidence
TEAM_SLOPE = 0.4            # logit per metre of (d_away - d_home); 2 m gap -> p ~ 0.69
MARGIN_CLIP_M = 8.0
BRIDGED_WEIGHT = 0.5        # evidence weight on interpolated ball positions
OOB_MARGIN_M = 1.0          # ball this far outside the pitch rectangle = out of play
STILL_PLAYER_MPS = 1.2      # median tracked-player speed below this = walking/standing
SLOW_BALL_MPS = 0.6         # ball essentially stationary
# Dead-ball evidence s in (0,1): P(dead | cues). Chosen as coarse, ordered priors.
S_OOB = 0.95
S_STILL_NOBALL_OR_SLOW = 0.70
S_STILL_ONLY = 0.30
S_BASE = 0.04
LAMBDA_TEAM = 6.0           # nats to switch H<->A (a priori, sanity-checked on the simulator)
LAMBDA_DEAD = 5.0           # nats to switch live<->dead
MIN_SPELL_S = 2.0           # merge live runs shorter than this into the longer neighbour
