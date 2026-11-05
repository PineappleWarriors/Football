# 06 - Dead-ball first (D detector, then team assignment on live segments)

## Core idea
D vs live is solved as its own two-state segmentation; every D run is a hard possession boundary and every live run is then a sequence of H/A spells. Rationale: the baseline emits D whenever the ball is untracked, so it shreds possessions (raw 0.05 -> smooth50 0.24 shows count inflation is the killer). A correct D mask fixes spell boundaries and gives restart anchors, so team assignment only has to answer "who holds it" inside bounded segments.

## Signals / inputs
- Ball off bounds: normalised ball (x,y) outside [0,1]^2 (x105 m, x68 m), last-seen position near a line/goal.
- Collective stillness: median player speed (`*_s`) across visible slots below ~1.0 m/s for >2 s; walking-pace, no sprinting.
- Set-piece clustering: players-in-box count, spread (convex-hull area / mean pairwise dist) typical of corners, free kicks, goal kicks.
- Smart Tagging `SET PIECES` intervals (Kick Off, Corner, Free Kick, Goal Kick, Throw-in): a restart marks the END of a D run; the interval start-minus-lead-in is the D run.
- Long ball-missing run + static players = D; ball missing + players moving at pace = live.
- Goal celebration: players clumped (hull collapse) plus slow, after a goal-box ball exit.
- Output: hysteresis state machine (enter D when >=2 cues for >=1.5 s; exit on restart tag, ball re-appears inside pitch with player speed jump).

## Ball-missing frames (41%)
Never default to D. Missing ball is classified by player kinematics: moving/spread -> live, carry the last label (X-like persistence, but written as H/A for macroF1); static/clustered/out-of-bounds exit -> D. Within live missing runs, hold the previous possession unless the nearest-player-to-last-ball / team centroid drift (team whose block advances towards the other half) indicates a turnover with a sustained margin; use X only mid-spell.

## Parameters WITHOUT match GT/video
Only external data: public tracking sets with event/dead-ball labels (e.g. SkillCorner open data, Metrica sample games, PFF/StatsBomb 360 where licensed) after confirming rights via RULES.md. Fit thresholds (speed, dwell time, hull stats) there, rescale to 25 fps/normalised units. Football priors (D ~40-45% of time over a match, ~100-150 stoppages/half-match) as sanity checks on predicted counts and durations on our own output, not on GT. Public 5-min GT used only for pass/fail checks of the pipeline running, no adjustments.

## Expected spellF1 gain
From 0.2433 to ~0.33-0.40 (estimate, uncertain). Reasoning: spellF1 matches runs by IoU; correct D boundaries cut spurious possessions (count inflation) and align spell starts/ends at restarts (+IoU at 0.5-0.7). Team assignment stays baseline-quality, which caps the gain; within noise band (0.04) only if D detector is good.

## Biggest risks
1. Stoppages with ball missing and moving players (quick throw-ins, free kicks taken fast) -> missed D.
2. Tracker slot churn corrupts speed/stillness stats; need robust median over visible slots.
3. Smart Tagging is automatic and noisy (offsets, N/A teams for throw-ins); use as soft evidence.
4. Without ball, turnover detection inside live runs is weak; team assignment becomes the bottleneck.
5. External dead-ball labels may be scarce/uneven in format; threshold transfer may be off.

## Effort
~16-22 h: D feature extraction 5 h, external-data calibration 6 h, state machine/hysteresis 4 h, team assignment on live segments 4 h, evaluation/docs 3 h.

## Rules-compliance verdict
Compliant if thresholds come only from external data (or are fixed football priors) and the provided match/video/public GT is never used for fitting; automatic checks on provided data are allowed. Run mtah-rules-check before using any external dataset. No hand labels used. Risk: low.
