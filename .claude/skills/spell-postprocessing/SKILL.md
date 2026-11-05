---
name: spell-postprocessing
description: Use when per-frame H/A/D predictions flicker, produce too many possessions, or need hysteresis, minimum-duration or merge logic to improve spellF1.
---
# Spell post-processing
- Target realistic spell counts and durations (GT mean ~14 s); raw nearest-player gives ~2 s and 131 spells per 5 min.
- Tools: hysteresis on team switches, minimum-duration filtering, merging short flips back into the surrounding spell, state machine (live/dead x team) instead of independent smoothing.
- Dead-ball runs split possessions: keep D stretches intact.
- Parameters come from external data or principled defaults; never from the public GT window (smooth125 wins publicly, loses on the full match).
- Check with spellF1 at IoU 0.3-0.7 and the possession count/duration lines in `run_evaluation.py` output.
