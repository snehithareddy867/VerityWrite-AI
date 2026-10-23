import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest

from core.facts import extract_facts
from core.llm import LLMError
from core.verifier import verify_output
from core.analyzer import analyze
from core.pipeline import MAX_RETRIES, humanize
from core.samples import SAMPLES
from core import mutate

SRC = SAMPLES["Recruiter feedback (robotic)"]["text"]


def keys(text):
    return {(f.kind, f.key) for f in extract_facts(text)}


def test_extracts_scores_dates_names_terms():
    k = keys(SRC)
    assert ("score", "score:82/100") in k and ("score", "score:74/100") in k
    assert ("date", "date:8-10-2026") in k
    assert ("name", "name:asha rao") in k
    assert ("term", "term:python") in k and ("term", "term:sql query optimization") in k


def test_out_of_equals_slash_score():
    assert ("score", "score:7.5/10") in keys("He got 7.5 out of 10") and ("score", "score:7.5/10") in keys("He got 7.5/10")


def test_date_formats_normalise():
    a = [f.meta for f in extract_facts("on 8 October 2026") if f.kind == "date"]
    b = [f.meta for f in extract_facts("on October 8, 2026") if f.kind == "date"]
    c = [f.meta for f in extract_facts("on 2026-10-08") if f.kind == "date"]
    assert a == b == c == [(8, 10, 2026)]


def test_identical_text_passes():
    assert verify_output(SRC, extract_facts(SRC), SRC).verdict == "PASS"


def test_reordered_date_still_passes():
    out = SRC.replace("on 8 October 2026", "on October 8, 2026")
    assert verify_output(SRC, extract_facts(SRC), out).verdict == "PASS"


def test_changed_score_is_blocked_and_reported_as_changed():
    out = SRC.replace("82/100", "92/100")
    r = verify_output(SRC, extract_facts(SRC), out)
    assert r.verdict == "BLOCKED"
    assert any(i.status == "changed" and i.source == "82/100" and i.output == "92/100" for i in r.items)


def test_dropped_date_blocked():
    out = mutate.drop_date(SRC)
    assert verify_output(SRC, extract_facts(SRC), out).verdict == "BLOCKED"


def test_swapped_term_blocked():
    out = mutate.swap_term(SRC)
    assert verify_output(SRC, extract_facts(SRC), out).verdict == "BLOCKED"


def test_invented_number_claim_blocked():
    out = mutate.add_numeric_claim(SRC)
    assert verify_output(SRC, extract_facts(SRC), out).verdict == "BLOCKED"


def test_shortened_name_is_warning_not_block():
    out = SRC.replace("Asha Rao", "Asha")
    assert verify_output(SRC, extract_facts(SRC), out).verdict == "REVIEW"


@pytest.mark.parametrize(
    ("source", "output", "expected"),
    [
        ("Meeting is on 8 October 2026.", "Meeting is on 2026-10-08.", "PASS"),
        ("Meeting is on 8 October 2026.", "Meeting is on 9 October 2026.", "BLOCKED"),
        ("Asha Rao completed Python training.", "Asha Sen completed Python training.", "BLOCKED"),
        ("Rao Asha completed Python training.", "Asha Rao completed Python training.", "PASS"),
        ("Conversion increased by 12 percent.", "Conversion increased by 12%.", "PASS"),
        ("Conversion increased by 12%.", "Conversion increased by 15%.", "BLOCKED"),
        ("The team reviewed 5 reports.", "A total of 5 reports were reviewed.", "PASS"),
        ("The team reviewed 5 reports.", "The team reviewed 5 emails.", "BLOCKED"),
        ("She used Python for analysis.", "She used Java for analysis.", "BLOCKED"),
        ("Asha did not complete the report.", "Asha didn't complete the report.", "PASS"),
        ("Asha did not complete the report.", "Asha did complete the report.", "BLOCKED"),
        ("Asha did not complete the report.", "The report remains pending.", "REVIEW"),
        ("The system is not only fast but reliable.", "The system is fast and reliable.", "PASS"),
        ("The candidate scored 82/100.", "The candidate scored 82/100 and led 10 people.", "BLOCKED"),
        ("The candidate scored 82/100 on 8 October 2026.", "The candidate scored 82/100.", "BLOCKED"),
        ("The team reviewed 5 reports.", "The team reviewed reports.", "BLOCKED"),
        ("Asha Rao reviewed 5 reports.", "Asha Rao reviewed five reports.", "PASS"),
    ],
)
def test_fact_and_meaning_verification_cases(source, output, expected):
    assert verify_output(source, extract_facts(source), output).verdict == expected


