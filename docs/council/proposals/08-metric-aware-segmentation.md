# 08 - Metric-aware segmentation (DP over spell boundaries)

## Core idea
Stop labelling frames; choose a **segmentation**. Run a semi-Markov (Viterbi with duration) DP over each half whose states are spells {H, A, D}. Maximise: sum of per-frame log-evidence for the segment label, minus a per-boundary cost, plus a log duration prior (gamma/log-normal, mean ~14 s, mode ~8 s, long tail to 60 s+). The per-boundary cost is the single knob that trades spell count against recall. It is set from the metric's structure (below), not from the match.

Verified metric properties used (`possession_metrics.py`):
- Spells are maximal H/A runs, so any stray `D` or opposite label inside a possession splits it and adds an unmatched FP spell. Hysteresis and merging are therefore worth more than frame accuracy.
- Matching is greedy, one-to-one, same team only, IoU >= 0.3..0.7. A long predicted spell over two true spells matches at most one of them (one FN, no FP). A true spell cut into two predicted pieces matches at most one piece, and only if that piece reaches IoU >= threshold (one FP). Merging errs on the FN side and splitting on the FP side, but splitting also shrinks IoU. Given weak evidence, prefer merging.
- A 1-frame offset is free. A 3-frame offset costs about 0.018 and a 1 s offset about 0.35. So boundary precision needs to be good to about 0.5 s, not frame-exact.
- `X` is forward-filled within the half (`fill_abstentions`), so `X` means "continue previous spell". The DP can emit `X` only on interior frames where the segment label is already fixed. This is cosmetic for spellF1 and a macroF1 loss, so default to emitting the segment label instead.
- The IoU average over 0.3..0.7 rewards getting the bulk of every spell right over exact edges.

## Signals/inputs
Any upstream per-frame score can drive it. Use the nearest-player-to-ball team margin (baseline signal), a ball-in-play/dead prior from the Smart Tagging set-piece intervals, and player-stillness. The DP is a decoder, not a signal. It is signal-agnostic, so it composes with other council proposals.

## How ball-missing frames are handled
Missing ball is treated as **missing evidence, not as D**. Its emission log-likelihood is flat across H/A, and weakly favours D only when stillness or tagging agrees. The segment label is then held through gaps by the duration prior (the DP equivalent of `X` forward-fill). Segment boundaries are allowed inside a gap only if the evidence on either side disagrees. Expect about 41% of frames to be "free" and the boundary location to be interpolated.

## Parameters without match GT
All priors are fixed from the problem statement and football sense, not fitted: mean duration ~14 s (from PROBLEM.md/`EVALUATION.md` scale), minimum spell ~2 s, boundary cost chosen so that, on **synthetic** noisy signals, expected spell count lands near 60 s / 14 s per minute. Validate on a numpy simulator: draw spell lengths from the prior, corrupt a per-frame signal at ~65% frame accuracy with 41% dropouts, decode, and score with `spell_scores`. Choose the cost that maximises the simulated spellF1, and never tune it on the public five minutes. The public window is used only for a sanity check on alignment.

## Expected spellF1 gain vs 0.2433
Realistic target is **0.30-0.36** (about +0.06 to +0.12), with the caveat that it is bounded by upstream signal quality. The baseline's smooth50 is already a crude decoder, with a fixed window and no duration prior. A duration-aware DP should remove the remaining micro-spells and D flicker (which cost spell count), and place boundaries in ball-missing gaps better than a majority vote. It cannot recover turnovers the signal never saw. If the signal is near chance at the team level, the ceiling is about 0.30. Differences under 0.04 are noise on the full match.

## Biggest risks
- Garbage in, garbage out. The DP amplifies the signal and cannot create it. The gain is capped by team-call accuracy.
- Over-merging: a prior that is too strong gives a few long spells and low recall at IoU 0.7.
- Boundary cost mis-set, since there is no GT to calibrate it. The simulator may not match real noise structure (correlated errors).
- Duration-DP cost is O(N * Dmax) per half, about 90k frames * 1500 frames, manageable with a downsample to 5 Hz and a band.

## Effort
About 6-8 hours: DP decoder (2 h), simulator and cost selection (2 h), integration and baseline comparison with spell count and mean duration (2 h), docs (1 h).

## Rules-compliance verdict
Compliant. The labels come from an algorithm and no hand labels are used. The exploited "quirks" are the documented, intended behaviour of the scorer: `EVALUATION.md` explicitly describes the X forward-fill and 1-frame tolerance, and AGENTS.md instructs us to prefer whole spells. Using the metric's definition to design the decoder is legitimate. What would not be legitimate is fitting boundary costs or thresholds to the public five minutes or to the match GT. Priors here come from a synthetic simulator and football domain knowledge, and are documented in the technical doc. Needs `mtah-rules-check` before any parameter is finalised.
