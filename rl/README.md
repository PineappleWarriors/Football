# RL experiment: can a learned policy beat the Viterbi model?

## Quick start (about 10 minutes of setup, then it runs on its own)

You do **not** need the competition's match data for this. It trains only on two public sample games
that the script downloads for you (about 130 MB).

1. **Install** Python 3.9 or newer (https://www.python.org/downloads/ -- on Windows tick
   "Add Python to PATH") and Git.
2. **Get the repository** (the branch with the RL code):
   ```bash
   git clone -b Jared_Dev https://github.com/PineappleWarriors/Football.git
   cd Football
   ```
   (If the repo is private, sign in to GitHub when asked.)
3. **Start it** -- one command, the number is how many hours to train (default 8):
   - Windows: double-click `run_rl.bat`, or in a terminal `run_rl.bat 8`
   - Linux / macOS: `./run_rl.sh 8`

   The first time it creates a virtual environment (`.venv_rl`), installs numpy/pandas/torch
   (a few minutes), downloads the data and builds features, then starts training by itself.
4. **Watch it**: open `rl/runs/latest/dashboard.html` in your browser. It refreshes every 15 seconds
   and shows the held-out score vs the current model, the training reward, and a timeline of the bot's
   actual decisions (Home / Away / Dead ball) against the truth and the Viterbi model. Drag the slider
   or press play to watch its decisions change as it trains.
5. **Stop it any time**: press `Ctrl+C` **once** in the terminal. It finishes the current step, saves
   everything, writes the report and exits. Run the same command again later to **resume** where it
   stopped (a second `Ctrl+C` aborts immediately, but the last periodic checkpoint is kept).
6. **Read the result**: `rl/runs/latest/report.md`. The bar to adopt RL over the current model:
   more than +0.02 spellF1 in both folds. Send it to me and I'll go through it with you.

`./run_rl.sh smoke` (or `run_rl.bat smoke`) is a ~6 minute check that everything works.
To start a completely fresh run, delete the folder `rl/runs/latest`.

Files: `rl/runs/latest/log.txt` (log), `metrics.json` (raw numbers), `*/best.pt` and `final/last.pt`
(trained weights), `report.md`.

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
