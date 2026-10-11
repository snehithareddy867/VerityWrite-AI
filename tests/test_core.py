import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from core.facts import extract_facts
from core.verifier import verify_output
from core.analyzer import analyze
from core.pipeline import humanize
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
