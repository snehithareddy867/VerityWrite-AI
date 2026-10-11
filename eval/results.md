# VerityWrite evaluation (offline rule-based fallback)

Test cases: 12 synthetic (9 robotic, 3 already natural)

- Rewrites with all protected facts verified (not blocked): **9/9**
- Already-natural texts correctly left unchanged: **3/3**
- Average robotic score: **41 -> 12**

## Tamper detection (deterministic checks on deliberately corrupted rewrites)

| Corruption | Detected | Tried |
|---|---|---|
| Change a number | 9 | 9 |
| Drop the date | 8 | 8 |
| Swap a technical term | 9 | 9 |
| Invent an achievement | 12 | 12 |

Limitation: invented claims that contain no number, date or name are NOT caught by the deterministic checks; they rely on the AI judge and human review.

## Per-case

| id | context | mode | robotic before | after | verdict | facts kept |
|---|---|---|---|---|---|---|
| 1 | Recruiter feedback | fallback | 32 | 12 | PASS | 7/7 |
| 2 | Recruiter feedback | fallback | 48 | 22 | PASS | 7/7 |
| 3 | Recruiter feedback | fallback | 44 | 24 | PASS | 6/6 |
| 4 | Candidate email | fallback | 48 | 0 | PASS | 6/6 |
| 5 | Candidate email | fallback | 36 | 24 | PASS | 4/4 |
| 6 | Interview question | fallback | 46 | 0 | PASS | 3/3 |
| 7 | Interview question | fallback | 29 | 0 | PASS | 3/3 |
| 8 | Summary | fallback | 48 | 24 | PASS | 6/6 |
| 9 | Report | fallback | 36 | 0 | REVIEW | 6/7 |
| 10 | Recruiter feedback | skipped | 0 | 0 | PASS | 7/7 |
| 11 | Candidate email | skipped | 0 | 0 | PASS | 7/7 |
| 12 | Interview question | skipped | 0 | 0 | PASS | 2/2 |