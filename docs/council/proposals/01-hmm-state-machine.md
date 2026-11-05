# Proposal 01: HMM / semi-Markov state machine (Viterbi over whole spells)

## Core idea
Replace "smooth a noisy per-frame label" with one joint decode. Latent state per frame s in {H, A, D}; D has sub-states D_stop (stoppage) and D_restart-lead. Decode with Viterbi on 5 Hz downsampled frames (then upsample to 25 fps), maximising
sum_t log p(e_t | s_t) + sum_t log P(s_t | s_{t-1}, dwell) with an explicit duration prior (semi-Markov: dwell ~ Gamma/log-normal, median ~10 s for H/A, ~30 s for D). Switch costs are asymmetric: H<->A requires evidence of *controlled* gain by the opponent (>= ~1 s of nearest-player dominance), costing about -log(1/2000) per switch at 5 Hz; H/A->D is cheap when ball is missing AND players are static/walking; D->H/A requires a restart signature. The cost lattice itself yields whole spells, which is what spellF1 rewards (baseline_raw 0.05 vs smooth50 0.24).

## Signals/inputs
Per frame: d_H, d_A = min metre distance (pitch 105.3x68) of home/away players to ball; ball-visible flag; ball speed; ball-in-bounds (homography/normalised coords); mean outfield player speed; fraction of players "settled" (<1 m/s); team-centroid compression; Smart Tagging set-piece/phase intervals (automatic, provided) as a D prior. Emission for H/A when ball seen: logistic in (d_H - d_A), saturating, flat when both > 5 m (loose ball => no evidence, state persists).

## Ball-missing frames (41%)
Treated as *missing emissions*, not D. Emission is marginalised: p(e|s) uses only player-configuration features (centroid shift toward a goal, line compression, which team's players are moving ball-ward). The transition prior then carries the last possession through gaps, matching "persistence through loose balls". Gaps inside a spell cost nothing; gaps cannot flip a spell unless player-only evidence is strong for >3 s. Output H/A (not X) because the decoder is already persistent.

## Dead-ball detection
D emission = low mean player speed + players dispersed/static (set-piece formations, e.g. spread of walking + one player near ball), ball out of bounds or missing >~3 s while players are slow, plus Smart Tagging set-piece/stoppage tags as a prior boost. D->live needs a restart pattern: ball speed spike or a player near ball with others accelerating. Min D dwell ~3 s (duration prior) to avoid chattering.

## Parameters WITHOUT match GT/video
(1) Principled defaults: 25 fps, ~1 s controlled-contact, football-domain durations above, stated in the tech doc. (2) Optional fitting on external data only: public Metrica Sports sample games (open, CC-BY-NC-style licence, check rights) and SkillCorner open data, which ship tracking + events; Baum-Welch/EM or grid search of ~6 scalars (emission slope, switch cost, D dwell) on those, with the *possession-spell metric* computed from their event data. Honest caveat: their tracking is cleaner and ball-complete, so I would degrade it (drop ball for 41% in random 1-5 s gaps, add noise) to mimic ATD. No tuning on the public 5-min GT, only a pipeline-correctness check.

## Expected gain
Expect spellF1 ~0.32-0.40 versus 0.2433 (guess, not measured): turns equals fewer, longer spells; baseline's weakness is per-frame hard decisions plus D=ball-missing. Gain is mostly from not breaking spells at ball dropouts and not inserting spurious D. Within noise band (0.04) of other approaches unless emissions improve.

## Biggest risks
Hand-set emission scales are mis-calibrated for ATD noise; external-data domain shift; D detection is the weakest emission (macroF1 may suffer); Viterbi smooths away real quick turnovers (short spells still count as separate objects in spellF1); mis-set switch cost trades missed vs spurious spells and cannot be validated on 17 public possessions.

## Effort
~16-20 h: loader + features 4 h, decoder 4 h, external-data degrade/fit harness 6 h, docs/validation 3 h.

## Rules-compliance verdict
Compliant: fully algorithmic, deterministic, no hand labels, no GT or provided-video fitting; external data used only if licence verified and documented (RULES.md: organisers must access it). Default-only variant (no fitting) is zero-risk fallback.