def test_pipeline_does_not_approve_negation_reversal(monkeypatch):
    import core.pipeline as pipeline

    source = "Asha did not complete the report."

    class AvailableLLM:
        available = True

    monkeypatch.setattr(pipeline, "rewrite_llm", lambda *args, **kwargs: "Asha did complete the report.")
    result = humanize(
        source,
        "Recruiter feedback",
        "Professional",
        AvailableLLM(),
        use_skip_gate=False,
        use_judge=False,
        max_retries=0,
    )

    assert result.report.verdict == "BLOCKED"
    assert not result.approved


def test_analyzer_robotic_vs_natural():
    assert analyze(SRC).score >= 25
    assert analyze(SAMPLES["Already natural (skip-gate test)"]["text"]).score < 25


def test_skip_gate_leaves_natural_text_unchanged():
    s = SAMPLES["Already natural (skip-gate test)"]
    r = humanize(s["text"], s["context"], s["tone"], None)
    assert r.mode == "skipped" and r.output == s["text"]


def test_pipeline_fallback_preserves_facts():
    for k, s in SAMPLES.items():
        r = humanize(s["text"], s["context"], s["tone"], None)
        assert r.approved, k


def test_approval_requires_pass_and_fallback_pass_remains_eligible():
    sample = SAMPLES["Recruiter feedback (robotic)"]
    result = humanize(sample["text"], sample["context"], sample["tone"], None, use_judge=False)

    assert result.mode == "fallback"
    assert result.report.verdict == "PASS"
    assert result.approved


def test_review_warning_requires_human_review_and_is_not_approved(monkeypatch):
    import core.pipeline as pipeline

    sample = SAMPLES["Recruiter feedback (robotic)"]
    shortened_name = sample["text"].replace("Asha Rao", "Asha")
    monkeypatch.setattr(pipeline, "rewrite_fallback", lambda _text: shortened_name)
    result = humanize(
        sample["text"],
        sample["context"],
        sample["tone"],
        None,
        use_skip_gate=False,
        use_judge=False,
        max_retries=0,
    )

    assert result.output == shortened_name
    assert result.report.verdict == "REVIEW"
    assert not result.approved
    assert any("Human review required" in note for note in result.notes)


def test_ai_judge_meaning_warning_prevents_approval(monkeypatch):
    import core.pipeline as pipeline

    sample = SAMPLES["Recruiter feedback (robotic)"]

    class AvailableLLM:
        available = True

    monkeypatch.setattr(pipeline, "rewrite_llm", lambda *args, **kwargs: sample["text"])
    monkeypatch.setattr(
        pipeline,
        "judge",
        lambda *args, **kwargs: {
            "meaning_preserved": False,
            "added_claims": [],
            "removed_claims": [],
            "notes": "Meaning may have shifted.",
        },
    )

    result = humanize(sample["text"], sample["context"], sample["tone"], AvailableLLM())

    assert result.report.verdict == "REVIEW"
    assert not result.approved
    assert any("Human review required" in note for note in result.notes)


def test_blocked_fact_failure_prevents_approval(monkeypatch):
    import core.pipeline as pipeline

    sample = SAMPLES["Recruiter feedback (robotic)"]
    altered = sample["text"].replace("82/100", "92/100")
    monkeypatch.setattr(pipeline, "rewrite_fallback", lambda _text: altered)

    result = humanize(sample["text"], sample["context"], sample["tone"], None, use_judge=False)

    assert result.report.verdict == "BLOCKED"
    assert not result.approved
    assert any("NOT approved or verified" in note for note in result.notes)


def test_retry_ending_in_review_is_not_approved(monkeypatch):
    import core.pipeline as pipeline

    sample = SAMPLES["Recruiter feedback (robotic)"]
    retry_outputs = iter((
        sample["text"].replace("82/100", "92/100"),
        sample["text"].replace("Asha Rao", "Asha"),
    ))

    class AvailableLLM:
        available = True

    monkeypatch.setattr(pipeline, "rewrite_llm", lambda *args, **kwargs: next(retry_outputs))
    result = humanize(
        sample["text"],
        sample["context"],
        sample["tone"],
        AvailableLLM(),
        use_judge=False,
        max_retries=1,
    )

    assert result.attempts == 2
    assert result.report.verdict == "REVIEW"
    assert not result.approved


class AvailableLLM:
    available = True


