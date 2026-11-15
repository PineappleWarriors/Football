# RL experiment: can a learned policy beat the Viterbi model?

**One button:** `./run_rl.sh 8` (Linux/macOS) or `run_rl.bat 8` (Windows) -- 8 = hours. Safe to stop and
re-run (resumes). `./run_rl.sh smoke` is a ~6 minute check. Result: `rl/runs/latest/report.md`.

## What it does
1. Creates `.venv_rl`, installs numpy/pandas/torch, downloads Metrica's public sample games 1 and 2.
2. Builds per-sample features (ball/player distances, ball-gap structure, stillness, team shape) and
   event-derived labels (same derivation as `possession/external_metrica.py`).
3. For two folds (train game 1 / validate game 2, and the reverse):
   - **imitation**: bidirectional-GRU policy, cross-entropy on the labels (15% of the time);
   - **RL**: REINFORCE (K=8 sampled label sequences per 5-minute window, leave-one-out baseline),
     reward = spellF1 + 0.5*macroF1 from the repo's own scorer, plus a small label-anchor loss.
   - Checkpoint chosen on held-out period 1; **reported on held-out period 2** (not selected on).
   - The Viterbi model is evaluated on the same held-out period for comparison.
4. Trains a final model on both games (iteration count = median best fold iteration).
5. Writes `report.md` with a verdict. The bar to adopt RL: > +0.02 spellF1 over Viterbi in BOTH folds.

## Rules
Allowed (RULES.md): any method, trained on **external** data only. This never touches BAR-ATH data or
its ground truth. If you adopt the policy, commit the weights (`rl/runs/latest/final/last.pt`) so the
submission file is reproducible, and describe the training data in `docs/TECHNICAL_DOC.md`.

## Honest caveats
- Two games only (~280 possessions each): overfitting is the main risk; treat < +0.02 as noise.
- The policy emits an independent label per sample; the reward only scores the whole sequence, so credit
  assignment is weak. The label-anchor loss keeps it from drifting.
- Features like gap structure may transfer imperfectly to the challenge's tracking.
- Resource use: CPU is fine (a GPU is used automatically if present); expect a few GB of RAM.
