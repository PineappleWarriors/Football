# Proposal 10: Uncertainty-aware ensemble with deliberate abstention

## Core idea
Several weak, roughly independent estimators each emit per-frame P(H), P(A), P(D). A Dawid-Skene-style EM fuses them into a posterior. A decision layer then exploits the scorer: spellF1 forward-fills `X` with the previous label in the half, so `X` is free *inside* a possession and harmful only *at* a hand-over. Policy: emit `X` when the fused posterior is confident that the possession persists (low transition hazard); force a hard H/A/D decision in a window around likely transitions, restarts and dead-ball boundaries.

## Signals/inputs
1. Nearest-player (distance-weighted softmax over the ball-to-player distance, tracking-quality gated).
2. Ball-zone control: Voronoi/pitch-control mass of each team around the ball, using homography-projected coordinates.
3. Team shape: team centroid and line height relative to the ball or the attacking direction. The attacking side tends to be compressed toward the ball. Works with no ball.
4. Smart Tagging prior: phase/set-piece type and `Team` give a restart owner. Throw-ins have N/A teams, so they only mark a boundary. Tagged set pieces anchor D then a new spell.
5. Motion: ball speed (zero or teleport means dead), player-cluster stillness for stoppages.
6. Persistence prior: an HMM transition matrix (see below).

## How ball-missing frames are handled
Ball absence is not D. Estimators 1 and 2 return a flat (uninformative) posterior when the ball is missing. Estimators 3 to 5 still vote, and the HMM carries the state forward, so confidence decays with the gap length. Short gaps inside a confident spell become `X`. Long gaps, or gaps that coincide with a tagged phase boundary or a shape flip, get a forced argmax. Dead-ball is entered only on positive evidence (a tagged stoppage, stillness, or the ball leaving the pitch just before a gap).

## How calibration/weights are set WITHOUT match GT/video
- Reliabilities: unsupervised EM over the estimators' hard votes on the provided tracking. This uses agreement only, with no labels and no GT. It is algorithmic and permitted ("learning without human labels").
- Priors and the HMM: dwell times and transition rates come from physical or football constants (a spell is about 10 to 30 s, restarts follow a stoppage), or from an external public tracking dataset with its own events (Metrica/SkillCorner open data, licence check first). No public GT and no video are used for fitting.
- Hyperparameters (hysteresis, X-confidence threshold) are fixed from the external data or set parameter-free: X iff posterior > 0.9 AND hazard < the median. Never swept against the public GT; the public GT is used only for a correctness check.

## Expected spellF1 gain vs 0.2433 and why
Estimate 0.30 to 0.38 (hedged; the noise band is ±0.04). The baseline's loss is possession fragmentation and missing ball frames labelled D. The HMM plus ensemble removes most spurious flips, and X-in-gaps protects spells without a guess. The abstention policy gives roughly +0.01 to +0.03 over the same ensemble without X (fewer accidental splits). The bulk of the gain comes from the ensemble and persistence, not from X. The X policy alone cannot lift the metric much, and it costs macroF1: about 41% of graded frames are ball-missing, so heavy X could drop macroF1 by 0.1 or more, and macroF1 is only the tie-break.

## Biggest risks
- Estimators are correlated (all use the same tracking), so EM overstates the reliability of the consensus. Fix: cap the weights and use tempered posteriors.
- EM can converge to a label-swapped or degenerate solution without anchors. Fix: initialise from nearest-player.
- X at a missed transition delivers the previous label across the hand-over, which costs a full spell. The hazard model must be conservative.
- Complexity: many tunable knobs with no GT to verify them.
- macroF1 penalty from X; tie-break only.

## Effort (hours)
About 25 to 35: estimators 10, EM and HMM 8, decision layer 4, external-data prior 6, reproducibility, docs and validation 4.

## Rules-compliance verdict
Compliant, provided that (a) EM/HMM parameters use only the provided tracking (unlabelled) or external data, (b) no GT or video-derived tuning and no hand labels are used, (c) any external dataset is licensed and documented, and (d) the output is regenerable by a deterministic seed. The public GT is used only to sanity-check formats and alignment.
