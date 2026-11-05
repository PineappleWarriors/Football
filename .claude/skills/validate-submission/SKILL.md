---
name: validate-submission
description: Use before delivering or finalising any submission CSV, or when a CSV might have the wrong row count, header, frame order or labels.
---
# Validate submission
`python evaluation/validate_submission.py <file.csv>` - must pass on the exact file to upload.
Contract: header `frame,label`; 199,319 rows; frames 0..199318 in order; labels in H/A/D/X; no blanks. ~164k rows means the broadcast video was indexed.
Name deliverables `<team_name>.csv` and `<team_name>.pdf|md`. Then run the rules-auditor agent.
