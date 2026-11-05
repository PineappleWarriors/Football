---
name: score-and-compare
description: Use after producing a candidate submission CSV and needing to score it against the baselines and report results.
---
# Score and compare
1. Save the candidate to `evaluation/results/<name>.csv` (gitignored).
2. `python evaluation/run_evaluation.py` (add `--bootstrap 1000` if a gap looks real).
3. Report vs `baseline_smooth50`: spellF1, macroF1, possession count, mean duration (compare with GT: 17 possessions, 14.2 s).
4. Append a row to `docs/EXPERIMENTS.md`.
Public window = 17 possessions: noise ~0.06 per possession. Never choose between variants on it; use it only to confirm alignment and label semantics.
