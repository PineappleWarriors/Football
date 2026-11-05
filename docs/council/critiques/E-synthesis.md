# E - Synthesis: one staged pipeline (numpy/pandas, Py3.8+)

## Shared core (7 of 10 proposals)
Missing ball is missing evidence, never D. A 3-state decoder with a duration prior and costly
H<->A switches. D only on positive evidence. Set pieces are hard boundaries. X only mid-spell.
Priors are physical, not fitted to the GT.

## Distinct contributions worth keeping
- 08: semi-Markov DP, simulator-chosen boundary cost, metric analysis (prefer merging, ~0.5 s tolerance).
- 06: D as a separate hysteresis detector whose runs are hard boundaries.
- 04: Smart Tagging restart anchors, new spell per restart.
- 09: touch/control test as the "controlled gain" switch evidence.
- 03: ball-free shape emission as a gap filler.
- 10: abstention rule and unsupervised reliability weights.

## Cut
- 05 (learned GRU): 25-35 h, licence/domain-gap risk, event labels differ from the GT definition.
- 07 (video ball): GPU unknown, gain inside the noise band.
- 02 Kalman/pull-estimator: keep only <=1 s linear bridging.
- 10 Dawid-Skene EM: correlated estimators; use fixed capped weights.
- 01's D_restart sub-state; Voronoi pitch control (v2 at most).

## Pipeline (each module = pure function on arrays, 5 Hz internal, upsample to 25 fps at the end)

| # | Module | Input -> Output | From |
|---|---|---|---|
| M0 | `load_align` | repo loaders, `games.py` -> `players[T,46,2]`, team[46], `ball[T,2]`+`vis[T]`, tags df (frame-aligned) | baseline |
| M1 | `features` | M0 -> d_H, d_A (m), margin, ball speed, in-bounds flag, median player speed, still-fraction, team centroid/line height in attack direction, hull spread; ball bridged <=1 s | 01, 02, 03 |
| M2 | `deadball` | M1 + tags -> `p_dead[T]`, hard restart anchors `R` (frames) | 06, 04 |
| M3 | `team_evidence` | M1 -> `ll[T,2]` log-lik H vs A. Ball seen: logistic in (d_A-d_H) with a control-radius gate. Ball missing: shape-only term (centroid/line advance), weight capped, otherwise 0 (flat) | 01, 03, 10 |
| M4 | `control` | ball + players -> `switch_ev[T]`: sustained >=1.5 s opponent control, or two consecutive opponent touches (filters deflections/duels) | 09 |
| M5 | `hsmm_decode` | `ll`, `p_dead`, `switch_ev`, `R` -> segments (start, end, label); duration log-normal, per-boundary cost, new spell forced at each R, min spell ~2 s | 08, 01 |
| M6 | `postprocess` | segments -> frame labels. Merge same-team spells split by <1 s gaps; merge sub-2 s spells; X only inside spells where posterior >0.9 and hazard low, optional flag, default off | 10, spell-postprocessing |
| M7 | `sim_calibrate` | synthetic simulator (spell lengths from the prior, 65% accuracy, 41% dropout), scored with `spell_scores`, picks boundary cost | 08 |
| M8 | `report` | CSV, validator, spellF1/macroF1, count, mean duration | AGENTS.md |

## Increments (each ships a valid CSV and is compared with smooth50)
1. M0+M1+nearest-player ll + M5, D = ball-missing-and-still (~6 h).
2. M2 (stillness, out of bounds, tag anchors) (~6 h).
3. M7 cost selection, M6 merging (~3 h).
4. M3 shape term for ball-missing frames (~4 h).
5. M4 control test as switch gating (~5 h).
6. X policy (~2 h), only if macroF1 loss is acceptable.

Total ~26 h.

## Risks
- Team assignment is the cap; shape lags the ball, so keep its weight low.
- No GT: fix constants a priori, document them, run `mtah-rules-check`.
- A 1 s boundary error costs ~0.35 IoU, so restart anchors (M2) beat frame accuracy.
