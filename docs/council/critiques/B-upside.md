# Critique B: realism of claimed spellF1 gains

Floor 0.2433, noise 0.04. Nothing was measured; seven of ten claim ~0.30-0.40, which looks like anchoring.

## What actually drives spellF1
1. **Spell count/duration realism.** raw 0.05 -> smooth50 0.24 shows fragmentation is the dominant loss. Any competent hysteresis/min-duration/merge layer captures most of the cheap gain. Expect a common persistence gain of +0.04 to +0.08 for any method.
2. **Boundary timing.** 1 s late = 0.65x. Turnover onset is uncertain by seconds from nearest-player/shape signals, so IoU at 0.6-0.7 mostly fails. Restarts (tags) are the only sharp anchors.
3. **D splitting possessions.** A stray D inside a live run adds an FP and kills IoU. Fixing D false positives is worth more than adding D true positives.
4. **Team-call accuracy** caps everything; a decoder cannot create turnovers the signal never saw. Realistic ceiling about 0.35.

## Scores

| # | Proposal | Claimed | My range | Upside /10 | Main inflation |
|---|---|---|---|---|---|
| 01 | HMM semi-Markov | 0.32-0.40 | 0.28-0.35 | 6 | Emissions hand-set |
| 02 | Ball reconstruction | 0.30-0.36 | 0.25-0.30 | 3 | Proposer admits fragmentation, not coverage, is the loss; player-pull for long gaps is weak |
| 03 | Team shape | 0.26-0.30 | 0.24-0.28 | 2 | Shape lags ball by seconds; only a gap-filler |
| 04 | Tag fusion | 0.30-0.38 | 0.28-0.35 | 6 | Tags give sharp boundaries but only 59 set pieces; throw-in team N/A |
| 05 | External learned model | 0.35-0.50 | 0.22-0.38 | 4 | Highest variance; label derivation mismatches GT definition; 0.50 is fantasy |
| 06 | Dead-ball first | 0.33-0.40 | 0.27-0.34 | 5 | Team assignment stays baseline quality; missed fast restarts |
| 07 | Video ball | 0.26-0.30 | 0.24-0.29 | 2 | Self-rated within noise; GPU/time infeasible |
| 08 | Metric-aware DP | 0.30-0.36 | 0.29-0.35 | 7 | Best cost/benefit; over-merging loses at IoU 0.7 |
| 09 | Event pipeline | 0.30-0.38 | 0.25-0.34 | 5 | Many interacting constants, no GT; touch detection on 59%-visible 25 fps ball is shaky |
| 10 | Ensemble + abstention | 0.30-0.38 | 0.27-0.34 | 4 | X-in-gaps adds ~0 to spellF1 (own admission) and costs macroF1; EM on correlated estimators overstates confidence |

## Cross-cutting inflation
- 01, 04, 06, 08, 10 share "HMM + persistence + tags": one family, not five independent bets; gains are sub-additive.
- Quoted "+0.06 to +0.14" mixes the persistence gain any smoother gets with the proposal's novelty (typically +0.01-0.04, inside noise).
- Public GT has ~17 spells, so +0.03 differences are untestable pre-submission.

## Recommendation
Build 08's decoder with 04's tag-anchored D; 02, 03, 07 are optional add-ons; 05 is a high-variance lottery ticket.
