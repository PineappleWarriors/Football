# Graph Report - Football  (2026-11-05)

## Corpus Check
- 44 files · ~33,274 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: .csv 5, (none) 3, .ipynb 3)

## Summary
- 436 nodes · 591 edges · 40 communities (27 shown, 13 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0310cbe7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- games.py
- run_evaluation.py
- OVERVIEW.md
- possession_metrics.py
- FAQ
- numpy
- The challenge
- The data
- Proposal 01: HMM / semi-Markov state machine (Viterbi over whole spells)
- Proposal 02: Ball-trajectory reconstruction, then control detection
- Proposal 03: Ball-free collective team-shape inference
- 04 - Smart-Tagging fusion (priors + tracking)
- 05 - External-data learned sequence model
- 07 - Video ball detection (CV on tactical/broadcast video)
- 09 - Rule-based event pipeline ("controlled possession" state machine)
- More than a Hack 2027 — Phase 1: Ball Possession
- Rules
- Proposal 10: Uncertainty-aware ensemble with deliberate abstention
- bootstrap_macro_f1
- bootstrap_spell_f1
- utils.py
- How you are scored
- Submitting
- Agent guide
- Problem definition
- transition_scores
- possession_spells
- mtah-rules-check/SKILL.md
- possession-definition/SKILL.md
- score-and-compare/SKILL.md
- spell-postprocessing/SKILL.md
- validate-submission/SKILL.md
- EXPERIMENTS.md
- TECHNICAL_DOC.md

## God Nodes (most connected - your core abstractions)
1. `evaluate()` - 21 edges
2. `FAQ` - 21 edges
3. `main()` - 18 edges
4. `require()` - 13 edges
5. `More than a Hack 2027 — Phase 1: Ball Possession` - 11 edges
6. `source_frames()` - 10 edges
7. `Proposal 01: HMM / semi-Markov state machine (Viterbi over whole spells)` - 10 edges
8. `Proposal 02: Ball-trajectory reconstruction, then control detection` - 10 edges
9. `Proposal 03: Ball-free collective team-shape inference` - 10 edges
10. `04 - Smart-Tagging fusion (priors + tracking)` - 10 edges

## Surprising Connections (you probably didn't know these)
- `build()` --calls--> `source_frames()`  [EXTRACTED]
  starter/baseline.py → games.py
- `build()` --calls--> `require()`  [EXTRACTED]
  starter/baseline.py → games.py
- `check_alignment()` --calls--> `source_frames()`  [EXTRACTED]
  starter/load_atd.py → games.py
- `check_alignment_raw()` --calls--> `source_frames()`  [EXTRACTED]
  starter/load_atd.py → games.py
- `check_alignment()` --calls--> `source_frames()`  [EXTRACTED]
  starter/load_homography.py → games.py

## Import Cycles
- None detected.

## Communities (40 total, 13 thin omitted)

### Community 0 - "games.py"
Cohesion: 0.05
Nodes (26): anchor_video_frame(), asset_paths(), frame_offset(), half_of_video_frame(), half_video_blocks(), halves(), id_to_video(), require() (+18 more)

### Community 1 - "run_evaluation.py"
Cohesion: 0.08
Nodes (19): label_codes(), read_label_csv(), competition_ranks(), find_gt(), format_value(), json_safe(), load_meta(), main() (+11 more)

### Community 2 - "OVERVIEW.md"
Cohesion: 0.09
Nodes (23): Nothing in here is committed, Unpack the match data here, You do not need any of this to run the scorer, Put your submissions here, What is already here, Why these are committed and yours will not be, Automatic Tracking Data (ATD), Context (+15 more)

### Community 3 - "possession_metrics.py"
Cohesion: 0.13
Nodes (10): accuracy(), alive_dead_f1(), cohens_kappa(), confusion(), evaluate(), fill_abstentions(), possession_share(), scored_confusion() (+2 more)

### Community 4 - "FAQ"
Cohesion: 0.10
Nodes (21): Are the 5 minutes of ground truth the test set?, Can I hand-label some frames?, Can I submit only the 5 minutes?, Can I train or tune a model on the 5 public minutes?, Can I use LLMs, pre-trained models, external data?, Can I use my own tracking instead of the provided ATD?, Can I use the broadcast video and its tracking?, Can I use the Smart Tagging? Isn't that cheating? (+13 more)

### Community 5 - "numpy"
Cohesion: 0.15
Nodes (8): validate_submission(), build(), nearest_player_labels(), smooth(), team_names(), team_of_each_track(), write_submission(), write_constant()

### Community 6 - "The challenge"
Cohesion: 0.15
Nodes (13): Change of possession, Definition, Deliverables and scoring, Key concepts, Possession rules, Scope: what this challenge is not, The challenge, The four labels (+5 more)

### Community 7 - "The data"
Cohesion: 0.15
Nodes (13): Automatic Tracking Data (ATD), Frame alignment, Getting it, Homography, Smart Tagging, The ball is missing 43% of all frames, and 41% of the graded ones, The broadcast recording, The data (+5 more)

### Community 8 - "Proposal 01: HMM / semi-Markov state machine (Viterbi over whole spells)"
Cohesion: 0.18
Nodes (10): Ball-missing frames (41%), Biggest risks, Core idea, Dead-ball detection, Effort, Expected gain, Parameters WITHOUT match GT/video, Proposal 01: HMM / semi-Markov state machine (Viterbi over whole spells) (+2 more)

### Community 9 - "Proposal 02: Ball-trajectory reconstruction, then control detection"
Cohesion: 0.18
Nodes (10): Biggest risks, Core idea, Effort, Expected spellF1 gain vs 0.2433, How ball-missing frames (41%) are handled, How dead-ball is detected, How parameters are set WITHOUT using match GT/video, Proposal 02: Ball-trajectory reconstruction, then control detection (+2 more)

### Community 10 - "Proposal 03: Ball-free collective team-shape inference"
Cohesion: 0.18
Nodes (10): Ball-missing frames (41%), Biggest risks, Core idea, Dead-ball detection, Effort, Expected spellF1 gain vs 0.2433, Parameters without match GT/video, Proposal 03: Ball-free collective team-shape inference (+2 more)

### Community 11 - "04 - Smart-Tagging fusion (priors + tracking)"
Cohesion: 0.18
Nodes (10): 04 - Smart-Tagging fusion (priors + tracking), Ball-missing frames (41%), Biggest risks, Core idea, Dead-ball detection, Effort, Expected spellF1, Parameters WITHOUT match GT/video (+2 more)

### Community 12 - "05 - External-data learned sequence model"
Cohesion: 0.18
Nodes (10): 05 - External-data learned sequence model, Ball-missing frames (41%), Biggest risks, Core idea, Effort, Expected spellF1 gain vs 0.2433, How dead-ball is detected, Rules-compliance verdict (+2 more)

### Community 13 - "07 - Video ball detection (CV on tactical/broadcast video)"
Cohesion: 0.18
Nodes (10): 07 - Video ball detection (CV on tactical/broadcast video), Ball-missing frames, Biggest risks, Core idea, Effort and compute, Expected spellF1 gain vs 0.2433, Parameters without match GT, Pretrained models and licences (+2 more)

### Community 14 - "09 - Rule-based event pipeline ("controlled possession" state machine)"
Cohesion: 0.18
Nodes (10): 09 - Rule-based event pipeline ("controlled possession" state machine), Ball-missing frames (41%), Biggest risks, Core idea, Dead-ball detection, Effort, Expected gain vs 0.2433, Rules-compliance verdict (+2 more)

### Community 15 - "More than a Hack 2027 — Phase 1: Ball Possession"
Cohesion: 0.18
Nodes (11): Getting the data, Licence and citation, More than a Hack 2027 — Phase 1: Ball Possession, Questions, Read these, in this order, Requirements, The challenge in one screen, The task (+3 more)

### Community 16 - "Rules"
Cohesion: 0.18
Nodes (11): 1. Annotate the data by hand, 2. Use the private ground truth, or any human-produced data about the game, 3. Submit a file your repository cannot regenerate, Eligibility and teams, Questions, Rules, The data, The provided data is a starting point, not a constraint (+3 more)

### Community 17 - "Proposal 10: Uncertainty-aware ensemble with deliberate abstention"
Cohesion: 0.20
Nodes (9): Biggest risks, Core idea, Effort (hours), Expected spellF1 gain vs 0.2433 and why, How ball-missing frames are handled, How calibration/weights are set WITHOUT match GT/video, Proposal 10: Uncertainty-aware ensemble with deliberate abstention, Rules-compliance verdict (+1 more)

### Community 18 - "bootstrap_macro_f1"
Cohesion: 0.20
Nodes (5): bootstrap_macro_f1(), fragmentation(), macro_f1(), per_class_prf(), segments()

### Community 19 - "bootstrap_spell_f1"
Cohesion: 0.22
Nodes (5): bootstrap_spell_f1(), match_spells(), matched_gt_flags(), spell_overlaps(), spell_scores()

### Community 20 - "utils.py"
Cohesion: 0.27
Nodes (5): animate_frames(), positions(), update(), draw_pitch(), plot_frame()

### Community 21 - "How you are scored"
Cohesion: 0.22
Nodes (9): How an abstention is scored, How you are scored, macroF1 — right label, right frame, Run it yourself, See the disagreement for yourself, spellF1 — right possessions, The definitions are in the code, The public window is not a leaderboard (+1 more)

### Community 22 - "Submitting"
Cohesion: 0.22
Nodes (9): 1. The possession file, 2. A public code repository, 3. A technical document, Check it before you send it, How to submit, Rules, Submitting, The possession file (+1 more)

### Community 23 - "Agent guide"
Cohesion: 0.25
Nodes (7): Agent guide, Constraints, Objective, Priorities, Project setup (Jared_Dev), Repository workflow, Required checks

### Community 24 - "Problem definition"
Cohesion: 0.25
Nodes (7): Hard rules (organiser clarification supersedes everything else), Inputs (all automatic and noisy), Metric, Open questions to resolve first, Plan, Problem definition, Task

### Community 25 - "transition_scores"
Cohesion: 0.25
Nodes (3): _count_ambiguous(), match_transitions(), transition_scores()

### Community 26 - "possession_spells"
Cohesion: 0.25
Nodes (4): possession_spells(), possession_stats(), valid_runs(), describe()

## Knowledge Gaps
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FAQ` connect `FAQ` to `OVERVIEW.md`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Should `games.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05027322404371585 - nodes in this community are weakly interconnected._
- **Why does `The data` connect `The data` to `OVERVIEW.md`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Should `run_evaluation.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07822410147991543 - nodes in this community are weakly interconnected._
- **Why does `The challenge` connect `The challenge` to `OVERVIEW.md`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Should `OVERVIEW.md` be split into smaller, more focused modules?**
  _Cohesion score 0.09090909090909091 - nodes in this community are weakly interconnected._
- **Should `possession_metrics.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12987012987012986 - nodes in this community are weakly interconnected._