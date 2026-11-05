# Problem definition

**More Than A Hack 2027, Initial Challenge.** Deadline **17 Nov 2026, 23:59 CET**. Top 20 teams
advance to the Innovation Challenge. All members must register under the same team name.

## Task
For each of 199,319 frames (25 fps) of FC Barcelona (H) v Athletic Club (A), output `H`, `A`, `D` or `X`.
Only 158,857 frames are graded (1st half 11185-90651, 2nd half 110808-190197).

| label | meaning |
|---|---|
| H / A | team in possession, ball live (persists through loose balls/deflections; changes only on *controlled* gain by the opponent) |
| D | ball not in play (stoppage, never a possession) |
| X | abstain. macroF1: a miss. spellF1: forward-filled with last label in the half |

## Metric
Rank = **spellF1** (possession-level temporal IoU, mean over 0.3-0.7); tie-break **macroF1**.
Floor to beat: `baseline_smooth50` spellF1 **0.2433** (full match). Noise bands: spellF1 ~0.04, macroF1 ~0.01.
Public GT covers only frames 11185-18684 (17 possessions): use it to check correctness, never to tune.

## Inputs (all automatic and noisy)
Tactical-video ATD tracking (46 anonymous slots, ball missing on 41% of graded frames), Smart Tagging
(638 phases/set pieces, `Team` is N/A for all throw-ins), homography (100% valid), broadcast feed
(unsynchronised, optional). Data is gated and gitignored; unpack into `data/` or set `MTAH_DATA_DIR`.

## Hard rules (organiser clarification supersedes everything else)
Not allowed: checking output against the video; hand labels or hand-corrected data on the provided game;
uploading the provided data to AI services; training/fitting/calibrating on the public GT or the provided video.
Allowed: automatic checks on provided data; inspecting data/video to understand possession; any input
(video, tracking, tagging) so long as the algorithm was not trained on GT/provided video; external datasets
you have rights to. Any training or tuning must use **external data only**.
Deliverables: `<team>.csv`, public code repo (reproduces the same file; no match data in it), `<team>.pdf|md`.

## Open questions to resolve first
1. **Tuning without GT/video.** With the above rules, how do we choose hyperparameters? Options: external
   tracking datasets (e.g. public Metrica/SkillCorner samples, license check), or parameter-free/physically
   motivated settings. Ask organisers if a rule is borderline.
2. **Ball-missing frames (41%).** Infer ball from player configuration / Smart Tagging, vs hold last state.
3. **Dead-ball detection** from ball-missing + player stillness + Smart Tagging set-piece intervals.
4. **Controlled-possession proxy** (e.g. >= N s contact by same team) and hysteresis for turnovers.
5. Use of `X` inside possessions (free under spellF1) vs at transitions (harmful).

## Plan
Phase 0 setup (done) -> Phase 1 live/dead (D vs alive) -> Phase 2 team assignment while alive ->
Phase 3 spell-level post-processing (merge/min-duration/hysteresis) -> Phase 4 reproducibility + tech doc.
Report for every experiment: spellF1, macroF1, possession count, mean duration (see `docs/EXPERIMENTS.md`).
