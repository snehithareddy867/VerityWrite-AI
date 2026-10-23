"""Run the synthetic evaluation; pass --offline to avoid Gemini/API calls.

The deterministic verifier set has expected verdict labels. Humanization examples
have no gold rewrites, so their text-quality measurements are descriptive only.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load_cases(path: pathlib.Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Do not load .env or use Gemini; evaluate with deterministic fallback only.",
    )
    args = parser.parse_args()

    if not args.offline:
        try:
            from dotenv import load_dotenv
            load_dotenv(ROOT / ".env")
        except ImportError:
            pass
    else:
        os.environ["PYTHON_DOTENV_DISABLED"] = "1"

    from core.analyzer import analyze
    from core.facts import extract_facts
    from core.llm import LLMClient
    from core.mutate import MUTATIONS
    from core.pipeline import humanize
    from core.verifier import verify_output

    llm = LLMClient("" if args.offline else os.getenv("GEMINI_API_KEY"))
    cases = load_cases(ROOT / "data" / "test_cases.json")
    verification_cases = load_cases(ROOT / "data" / "verification_cases.json")
    engine = "offline rule-based fallback" if not llm.available else f"Gemini ({llm.model})"

    robotic_cases = [case for case in cases if not case["already_natural"]]
    natural_cases = [case for case in cases if case["already_natural"]]
    natural_unchanged = robotic_changed = robotic_pass = 0
    before, after = [], []
    tamper = {name: [0, 0] for name in MUTATIONS}
    humanization_rows = []

    for case in cases:
        result = humanize(case["text"], case["context"], case["tone"], llm)
        if case["already_natural"]:
            natural_unchanged += (
                result.mode == "skipped"
                and result.output == case["text"]
                and result.status == "skipped"
            )
        else:
            robotic_changed += result.output != case["text"]
            robotic_pass += result.report.verdict == "PASS"
            before.append(result.analysis.score)
            after.append(analyze(result.output).score)

        for name, mutation in MUTATIONS.items():
            corrupted = mutation(result.output)
            if corrupted is None:
                continue
            tamper[name][1] += 1
            tamper[name][0] += (
                verify_output(case["text"], result.facts, corrupted).verdict == "BLOCKED"
            )
        humanization_rows.append(
            f"| {case['id']} | {case['already_natural']} | {result.status} | "
            f"{result.report.verdict} | {result.analysis.score} | {analyze(result.output).score} |"
        )

    confusion = {
        expected: {actual: 0 for actual in ("PASS", "REVIEW", "BLOCKED")}
        for expected in ("PASS", "REVIEW", "BLOCKED")
    }
    exact_verdicts = false_positive_approvals = false_negative_approvals = 0
    verification_rows = []
    for case in verification_cases:
        facts = extract_facts(case["source"])
        report = verify_output(case["source"], facts, case["output"])
        actual = report.verdict
        expected = case["expected_verdict"]
        confusion[expected][actual] += 1
        exact_verdicts += actual == expected
        expected_approved = expected == "PASS"
        actual_approved = actual == "PASS"
        false_positive_approvals += actual_approved and not expected_approved
        false_negative_approvals += expected_approved and not actual_approved
        verification_rows.append(
            f"| {case['id']} | {case['category']} | {expected} | {actual} | "
            f"{'yes' if actual_approved else 'no'} |"
        )

    lines = [
        f"# VerityWrite evaluation ({engine})",
        "",
        f"Humanization set: **{len(cases)} synthetic examples** "
        f"({len(robotic_cases)} annotated robotic, {len(natural_cases)} annotated natural).",
        "Annotations describe expected handling, not a reference rewrite or independent factual judgment.",
        "",
        "## Humanization behavior (descriptive, not a quality-accuracy score)",
        "",
        f"- Annotated robotic examples with changed output: **{robotic_changed}/{len(robotic_cases)}**.",
        f"- Annotated robotic examples whose verifier returned PASS: **{robotic_pass}/{len(robotic_cases)}**.",
        f"- Annotated natural examples skipped and byte-for-byte unchanged: **{natural_unchanged}/{len(natural_cases)}**.",
        f"- Mean local robotic score for robotic examples: **{statistics.mean(before):.1f} -> "
        f"{statistics.mean(after):.1f}**.",
        "",
        "These counts do not establish that changed rewrites are good or semantically faithful. "
        "There are no human ratings, reference rewrites, or external validation in this evaluation.",
        "",
        "## Deterministic verification set",
        "",
        f"Expected-verdict corpus: **{len(verification_cases)} synthetic, hand-labeled cases**.",
        f"- Exact verdict matches: **{exact_verdicts}/{len(verification_cases)}**.",
        f"- False-positive approvals (expected REVIEW/BLOCKED, actual PASS): **{false_positive_approvals}**.",
        f"- False-negative approvals (expected PASS, actual REVIEW/BLOCKED): **{false_negative_approvals}**.",
        "",
        "| Expected \\\\ Actual | PASS | REVIEW | BLOCKED |",
        "|---|---:|---:|---:|",
    ]
    for expected in ("PASS", "REVIEW", "BLOCKED"):
        lines.append(
            f"| {expected} | {confusion[expected]['PASS']} | {confusion[expected]['REVIEW']} | "
            f"{confusion[expected]['BLOCKED']} |"
        )

    lines += [
        "",
        "| Case | Category | Expected | Actual | Approved by verdict |",
        "|---|---|---|---|---|",
        *verification_rows,
        "",
        "## Deliberate mutation detection",
        "",
        "| Corruption | Detected as BLOCKED | Tried |",
        "|---|---:|---:|",
    ]
    for name, (detected, tried) in tamper.items():
        lines.append(f"| {name} | {detected} | {tried} |")

    lines += [
        "",
        "## Humanization examples",
        "",
        "| ID | Annotated natural | Result status | Verifier verdict | Robotic score before | after |",
        "|---:|---|---|---|---:|---:|",
        *humanization_rows,
        "",
        "Limitations: both datasets are small and synthetic. Expected verdicts are manually authored "
        "examples, not human-subject results. Deterministic checks cannot reliably identify every "
        "unsupported qualitative claim or paraphrased contradiction; those require the optional AI "
        "judge and/or human review. The local robotic score is not a measure of writing quality.",
    ]
    report_text = "\n".join(lines)
    (ROOT / "eval" / "results.md").write_text(report_text, encoding="utf-8")
    print(report_text)


if __name__ == "__main__":
    main()
