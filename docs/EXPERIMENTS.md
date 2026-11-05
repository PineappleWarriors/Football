# Experiment log

Compare against `baseline_smooth50`. Public-window numbers are a correctness check only; do not pick
between variants on them (use `--bootstrap 1000` if a gap looks real). Record the *reasoning*, and
the external data (if any) used for tuning.

| date | name | idea | spellF1 | macroF1 | poss | mean dur (s) | notes |
|---|---|---|---|---|---|---|---|
| - | baseline_smooth50 | nearest player to ball, +-50 frame vote | 0.3256 (public) / 0.2433 (full) | 0.6207 | 26 | 10.8 | floor |
