import json
import pathlib

import pytest

from core.facts import extract_facts
from core.verifier import verify_output

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERIFICATION_CASES = json.loads(
    (ROOT / "data" / "verification_cases.json").read_text(encoding="utf-8")
)


@pytest.mark.parametrize("case", VERIFICATION_CASES, ids=lambda case: case["id"])
def test_synthetic_verification_corpus_matches_expected_verdict(case):
    report = verify_output(
        case["source"],
        extract_facts(case["source"]),
        case["output"],
    )
    assert report.verdict == case["expected_verdict"]
    assert (report.verdict == "PASS") == (case["expected_verdict"] == "PASS")
