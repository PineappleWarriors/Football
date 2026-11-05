# Council verdict

Scores are the four critics' 1-10 marks (rules A, upside B, feasibility C, domain D); E (synthesis) gave no scores.

| # | proposal | A | B | C | D | total |
|---|---|---|---|---|---|---|
| 08 | metric-aware semi-Markov DP | 8 | 7 | 9 | 5 | **29** |
| 01 | HMM state machine | 8 | 6 | 7 | 6 | 27 |
| 06 | dead-ball first | 7 | 5 | 7 | 6 | 25 |
| 09 | event pipeline | 9 | 5 | 6 | 5 | 25 |
| 04 | Smart Tagging fusion | 5 | 6 | 7 | 6 | 24 |
| 02 | ball reconstruction | 8 | 3 | 4 | 5 | 20 |
| 03 | team shape | 7 | 2 | 5 | 4 | 18 |
| 05 | external learned model | 5 | 4 | 3 | 6 | 18 |
| 10 | ensemble + abstention | 4 | 4 | 5 | 4 | 17 |
| 07 | video ball detection | 6 | 2 | 2 | 5 | 15 |

## Winner: one pipeline, not one proposal
Decoder from **08** with **01**'s emissions; dead-ball layer from **06** + **04**'s restart anchors;
**09**'s dwell test as the "controlled gain" rule; **03** only as a weak ball-missing cue.
Cut: 05, 07, 10's EM, 02 beyond <=1 s bridging. Module spec: `critiques/E-synthesis.md`.
Build order (C): decoder + flat emission + minimal D rule -> valid CSV first, then 04 anchors, 06 stillness, 03.

## Caveats to carry forward
- All gain estimates are unmeasured. B: any persistence smoother is worth ~+0.04-0.08; extras are inside the 0.04 noise band; team-call accuracy caps results near 0.35.
- Missing ball must be missing evidence, never `D`; and per D, gaps cluster at aerial turnovers, so "hold last state" is risky there.
- Rules (A): fix every constant a priori; no EM/agreement statistics fitted on the match; freeze config before any public-GT run, one scored run per final candidate; verify and tabulate external licences before using any.
- No match data in this container, so nothing here can be scored on the real match yet.
