# Critique D: football and data-domain correctness

## Cross-cutting errors
1. **Missing ball is not random.** The 41% gap clusters in aerial and crowded moments: goal kicks, clearances, long balls, box scrambles. "Hold last state through the gap" (01, 04, 06, 08, 09, 10) fails exactly where turnovers happen.
2. **GT is mechanical** (dead flag, else tracked owner). Human-style "controlled gain" rules (09's 1.5 s dwell, 01's 1 s dominance, 05's event labels) delay or miss short spells the GT records.
3. **Tags are not possessions.** Throw-in `Team` is N/A, so a throw-in marks a boundary only. Only about 59 set pieces exist, so D coverage is partial.
4. **Stillness is a weak D cue.** Build-up play is slow, and fast restarts have moving players and a missing ball.
5. **Slot churn** (46 slots, ID switches) breaks per-player statistics.
6. **Counter-attacks** invert shape cues: the attacking block is stretched, not compressed.

## Scores (domain soundness, 1-10)
- **01 HMM, 6.** Persistence logic is sound. A 30 s median D dwell is too long (many stoppages last 5-15 s). It ignores that gaps coincide with turnovers.
- **02 Ball reconstruction, 5.** There is no height in the data, so aerial balls cannot be filled ballistically. The player-pull estimator is circular.
- **03 Team shape, 4.** It lags by seconds and fails on counters. The literature accuracy figure is for coarse phases.
- **04 Tagging fusion, 6.** Restart anchors are right. Inferring the throw-in team from the last control is unreliable when the ball is missing. Resumption offsets of 1 s or more are likely.
- **05 External model, 6.** It is the only approach that could learn the dropout/turnover correlation. The label mismatch with the mechanical GT and the optical-to-ATD domain gap are serious, and i.i.d. masking understates both.
- **06 Dead-ball first, 6.** The D-first insight is correct, but the stillness cues are weak.
- **07 Video ball, 5.** It targets the right frames, but the ball is hardest to detect in those same aerial and crowded frames.
- **08 Metric DP, 5.** The metric analysis is good. The simulator assumes i.i.d. dropouts, but real errors correlate with turnovers, so the boundary cost is untrustworthy. It is a decoder only.
- **09 Event pipeline, 5.** It matches the definition's wording, not the mechanical GT. Touch detection on 25 fps data with the ball missing 41% of the time is brittle.
- **10 Ensemble and abstention, 4.** Dawid-Skene assumes independent errors, but the estimators share the same tracking. X forward-fills across turnovers, which cluster in the gaps where X would be used.

## Recommendation
Combine 06 (D layer), 04 (restart anchors) and 01 or 08 (decoder). Add a prior that a gap right after a clearance or goal kick probably means a team change.