def test_successful_mocked_gemini_rewrite_is_verified_and_reported(monkeypatch):
    import core.pipeline as pipeline

    source = "The candidate, Asha Rao, scored 82/100 in Python. The candidate demonstrated Python skills."
    rewritten = "Asha Rao scored 82/100 in Python and demonstrated Python skills."
    monkeypatch.setattr(pipeline, "rewrite_llm", lambda *args, **kwargs: rewritten)

    result = humanize(
        source, "Recruiter feedback", "Professional", AvailableLLM(),
        use_skip_gate=False, use_judge=False,
    )

    assert result.output == rewritten
    assert result.mode == "gemini"
    assert result.status == "rewritten"
    assert result.report.verdict == "PASS"
    assert result.approved


def test_failed_verification_then_successful_retry(monkeypatch):
    import core.pipeline as pipeline

    outputs = iter((
        SRC.replace("82/100", "92/100"),
        SRC.replace("The candidate, Asha Rao,", "Asha Rao,"),
    ))
    monkeypatch.setattr(pipeline, "rewrite_llm", lambda *args, **kwargs: next(outputs))

    result = humanize(
        SRC, "Recruiter feedback", "Professional", AvailableLLM(),
        use_skip_gate=False, use_judge=False, max_retries=1,
    )

    assert result.attempts == 2
    assert result.report.verdict == "PASS"
    assert result.approved
    assert any("retrying with feedback" in note for note in result.notes)


def test_api_error_uses_verified_fallback_without_claiming_gemini_success(monkeypatch):
    import core.pipeline as pipeline

    def fail_rewrite(*args, **kwargs):
        raise LLMError("Gemini call failed: service unavailable")

    monkeypatch.setattr(pipeline, "rewrite_llm", fail_rewrite)
    result = humanize(
        SRC, "Recruiter feedback", "Professional", AvailableLLM(),
        use_skip_gate=False, use_judge=False,
    )

    assert result.mode == "fallback"
    assert result.status == "fallback"
    assert result.report.verdict == "PASS"
    assert result.approved
    assert any("Gemini rewrite failed" in note for note in result.notes)
    assert not any("Gemini (" in note or "AI-humanized" in note for note in result.notes)


def test_fallback_candidate_is_verified_before_approval(monkeypatch):
    import core.pipeline as pipeline

    unsafe = SRC.replace("82/100", "92/100")
    monkeypatch.setattr(pipeline, "rewrite_fallback", lambda _text: unsafe)
    result = humanize(SRC, "Recruiter feedback", "Professional", None, use_judge=False)

    assert result.mode == "fallback"
    assert result.report.verdict == "BLOCKED"
    assert not result.approved


def test_retry_limit_is_bounded_and_exhaustion_is_not_approved(monkeypatch):
    import core.pipeline as pipeline

    calls = []
    unsafe = SRC.replace("82/100", "92/100")

    def always_fail_verification(*args, **kwargs):
        calls.append(1)
        return unsafe

    monkeypatch.setattr(pipeline, "rewrite_llm", always_fail_verification)
    result = humanize(
        SRC, "Recruiter feedback", "Professional", AvailableLLM(),
        use_skip_gate=False, use_judge=False, max_retries=1000,
    )

    assert MAX_RETRIES == 2
    assert len(calls) == result.attempts == MAX_RETRIES + 1
    assert result.report.verdict == "BLOCKED"
    assert not result.approved
    assert any("retry limit reached" in note for note in result.notes)


def test_negative_retry_count_still_runs_one_verified_attempt(monkeypatch):
    import core.pipeline as pipeline

    calls = []
    monkeypatch.setattr(pipeline, "rewrite_llm", lambda *args, **kwargs: calls.append(1) or SRC)
    result = humanize(
        SRC, "Recruiter feedback", "Professional", AvailableLLM(),
        use_skip_gate=False, use_judge=False, max_retries=-10,
    )

    assert len(calls) == result.attempts == 1
    assert result.report.verdict == "PASS"
    assert result.approved


def test_unchanged_fallback_is_reported_as_original_not_rewrite(monkeypatch):
    import core.pipeline as pipeline

    monkeypatch.setattr(pipeline, "rewrite_fallback", lambda text: text)
    result = humanize(
        SRC, "Recruiter feedback", "Professional", None,
        use_skip_gate=False, use_judge=False,
    )

    assert result.output == result.original
    assert result.unchanged
    assert result.status == "unchanged"
    assert result.report.verdict == "PASS"
    assert any("original text is shown unchanged" in note for note in result.notes)
