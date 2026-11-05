---
name: possession-definition
description: Use when deciding how to label a frame or a transition (H, A, D, X), handling loose balls, deflections, duels, restarts, or ball-missing frames in the possession challenge.
---
# Possession definition
- **H/A**: ball live. Possession stays with the last team that *controlled* it through loose balls, deflections, aerial duels without control.
- **Change** only when an opponent gains *controlled* possession (proxies: keeps ball a few seconds; >2 consecutive passes).
- **D**: ball not in play; a stoppage, never a possession. A restart opens a new possession. `H H D D H H` = two possessions.
- **Ball missing != D and != X.** 41% of graded frames lack the ball.
- GT is mechanical from corrected tracking: D where ball marked dead, else the tracked owner. When your reading and the public GT disagree, GT wins, but do not tune constants to it.
- `X`: free inside a possession (spellF1 forward-fills); harmful at a transition.
Full text: CHALLENGE.md, EVALUATION.md.
