# 05 - External-data learned sequence model

## Core idea
Train a small GRU/TCN on open tracking+event data from OTHER matches to emit per-frame H/A/D, with labels derived from external event data by an algorithm. Degrade the external tracking to look like the supplied ATD (ball dropped ~41%, anonymised slots, jitter, ID switches). Run it on the supplied match and decode into spells (hysteresis, min-duration, merge).

## Signals/inputs used
Per frame, from the supplied tactical ATD: the 22 player positions as a permutation-invariant set, sorted or pooled per side. Team side is needed, so the tactical tagging or a clustering step must supply it. Also the ball (x, y, visible flag, time since last seen), player and ball speeds, a "stillness" feature, and optionally Smart Tagging intervals. The input window is about 10 s at 5 Hz, with a bidirectional pass, since offline inference is allowed.

## Ball-missing frames (41%)
Train with the same masking, using block dropout drawn from the real gap-length distribution. That distribution is measured on the unlabelled supplied tracking, which is allowed because it is not label tuning. The network learns to infer possession from player geometry: compactness, who is pressing, and the pack's centroid. A visibility flag and a last-seen embedding are also fed in. Output is carried through gaps by the bidirectional context.

## How dead-ball is detected
The D label is derived externally from event data (out-of-play, foul, goal, kick-off, throw-in, etc., with PFF's explicit ball-in-play and period flags where present). The model learns D from players standing still or walking, formation resets, ball absent, and no ball motion. It is decoded with a minimum D duration of about 2 s.

## Training data
Verify every licence before use. My recall may be out of date.
- **SkillCorner open data**: 10 A-League matches with broadcast-derived tracking (about 10 fps, 105x68 m) and basic events. It is on GitHub and is the best domain match, since it is also camera-derived tracking with missing players. The licence is a custom open-use one, believed to be non-commercial/attribution. I am uncertain.
- **Metrica Sample Games**: 3 games, 25 fps, normalised 0-1 coordinates (rescale to 105x68), full-pitch tracking, events included. GitHub, CC BY-NC 4.0 as I recall. The tracking is clean, so degrade it heavily.
- **PFF FC World Cup 2022**: 64 matches, 29.97 fps, with tracking and rich events including possession events. Delivered by request or form on PFF's site; the licence is non-commercial research and I am unsure of the terms. This is the biggest set, but access may need registration or approval, which could take days.
- **StatsBomb open data**: events only, with no tracking. It is useful for label logic and not for training the model.

Domain gap: normalise coordinates to metres, centre the pitch, and flip direction so the home side attacks left to right. Resample everything to 5 Hz. The supplied data has anonymous slots, so use sets and no IDs. Broadcast-derived tracking differs from optical tracking, so inject jitter, clipped fields of view and swaps. Direct download without registration probably works for Metrica and SkillCorner. No match data or network use is verified here, and I have not checked live downloads.

## Expected spellF1 gain vs 0.2433
Uncertain. My guess is 0.35-0.50 if domain transfer holds, so +0.10 to +0.25. A learned prior on dead-ball and on possession under ball absence should beat heuristics. I cannot support this with measurement. Spell F1 mainly rewards correct turnover boundaries, and a model trained on 13+ matches of event-derived labels may be blurry at those. Post-processing (spell-postprocessing skill) is mandatory.

## Biggest risks
1. Label mismatch. The task defines possession as persistent through contests and changing only on controlled gain. Event data has no such concept, so the rules must be coded from the events (last controlled touch, with carry-over through loose-ball and duel events). The ground truth definition wins, and my derived labels will differ from it. Do not tune that derivation against the public GT.
2. Domain gap and a small number of games. SkillCorner and Metrica together are about 13 games; PFF is more but access is uncertain.
3. Validation only on held-out external games. The public 5 minutes is a sanity check, not a tuning set.
4. Licence ambiguity. Non-commercial licences may conflict with the organisers' redistribution, but RULES.md allows open datasets that organisers can access.

## Effort
About 25-35 h: loaders and normalisation 6, label derivation 6, degradation simulator 4, model and training 6, decoding 3, docs 3, with a buffer for access delays. Add 1-3 days of calendar time if PFF approval is needed.

## Rules-compliance verdict
Compliant. RULES.md explicitly allows external data about other games and models, provided organisers can access them and the technical document describes them. Labels are algorithmic, and nothing is trained or tuned on the provided match or its GT. Open conditions: record each dataset's licence and URL, pin the versions, and keep the weights and training scripts in the repo.
