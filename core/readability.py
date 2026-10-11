"""Readability scores (pure Python, no extra dependencies).

Six standard formulas: Flesch Reading Ease, Flesch-Kincaid Grade, Gunning Fog, SMOG,
Coleman-Liau and Automated Readability Index. Grade-level scores are clamped at 0 and
Flesch Reading Ease is clamped to 0-100 so the dashboard always shows sensible numbers.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'\u2019\-]*")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_PARA_SPLIT = re.compile(r"\n\s*\n")

# key -> (display name, tooltip)
METRICS = {
    "fre": ("Flesch Reading Ease", "Higher is easier. Based on sentence length and syllables per word."),
    "fk": ("Flesch-Kincaid Grade Level", "U.S. school grade needed to follow the text."),
    "fog": ("Gunning Fog Index", "Grade level, driven by long sentences and words of 3+ syllables."),
    "smog": ("SMOG Index", "Grade level, driven by words of 3+ syllables. Designed for 30+ sentences."),
    "cli": ("Coleman-Liau Index", "Grade level based on letters per word and sentence length."),
    "ari": ("Automated Readability Index", "Grade level based on characters per word and sentence length."),
}
GRADE_KEYS = ["fk", "fog", "smog", "cli", "ari"]


@dataclass
class Readability:
    words: int = 0
    characters: int = 0
    sentences: int = 0
    paragraphs: int = 0
    syllables: int = 0
    complex_words: int = 0
    scores: dict = field(default_factory=dict)   # key -> float
    overall: float = 0.0

    @property
    def avg_sentence_len(self) -> float:
        return self.words / self.sentences if self.sentences else 0.0

    @property
    def complex_pct(self) -> float:
        return 100 * self.complex_words / self.words if self.words else 0.0


def count_syllables(word: str) -> int:
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 1  # numbers and symbols count as one beat
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", w)))


def ease_from_grade(grade: float) -> float:
    """Map a U.S. grade level onto the same 0-100 'higher is easier' scale as Flesch."""
    return max(0.0, min(100.0, 100 - 6 * (grade - 2)))


def analyze_readability(text: str) -> Readability:
    text = text or ""
    words = _WORD.findall(text)
    n = len(words)
    sents = [s for s in _SENT_SPLIT.split(text.strip()) if _WORD.search(s)]
    s = len(sents)
    paras = len([p for p in _PARA_SPLIT.split(text.strip()) if _WORD.search(p)])
    r = Readability(words=n, characters=len(text), sentences=s, paragraphs=paras)
    if n == 0 or s == 0:
        return r

    syl = [count_syllables(w) for w in words]
    r.syllables = sum(syl)
    r.complex_words = sum(1 for k in syl if k >= 3)
    letters = sum(c.isalpha() for w in words for c in w)
    alnum = sum(c.isalnum() for w in words for c in w)

    wps = n / s                    # words per sentence
    spw = r.syllables / n          # syllables per word
    L = 100 * letters / n          # letters per 100 words
    S = 100 * s / n                # sentences per 100 words

    fre = 206.835 - 1.015 * wps - 84.6 * spw
    fk = 0.39 * wps + 11.8 * spw - 15.59
    fog = 0.4 * (wps + 100 * r.complex_words / n)
    smog = 1.0430 * math.sqrt(r.complex_words * (30 / s)) + 3.1291
    cli = 0.0588 * L - 0.296 * S - 15.8
    ari = 4.71 * (alnum / n) + 0.5 * wps - 21.43

    r.scores = {"fre": max(0.0, min(100.0, fre)), "fk": max(0.0, fk), "fog": max(0.0, fog),
                "smog": max(0.0, smog), "cli": max(0.0, cli), "ari": max(0.0, ari)}
    eases = [r.scores["fre"]] + [ease_from_grade(r.scores[k]) for k in GRADE_KEYS]
    r.overall = sum(eases) / len(eases)
    return r


# ---------- labels used by the dashboard ----------
def level_for_grade(grade: float) -> str:
    return "Easy" if grade <= 6 else "Standard" if grade <= 12 else "College" if grade <= 16 else "Professional"


def level_for_ease(score: float) -> str:
    return "Easy" if score >= 70 else "Standard" if score >= 50 else "College" if score >= 30 else "Professional"


def band_for_score(score: float) -> str:
    return ("Very hard" if score < 30 else "Hard" if score < 50 else "Standard" if score < 70
            else "Easy" if score < 90 else "Very easy")


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}" + {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def audience_for_grade(grade: float) -> str:
    g = int(round(grade))
    if g < 1:
        return "Appropriate for early elementary readers."
    if g >= 17:
        return "Best for specialised or professional readers."
    if g >= 13:
        return "Best for college-level readers."
    return f"Appropriate for {_ordinal(g)}\u2013{_ordinal(g + 1)} grade students."


_FRE_TABLE = [  # (minimum score, plain-English reading)
    (90, "Very easy. Easy for an 11-year-old."), (80, "Easy. Conversational English."),
    (70, "Fairly easy. Easy for 13-year-olds."), (60, "Plain English. Easy to read for most high school students."),
    (50, "Fairly difficult. Suits 10th-12th grade readers."), (30, "Difficult. Best for college-level readers."),
    (0, "Very difficult. Best for graduates and specialists."),
]


def audience_for_ease(score: float) -> str:
    return next(txt for lo, txt in _FRE_TABLE if score >= lo)


def tip_for(r: Readability) -> str:
    if r.words == 0:
        return "Add some text to see your readability scores."
    if r.avg_sentence_len > 20:
        return "Shortening long sentences can improve clarity and help you reach a wider audience."
    if r.complex_pct > 15:
        return "Swapping a few long words for simpler ones can improve clarity."
    return "Sentence length and word choice are in a comfortable range for most readers."


def scores_as_text(after: Readability, before: Readability) -> str:
    lines = ["Readability scores (original -> rewritten)"]
    for k, (name, _) in METRICS.items():
        lines.append(f"{name}: {before.scores.get(k, 0):.1f} -> {after.scores.get(k, 0):.1f}")
    lines.append(f"Overall score: {before.overall:.0f} -> {after.overall:.0f}")
    lines.append(f"Words: {before.words} -> {after.words}")
    return "\n".join(lines)
