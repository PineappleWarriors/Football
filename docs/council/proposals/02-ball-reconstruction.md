# Proposal 02: Ball-trajectory reconstruction, then control detection

## Core idea
Complete the ball trajectory first, then detect control on a gap-free track. Fill the 41% missing frames with a kinematic smoother (RTS over a constant-velocity/ballistic model), constrain it with player-motion evidence, and run one control detector on the completed track. Spell post-processing (hysteresis, min-duration) follows (see skill spell-postprocessing).

## Signals/inputs used
- ATD ball (x,y,speed) with NaN gaps, 46 player slots (position, speed), homography (metres).
- Smart Tagging phases/set pieces, used only for restart and dead-ball intervals.
- Optional: broadcast video is NOT used.

## How ball-missing frames (41%) are handled
1. Short gaps (<~1 s): RTS/Kalman smoothing. State is (x, y, vx, vy) with process noise from physical limits (ball speed <= ~35 m/s, ground deceleration ~ rolling friction). Gaps are bridged only where the smoothed covariance stays below a threshold.
2. Long gaps: no physics prior is credible. Estimate a latent ball position as the argmax of a "pull" score: the centroid of the 2-3 nearest players weighted by who accelerates toward a point and who is stationary/decelerating (carrier cue), blended with the Kalman prediction and gated by speed limits.
3. Each filled frame carries a confidence. Below the threshold the frame is `X` inside a possession (free on spellF1, forward-filled) and a guess only when the neighbouring observed segments show different controllers, so that the transition is not carried over.

## How dead-ball is detected
- Smart Tagging set-piece/restart intervals plus ball stationarity or off-pitch in homography coordinates (outside lines).
- Player stillness and spread (a dispersed, walking block with no player within ~2 m of the ball for >3 s).
- Missing ball alone is never D. The completed track is tested for the same rules, and gaps shorter than 2 s that begin and end in play remain live.

## How parameters are set WITHOUT using match GT/video
Honestly: most are physical constants or principled defaults, not fitted. Ball max speed (~35 m/s), friction deceleration, control radius (~1.5-2 m), min control duration (~1 s, ~2 s per CHALLENGE.md "a few seconds"), and noise covariances come from the physics and the tracker's reported accuracy. Anything that needs fitting (Kalman Q/R, control-radius, hysteresis) would be tuned only on external open tracking data we may legally use (e.g. Metrica Sports sample games, SkillCorner open data; licence check first, per RULES.md/mtah-rules-check), with ball dropout simulated by masking. Not tuned on the public GT or on this match. The gap model stays physically motivated so there is little to tune.

## Expected spellF1 gain vs 0.2433
Modest and uncertain: +0.05 to +0.12 (to ~0.30-0.36), roughly at or above the 0.04 noise band. Most of the baseline's loss is fragmentation and false switches, not missing coverage. A completed track reduces spurious D and removes hold-last flicker, but the large gains come from spell logic and dead-ball detection, which this approach only partly addresses. It is best as a front-end module for a combined solution.

## Biggest risks
- Player-pull inference for long gaps is a weak signal; errors during gaps can create false turnovers.
- Passes and aerial balls over long gaps are not ballistic in 2D, since the data has no height.
- ID switches and fragmented tracks (46 slots for 22 players) degrade motion cues.
- Complexity may outstrip the evidence. Gains may not show against a ~0.04 noise band.
- Cannot be verified here (data/ empty).

## Effort
About 20-28 h: Kalman/RTS gap fill (6 h), player-pull estimator (6 h), control/dead-ball logic (6 h), external-data calibration and simulated-dropout tests (6-8 h), docs/repro (2 h).

## Rules-compliance verdict
Compliant. It is fully algorithmic, with no hand labels or hand-corrected ball positions. The public GT is used only for pipeline correctness checks, not for tuning. Any fitting uses external data with a licence check before use. The code and method are fully inspectable.
