# Technical document (draft; export to `<team_name>.pdf` or `.md`)

## 1. Approach
A 5 Hz three-state (H/A/D) Viterbi decode with switching penalties, followed by merging of
spells shorter than 2 s and upsampling to 25 fps. Chosen by a design council (docs/council/) as
the strongest approach that needs no training data: possession-level scoring (spellF1) rewards
whole, correctly bounded spells, and a switching penalty acts as a possession-length prior.

## 2. Assets used / dropped
- Used: tactical ATD tracking (positions, player speed, ball), ATD metadata (team of each track slot).
- Not used (yet): Smart Tagging (optional `--use-tags`, off), homography, both videos, broadcast feed.
- Dropped after review: learned sequence model, video ball detection, unsupervised EM ensemble.

## 3. Training data
Only EXTERNAL data, never the provided match, its video, or its ground truth.
- Source: Metrica Sports public sample data, Sample_Game_1 and Sample_Game_2 (CSV format),
  https://github.com/metrica-sports/sample-data (anonymised tracking + event data; README asks users to
  acknowledge the source; it has no separate licence file -- confirm terms before publishing anything).
- Labels: derived mechanically from the games' event data (possession = team of the last PASS/SHOT/
  RECOVERY/restart; dead = BALL OUT/FAULT/goal until the next restart). Sanity check: 17.0 and 15.7
  possessions per 5 min, mean 12-15 s -- the same statistics the challenge states for its ground truth.
- What is trained: one small logistic regression (dead-ball probability from ball-gap structure and
  player stillness; `possession/models/dead_ext_v1.json`, trained by `experiments/train_dead_model.py`).
- What is tuned on external data: the switching cost, team-evidence slope, control radius and ball-speed
  gate (`possession/params.py`), chosen on one external game and checked on the other.
- Validation protocol: `experiments/eval_external.py` (train/tune on one game, test on the other, repo scorer).

## 4. Possession rules implemented
- Per sample, team evidence = logistic in (distance of nearest away player - nearest home player) to
  the ball, only when the ball is within 10 m of someone (otherwise no evidence: loose ball).
- Missing ball = missing evidence (never D). Gaps up to 1 s are linearly bridged at half weight.
- Dead ball evidence: ball outside the pitch (+1 m), or players standing (median speed < 1.2 m/s)
  with a missing/slow ball. Probabilities are coarse ordered priors (`possession/params.py`).
- Switching penalties (6 nats H<->A, 5 nats live<->dead) act as the duration prior; live spells
  under 2 s are merged into the longer neighbour. X is not used.

## 5. Parameter provenance
Physical constants are fixed a priori; the decoder constants were tuned on external games only (see 3).
Nothing was tuned on the provided match, its video or the public ground truth.

## 6. Limitations
Team assignment from nearest player is the accuracy cap; ball-missing frames cluster at aerial
turnovers where the decoder holds the previous team; no controlled-possession (dwell) test yet;
tag anchors untested; real-match score not yet measured.

## 7. Reproduction
```bash
pip install -r requirements.txt
# place the organiser bundle in ./data (not committed)
make test
make run OUT=evaluation/results/<team_name>.csv
python evaluation/validate_submission.py evaluation/results/<team_name>.csv
```
Python 3.8+, numpy + pandas only. Deterministic (no randomness in the pipeline).

## 8. Stopgap path (only while the tactical ATD is unavailable)
`possession/make_stopgap.py` fuses the organisers' shipped `evaluation/results/baseline_raw.csv`
(automatic nearest-player output; D = untracked ball) with a capped Smart Tagging prior and the same
Viterbi decode. It is NOT the intended final path: regenerate the final CSV from the raw ATD with
`possession.pipeline`. Homography camera motion was checked as a dead-ball cue and rejected (does not
separate D from live). Tag window ends do not line up with turnovers (checked on tags alone).

### 8b. Broadcast alignment (stopgap v2)
`possession/broadcast_align.py` aligns the unsynchronised broadcast tracking to the tactical timeline
by cross-correlating the per-frame 'team of nearest player to ball' series of both feeds (no video, no
GT, no manual input). It finds constant lags of +4014 (1st half) and +26920 frames (2nd half), verifies
10 s windows against shifted controls (92% vs 51% agreement), and covers 38% of graded frames.
Broadcast player speeds on those frames give a stillness cue for dead ball. The broadcast ball rarely
fills tactical ball gaps (5%): both feeds lose the ball at the same moments.
