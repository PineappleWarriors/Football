# 09 - Rule-based event pipeline ("controlled possession" state machine)

## Core idea
Mirror the official definition literally. Possession is a state machine over {LIVE-H, LIVE-A, DEAD}. State only flips H->A
when an *event chain* shows the opponent gained **control**; touches, deflections and aerial duels never flip it.
Pipeline: ball cleaning -> touch detection -> touch-to-player attribution -> control test -> spell assembly.

## Signals / inputs
- ATD ball (x,y metres via 105.3x68), 25 fps; 46 anonymous player slots with team and speed (m/s).
- Smart Tagging (638 phases/set pieces) for restart/dead intervals and the post-restart "clear possessor" seed.
- Homography only to sanity-check the pitch bounds (out-of-bounds => dead candidate).
- Touch = ball acceleration/direction-change spike (|a| > ~15 m/s^2 or heading change > 35 deg after 3-frame median filter)
  with a player within ~1.5 m (tracking noise margin). Touch team = team of nearest player.
- Control = same team touches the ball for >= 1.5 s with ball within ~2.5 m of its own player, OR >= 2 consecutive same-team
  touches (a completed pass A->A' with no opponent touch between), OR an opponent-touch chain of >= 2 touches by the new team.
- Interception = opponent touch that *redirects* a ball in flight and is followed by control of that team.

## Ball-missing frames (41%)
Short gaps (<= 1 s): interpolate with a constant-velocity/ballistic fill, flagged low confidence (no touch events created).
Longer gaps: carry current state (persistence is the definition's own default), and use a player-only proxy: if one team's
nearest-player cluster moves toward the last ball position and the opposing team is >5 m from it, keep state. Flip only if the ball
reappears and the control test passes. Never emit D just because the ball is absent. Within a possession, emit X (free on spellF1) only where
confidence is lowest; never X across a suspected transition.

## Dead-ball detection
D when: Smart Tagging marks a set piece/stoppage interval (throw-in, goal kick, corner, free kick, kickoff) and the ball is
near-stationary or players are walking (< 2 m/s mean speed) ; or ball leaves the pitch rectangle (+0.5 m margin) and is
subsequently not tracked inside for >= 2 s; or ball speed < 0.5 m/s for > 3 s with no player within 3 m. Dead run ends at the
first touch after the stoppage or the tag end; that touch seeds a new possession (team from the tag, or nearest player).
Throw-ins have Team=N/A, so use the first-toucher.

## Thresholds without match GT/video
All physically grounded and set once, before any scoring: max human sprint ~ 10-11 m/s, so a ball within 1.5 m of a player and
moving < 12 m/s is plausibly controlled; pass ball speeds 8-30 m/s (shots > 25) separate kicks from dribbles (< 8 m/s); dribble
touch cadence 0.5-1.5 s motivates the 1.5 s dwell; "more than two consecutive passes" is quoted from CHALLENGE.md. Sensitivity
check only on *external* open tracking (e.g. public Metrica sample, licence permitting) - not on this match. Report public-GT
score once, as a correctness check, never to select values.

## Expected gain vs 0.2433
Plausibly 0.30-0.38 spellF1 (+0.06 to +0.14, above the 0.04 noise band if the high end holds). The baseline mostly fails by
inventing possessions on nearest-player flicker; hysteresis via control test cuts count several-fold and dwell logic aligns
spells with the GT's long maximal runs. Tagging-based D gives accurate spell boundaries around stoppages, which spellF1 IoU rewards.
It is a hypothesis, not measured; it should land between a plain hysteresis baseline and an ML approach.

## Biggest risks
1. Touch detection on 25 fps noisy, 59%-visible ball: false/missed touches (aerial balls, crowded boxes).
2. Too-strict control rule => stuck on one team, missing turnovers; too loose => flicker. Both hurt IoU at 0.3-0.7.
3. Many hand-set constants interact; no GT for tuning, so errors cannot be corrected empirically.
4. Tagging reliability for dead intervals (inferred/noisy); N/A team on throw-ins.
5. Anonymous slots: no player continuity, so "same player dwell" must be collective (team proximity).

## Effort
~16-24 h: touch detector 5, control/state machine 6, tag/dead logic 4, gap handling 3, validation/docs 3.

## Rules-compliance verdict
Compliant: fully algorithmic, uses only provided data, physics constants fixed a priori, no hand labels, no training or tuning on
the match/video/public GT (used only once as a correctness check). Needs a RULES.md/mtah-rules-check pass only if external tracking is
used for sensitivity checks.
