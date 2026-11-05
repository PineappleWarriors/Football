# Critique A: Rules compliance and legitimacy

Every proposal claims "compliant". Scores are for compliance risk (10 = safest).

| # | Proposal | Score | Reason |
|---|----------|-------|--------|
| 01 | HMM | 8 | Defaults or external fit; licence "check rights" is a guess; switch cost can only be validated by peeking at public GT. |
| 02 | Ball reconstruction | 8 | Physics constants; licences unverified; Kalman Q/R must truly be external-only. |
| 03 | Team shape | 7 | Per-match z-scores fit to the match (unlabelled, benign); licence "as I recall"; falls back to defaults. |
| 04 | Smart-tag fusion | 5 | "Tag-vs-tracking agreement on the full match to weight the prior" is a hidden match fit; proposal admits prior weight "can quietly become match-tuning". |
| 05 | External learned model | 5 | Biggest licence exposure (SkillCorner, Metrica, PFF all "unsure"; PFF needs approval organisers may lack); event-to-possession label derivation invites GT tuning. |
| 06 | Dead-ball first | 7 | External or prior thresholds; "40-45% D" sanity check must not become a tuning target; licences unverified. |
| 07 | Video ball detection | 6 | Local inference fine; AGPL and Roboflow weight licences unchecked; re-masking ATD ball on this match to pick thresholds is grey; derived ball tracks must not be published. |
| 08 | Metric-aware DP | 8 | Synthetic-simulator cost is clean; metric-structure use is legitimate; simulator must not be shaped to public-GT statistics. |
| 09 | Event pipeline | 9 | Physics constants, one GT report; only risk is editing constants after a GT peek. |
| 10 | Ensemble and abstention | 4 | Unsupervised EM on the match is exactly the "self-consistency" path; data-dependent weights; X policy is a high-variance metric bet; licences unverified. |

## Cross-cutting findings
1. **No licence is verified.** All external dataset claims are recalled. Require URL, licence text, version hash and organiser-access check in a LICENCES table in the tech document before any download.
2. **Variant selection on the public window is the real leak.** "Report once" is unenforceable. Freeze the config (commit hash) before the first public-GT run, and run once per final candidate.
3. **Unsupervised EM or self-consistency on the match** is allowed only if no person picks seeds, inits or anchors after seeing results. Fix them in code.
4. **Metric quirks** (X forward-fill, IoU tolerance) are legitimate: they are the documented scorer and AGENTS.md prefers whole spells. Justify abstention by the possession definition too, not only by the quirk.
5. **Reproducibility**: deterministic seeds, pinned weights, no run-time network, data excluded from the repo. Do not publish derived frame-level exports.
6. No proposal uploads match data to AI services; keep 05 and 07 fully local.
