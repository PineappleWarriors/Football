---
name: mtah-rules-check
description: Use before using external data, models or services, before tuning any parameter, or before committing/publishing anything in this challenge repo.
---
# Rules check
Not allowed: checking output against the video; hand labels or corrections on the provided game; uploading provided data to AI services; training/fitting/calibrating on the GT or provided video.
Allowed: inspecting data/video to understand possession; video/tracking/tagging as inputs; external datasets you have rights to (check the license); LLMs as long as the provided data is not uploaded.
Process: (1) name the data and where each tunable parameter comes from; (2) confirm it is external or principled; (3) log it in `docs/TECHNICAL_DOC.md`; (4) if borderline, ask the organisers (hackathon.talentarena@mobileworldcapital.com) before building. Run the `rules-auditor` agent before final submission.
