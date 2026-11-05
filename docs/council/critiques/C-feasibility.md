# C-feasibility (12 days, 3-5 part-time, no data here, no GT tuning)

## Feasibility scores (1-10)
- 08 Metric-aware DP: **9** (6-8 h, numpy only; decoder needs an upstream signal)
- 04 Smart-Tagging fusion: **7** (provided data only; throw-in team inference weak)
- 01 HMM/semi-Markov: **7** (defaults-only is easy; overlaps 08)
- 06 Dead-ball first: **7** (defaults suffice; external calibration optional)
- 09 Event pipeline: **6** (many interacting constants, touch detection on a 59% ball is brittle)
- 03 Team shape: **5** (cheap as ball-missing emission, weak alone)
- 10 Ensemble + abstention: **5** (correlated estimators, EM unverifiable, X risky)
- 02 Ball reconstruction: **4** (20-28 h, 2D physics fails on aerial balls)
- 05 External learned model: **3** (licences, PFF approval delay, label derivation mismatch, training, untestable domain gap)
- 07 Video ball detection: **2** (GPU not guaranteed, AGPL/weights licences, low recall on the hard frames)

## Stack vs exclusive
- Decoders (pick one): 08 or 01 (plus HMM layers in 03/04/10). Use 08 as the engine, borrow 01's emissions.
- Modules that stack into it: 04 (restart anchors), 06 (D mask), 03 (shape emission when ball missing), 09's control test (optional feature).
- Heavy and optional: 02, 05, 07, 10's EM. Each 20+ h, none verifiable without GT. Skip.

## Debuggability without GT
Only self-consistency checks exist: spell count and mean duration vs football priors, D fraction (about 40-45%), D-run count vs tag count, re-masking known ATD ball frames, and 08's synthetic simulator. A module whose effect shows only in public-GT spellF1 cannot be judged (noise 0.04). Prefer modules with inspectable intermediates.

## Build order
1. **Days 0-2, valid improved CSV:** starter loaders; nearest-player H/A margin; missing ball = flat emission, never D; 5 Hz duration-aware DP (08), min spell about 2 s; D only from ball out-of-bounds plus slow players. Run validator; report both metrics, count, mean duration vs baseline.
2. **Days 3-5:** 04 tag anchors (D to restart, new spell, kick-off resets).
3. **Days 6-8:** 06 stillness/hull D cues with hysteresis; check D fraction and run counts.
4. **Days 9-10:** 03 shape emission for ball-missing stretches (z-score defaults, no fitting); simulator check of boundary cost.
5. **Day 11:** freeze, mtah-rules-check, final validator, tech write-up. Day 12 buffer.
6. Only if ahead: 09 control test; external sensitivity checks with licence review.

## Cross-cutting
- Keep all constants in one config, fixed before scoring, to avoid silent GT tuning.
- Default to emitting labels, not X (macroF1 cost, turnover risk).
