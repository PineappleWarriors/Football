# 07 - Video ball detection (CV on tactical/broadcast video)

## Core idea
Run an open pretrained ball (+player) detector on the tactical video to recover the ball on the ~41% of graded frames where ATD has none, project it to pitch coords with the supplied homography, then feed a filled ball track into a standard nearest-player / hysteresis possession pipeline. Optionally use the broadcast feed as a second view.

## Signals/inputs
Tactical mp4 (1920x1080, 25 fps), tactical homography (100% valid), ATD players and ball, Smart Tagging (restarts). Broadcast video is secondary: unsynchronised, 65.8% usable homography, needs an automatic alignment step (e.g. cross-correlating ATD player/ball motion energy), so it is expensive for little gain.

## Ball-missing frames
Run the detector on missing frames only (plus +-1 s around gaps for track continuity), detect on crops/tiles (ball is ~8-12 px), keep detections above a confidence threshold, then gate them: project through H, reject points off pitch or far from the interpolated trajectory, and link with a Kalman/ballistic smoother. Gaps that stay unfilled fall back to the last-controlled team (X inside a possession is free for spellF1). Missing is never equated with D.

## Pretrained models and licences
- Ultralytics YOLOv8/11 with COCO "sports ball": AGPL-3.0 (public repo OK, must be disclosed). Weak on small broadcast balls.
- Public football-ball YOLO weights (Roboflow Universe / HuggingFace community checkpoints): licences vary (often CC BY 4.0); each must be checked individually.
- SoccerNet tracking/ball-detection baselines, TrackNetV3-style small-object nets: mostly MIT/Apache or research-only. Verify before use.
- Fine-tuning allowed only on external data (SoccerNet, public ball datasets), never on this match.

## Parameters without match GT
Confidence threshold, gating radius and Kalman noise are set from external annotated footage (SoccerNet/other public games) or from physical limits (max ball speed ~35 m/s = 1.4 m/frame). Held-out check: re-mask known ATD ball frames on this match (an automatic check against ATD data, not GT) and measure detector recall/error. That is allowed as an "automatic check on provided data", but I would not tune possession parameters on it.

## Expected spellF1 gain vs 0.2433
Honest estimate: +0.02 to +0.06, within the 0.04 noise band. Reason: spellF1 is dominated by possession-boundary placement and spell count, not ball coverage. The baseline's weakness is flicker (smooth25 -> smooth50 moved it 0.20 -> 0.24), which hysteresis and min-duration fix at zero video cost. Ball recovery helps mainly during aerial/crowded phases, exactly where detectors also fail (occlusion, ball in air, motion blur). Video detection is an enhancer, not a standalone route to a large gain. Contact/pose cues add little at this resolution and I would not rely on them.

## Biggest risks
1. Detector recall on a tiny, blurred ball is low (likely 30-60% on the missing frames, which are the hard ones; the ATD tracker presumably already took the easy ones).
2. False positives (boots, line marks, ad boards) create phantom possession flips.
3. Compute and time against the 17 Nov deadline.
4. Broadcast alignment is a project in itself.
5. Licence mismatches (AGPL, per-dataset terms).

## Effort and compute
- Decoding: 199k frames 1080p ~ 10-20 min CPU with ffmpeg (hw decode much faster). Graded-only gap frames ~65k, so subsample every 2nd frame (12.5 fps).
- Inference: YOLO-m at 1280 tiled (about 4 tiles) ~ 25 ms/tile on a T4 -> about 1.5-2 h GPU for ~65k frames; CPU-only is ~10x slower (15-25 h), which is infeasible. A GPU in the cloud container is NOT guaranteed (assume none; check nvidia-smi first). Without a GPU, restrict to the +-2 s windows around ambiguous transitions (~10-15% of frames).
- Engineering: ~20-30 h (decode, tiling, gating, track fusion, validation), plus 3-5 h integration with the base pipeline.

## Rules-compliance verdict
Compliant if: models are public, run locally, no match video or data goes to external services, no fine-tuning on this match or the public GT, and the repo/technical doc names weights and licences. Watching the video to design features is allowed; hand-corrected ball positions are not. Verdict: allowed, but low-risk-reward; recommend it as an optional module after the video-free hysteresis pipeline, not as the primary approach.
