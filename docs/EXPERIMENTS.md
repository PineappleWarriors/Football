# Experiment log

Compare against `baseline_smooth50`. Public-window numbers are a correctness check only; do not pick
between variants on them (use `--bootstrap 1000` if a gap looks real). Record the *reasoning*, and
the external data (if any) used for tuning.

| date | name | idea | spellF1 | macroF1 | poss | mean dur (s) | notes |
|---|---|---|---|---|---|---|---|
| - | baseline_smooth50 | nearest player to ball, +-50 frame vote | 0.3256 (public) / 0.2433 (full) | 0.6207 | 26 | 10.8 | floor |
| 2026-11-05 | viterbi_v1 | 5 Hz Viterbi H/A/D, switch penalties, dead-ball cues, min-spell merge | not run (no data) | - | - | - | simulator only: spellF1 ~0.7 on an idealised self-made generator (optimistic, NOT evidence); vote baseline 0.14-0.24 there |
| 2026-11-05 | tags_viterbi_v0 | Smart Tagging votes only + Viterbi | 0.191 (public) | 0.340 | 6 | 50.0 | 83 live spells over the match, mean ~75 s, no D: too sticky; tags too coarse in time. Dropped. |
| 2026-11-05 | stopgap_v1 | baseline_raw nearest-player (D=ball untracked) + capped tag prior + Viterbi (lam=ln(70)) | 0.455 (public) | 0.515 | 12 | 25.0 | NO tactical ATD available. 173 live spells over the match (mean ~37 s, target ~14 s), no D output. Public window = 17 possessions (+-0.06 per possession): NOT evidence of beating smooth50. Constants not chosen by public score; but public scores were seen after each change (0.352 -> 0.336 -> 0.455). |
