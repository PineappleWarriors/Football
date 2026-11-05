# 04 - Smart-Tagging fusion (priors + tracking)

## Core idea
Treat the 638 automatic Smart Tagging phases as a *noisy prior track* over a two-layer state machine: a live/dead layer anchored on set pieces, and a possession-team layer (H/A) driven by tracking evidence, with phase `Team` as a soft prior. Output is whole spells (Viterbi/HSMM decode), not per-frame votes.

## Signals/inputs
- Smart Tagging: `Team`, `Half`, `Type` (throw-in, corner, goal kick, free kick, kick-off), phase intervals (`round(s*25)`).
- ATD: ball x/y (59% of graded frames), player positions and team per slot, speeds.
- Homography (valid 100%) only for pitch-line/touchline distance; no video.
- Baseline nearest-player vote kept as one emission feature.

## Ball-missing frames (41%)
No D/X by default. Emissions come from the ball-free evidence: team-centroid shift, team compression toward the ball side, players' speed fields, and the phase Team prior. Short gaps inside a spell inherit the state (decode stays put; a switch needs sustained opposite evidence). Long gaps with no ball AND a set-piece anchor become candidate dead-ball. X is used only inside spells, never near a turnover.

## Dead-ball detection
Set pieces give restart anchors: dead state from (tag start - lead-in) until play resumes. Resumption = first frame after the anchor where the ball moves above a speed threshold or players disperse (mean speed/spread rising). Dead also from: ball absent with all players slow/static for a long run; stoppage before goal kick/corner/free kick. Kick-off tags (6) give hard resets. Each restart starts a new spell.

## Parameters WITHOUT match GT/video
- Principled defaults: hysteresis/min-duration from football priors (typical possessions are about 5-15 s; min spell about 1.5-2 s; merge gaps under 1 s).
- Team-prior weight and Team=N/A handling set by a *generative* argument, not tuned: N/A (all throw-ins) gets a flat prior, and the throw-in team is inferred by the resumption: the team whose nearest player to the touchline ball point restarts (or the side opposite the team last in control before the stoppage, a standard rule).
- Tag-vs-tracking agreement stats can be computed on the full unlabeled match (self-consistency, no labels) to weight the prior.
- Any real fitting only on external data we hold rights to (e.g. other open tracking/event datasets such as SkillCorner or Metrica sample games); none planned for v1. The 5-min public GT is a sanity check only, never for selection.

## Expected spellF1
Roughly 0.30-0.38 vs 0.2433 (honest, wide band; below the 0.04 noise band it may not show). Gain comes from (1) restarts fixing spell boundaries so the IoU at 0.3-0.7 matches, (2) fewer phantom possessions from structure, (3) a Team prior stabilising ball-missing stretches. Phase intervals are coarse, so I do not expect much beyond that.

## Biggest risks
- Tags are automatic and false positive/negative; Team may be wrong or lag the true turnover; phases are not possessions. Over-trusting them imports their errors.
- Throw-in team inference is weak. Resumption detection could be off by seconds (a 1 s offset costs about 35% spellF1 on that spell).
- Only 59 set pieces, so D coverage is partial; most of the dead time (fouls, injuries) is not tagged.
- Prior-weight choice can quietly become match-tuning; must be fixed a priori.

## Effort
About 14-18 hours: loaders and alignment 2h, dead-ball and resumption logic 5h, HSMM/Viterbi fusion 5h, checks, validator and doc 3h.

## Rules-compliance verdict
Compliant. All inputs are provided automatic data, the labels come from code, no hand labels or event data for this match, and the public GT is used only for pipeline sanity checks. External data, if any, will be documented. Reproducible and deterministic.
