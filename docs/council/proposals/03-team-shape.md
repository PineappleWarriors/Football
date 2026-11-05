# Proposal 03: Ball-free collective team-shape inference

## Core idea
Possession is a property of the 22 players, not only the ball. The team in possession pushes its centroid and defensive line forward, spreads wide, and has runners moving upfield. The defending team compacts, drops and presses toward the ball zone. Compute a per-frame "attack score" per team from shape alone, take the sign as an H/A posterior, and feed it into a spell-level HMM (states H/A/D) with sticky transitions.

## Signals/inputs
Automatic ATD player tracks (46 slots, homography to pitch metres). Each team's centroid and line height (mean x of the back 4 outfielders) in its own attacking direction, taken from Smart Tagging half and side info. Team width and depth, plus convex-hull area. Mean forward velocity over a 2 s window. Voronoi space-control share in the final third. Pressing: count of opponents within 5 m of the nearest player, and nearest-opponent pressure on the centroid-nearest player. Smart Tagging phases and set pieces are used as priors. The ball, when visible, is a high-confidence emission that overrides shape.

## Ball-missing frames (41%)
Shape-only emission, smoothed by the HMM and anchored to the nearest visible-ball frames. A proxy "ball locus" is the player cluster with the highest local density plus convergence of the opposing side. The state is held through short gaps and flips only when the shape evidence is sustained for 1-2 s.

## Dead-ball detection
Mean player speed and the fraction of stationary players are high. Players then stand in a set-piece formation (restart shapes, a wall, a goal-kick line-up). Smart Tagging set-piece intervals mark D. A long missing ball combined with low collective motion also suggests D. A ball-free "everyone walking" state is a strong D cue.

## Parameters without match GT/video
Principled defaults only: window lengths, hysteresis (min spell about 3 s, matching typical real possession durations), thresholds set as per-match z-scores (self-normalised, no labels). Optional fitting of the logistic weights on external, rights-cleared tracking data with events, such as Metrica Sports sample games (open, CC-BY-NC 4.0 per their repository, so I would verify the licence) and SkillCorner open data (licence check required). Weights are fitted there and frozen. If the licence is not cleared, equal-weight z-score defaults are used and no fitting is done.

## Expected spellF1 gain vs 0.2433
I estimate +0.02 to +0.06 on its own, which is speculative and untested. Shape-only possession accuracy in the literature is modest (about 65-75% frame accuracy), and a spell metric at IoU 0.3-0.7 punishes boundary jitter. The real value is as a gap-filler and tie-breaker when the ball is absent, where the baseline likely holds or guesses. It is weaker as a standalone method.

## Biggest risks
- Shape lags the ball by seconds, so turnovers are late.
- Counter-attacks and transitions invert the cues.
- Anonymous slots may swap teams; the team assignment must be checked, though the baseline loader already handles this.
- Generalisation from external datasets to this broadcast-style ATD tracking is unproven.
- Without GT-based evaluation there is no way to confirm that the weights help.

## Effort
About 14-20 hours: features 5, HMM and post-processing 4, external-data fitting 5, docs and checks 3.

## Rules-compliance verdict
Compliant if weights are fixed by defaults or fitted on external data only, with no use of the public GT or video for tuning. The public GT is for sanity checks only. Algorithmic labels, a documented pipeline, and a licence check on any external dataset are required before use.
