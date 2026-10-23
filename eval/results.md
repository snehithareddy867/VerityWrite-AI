# VerityWrite evaluation (offline rule-based fallback)

Humanization set: **12 synthetic examples** (9 annotated robotic, 3 annotated natural).
Annotations describe expected handling, not a reference rewrite or independent factual judgment.

## Humanization behavior (descriptive, not a quality-accuracy score)

- Annotated robotic examples with changed output: **9/9**.
- Annotated robotic examples whose verifier returned PASS: **8/9**.
- Annotated natural examples skipped and byte-for-byte unchanged: **3/3**.
- Mean local robotic score for robotic examples: **40.8 -> 11.8**.

These counts do not establish that changed rewrites are good or semantically faithful. There are no human ratings, reference rewrites, or external validation in this evaluation.

## Deterministic verification set

Expected-verdict corpus: **19 synthetic, hand-labeled cases**.
- Exact verdict matches: **19/19**.
- False-positive approvals (expected REVIEW/BLOCKED, actual PASS): **0**.
- False-negative approvals (expected PASS, actual REVIEW/BLOCKED): **0**.

| Expected \\ Actual | PASS | REVIEW | BLOCKED |
|---|---:|---:|---:|
| PASS | 8 | 0 | 0 |
| REVIEW | 0 | 2 | 0 |
| BLOCKED | 0 | 0 | 9 |

| Case | Category | Expected | Actual | Approved by verdict |
|---|---|---|---|---|
| date-equivalent-format | date | PASS | PASS | yes |
| date-changed | date | BLOCKED | BLOCKED | no |
| name-reordered | name | PASS | PASS | yes |
| name-changed | name | BLOCKED | BLOCKED | no |
| score-equivalent-format | score | PASS | PASS | yes |
| score-changed | score | BLOCKED | BLOCKED | no |
| percentage-equivalent-format | percentage | PASS | PASS | yes |
| percentage-changed | percentage | BLOCKED | BLOCKED | no |
| quantity-rephrased | quantity | PASS | PASS | yes |
| quantity-unit-changed | quantity | BLOCKED | BLOCKED | no |
| technical-term-preserved | technical-term | PASS | PASS | yes |
| technical-term-swapped | technical-term | BLOCKED | BLOCKED | no |
| negation-contraction | negation | PASS | PASS | yes |
| negation-reversed | negation | BLOCKED | BLOCKED | no |
| negation-uncertain | negation | REVIEW | REVIEW | no |
| dropped-date | dropped-fact | BLOCKED | BLOCKED | no |
| invented-numeric-claim | invented-claim | BLOCKED | BLOCKED | no |
| shortened-name | name | REVIEW | REVIEW | no |
| harmless-punctuation-and-tone | safe-rewrite | PASS | PASS | yes |

## Deliberate mutation detection

| Corruption | Detected as BLOCKED | Tried |
|---|---:|---:|
| Change a number | 9 | 9 |
| Drop the date | 8 | 8 |
| Swap a technical term | 9 | 9 |
| Invent an achievement | 12 | 12 |

## Humanization examples

| ID | Annotated natural | Result status | Verifier verdict | Robotic score before | after |
|---:|---|---|---|---:|---:|
| 1 | False | fallback | PASS | 32 | 12 |
| 2 | False | fallback | PASS | 48 | 22 |
| 3 | False | fallback | PASS | 44 | 24 |
| 4 | False | fallback | PASS | 48 | 0 |
| 5 | False | fallback | PASS | 36 | 24 |
| 6 | False | fallback | PASS | 46 | 0 |
| 7 | False | fallback | PASS | 29 | 0 |
| 8 | False | fallback | PASS | 48 | 24 |
| 9 | False | fallback | REVIEW | 36 | 0 |
| 10 | True | skipped | PASS | 0 | 0 |
| 11 | True | skipped | PASS | 0 | 0 |
| 12 | True | skipped | PASS | 0 | 0 |

Limitations: both datasets are small and synthetic. Expected verdicts are manually authored examples, not human-subject results. Deterministic checks cannot reliably identify every unsupported qualitative claim or paraphrased contradiction; those require the optional AI judge and/or human review. The local robotic score is not a measure of writing quality.