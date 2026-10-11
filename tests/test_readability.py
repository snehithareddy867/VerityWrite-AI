import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from core.readability import (METRICS, analyze_readability, count_syllables, band_for_score,
                              level_for_grade, audience_for_grade, scores_as_text)
from core.readview import dashboard_html
from core.samples import SAMPLES

SIMPLE = "The cat sat on the mat. The dog ran to the park. We like to play. It is fun."
HARD = ("Notwithstanding considerable organisational heterogeneity, the interdisciplinary committee "
        "recommended comprehensive reconsideration of administrative methodologies throughout the institution.")


def test_counts():
    r = analyze_readability("One two three. Four five?\n\nSix.")
    assert (r.words, r.sentences, r.paragraphs) == (6, 3, 2)


def test_syllables():
    assert count_syllables("cat") == 1 and count_syllables("water") == 2 and count_syllables("readability") == 5


def test_empty_text_is_safe():
    r = analyze_readability("")
    assert r.words == 0 and r.scores == {} and r.overall == 0.0
    assert "Multi-Readability Suite" in dashboard_html(r, r, [])


def test_simple_is_easier_than_hard():
    a, b = analyze_readability(SIMPLE), analyze_readability(HARD)
    assert a.scores["fre"] > b.scores["fre"] and a.overall > b.overall
    for k in ("fk", "fog", "smog", "cli", "ari"):
        assert a.scores[k] < b.scores[k], k


def test_ranges_and_all_metrics_present():
    for t in [SIMPLE, HARD] + [s["text"] for s in SAMPLES.values()]:
        r = analyze_readability(t)
        assert set(r.scores) == set(METRICS)
        assert 0 <= r.scores["fre"] <= 100 and 0 <= r.overall <= 100
        assert all(v >= 0 for v in r.scores.values())


def test_labels():
    assert band_for_score(62) == "Standard" and band_for_score(10) == "Very hard" and band_for_score(95) == "Very easy"
    assert level_for_grade(8.3) == "Standard" and level_for_grade(14) == "College"
    assert audience_for_grade(8.2) == "Appropriate for 8th\u20139th grade students."


def test_dashboard_has_no_blank_lines_and_shows_scores():
    a, b = analyze_readability(HARD), analyze_readability(SIMPLE)
    html = dashboard_html(a, b, [("Facts preserved", "4/4")])
    assert "\n\n" not in html  # a blank line would break Streamlit's markdown HTML block
    assert "Flesch Reading Ease" in html and "Original" in html and "4/4" in html
    assert "Flesch Reading Ease" in scores_as_text(a, b)
