"""Robotic-language detector: rule-based, explainable, no API needed."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

TEMPLATE_PHRASES = [
    "i hope this email finds you well", "it is important to note that", "it should be noted that",
    "it is worth noting that", "please do not hesitate to", "do not hesitate to contact",
    "in conclusion", "in summary", "furthermore", "moreover", "additionally", "in addition",
    "demonstrated proficiency in", "demonstrated a good understanding of", "demonstrated a strong understanding of",
    "demonstrated a strong understanding", "has demonstrated", "showcased proficiency", "a wide range of",
    "plays a crucial role", "at this point in time", "due to the fact that", "in order to",
    "with regard to", "with respect to", "pursuant to", "kindly note", "kindly be informed",
    "we regret to inform you", "we are pleased to inform you", "thank you for your time and consideration",
    "i am writing to", "delve into", "comprehensive overview", "kindly describe", "kindly elaborate",
]
FORMAL_WORDS = [
    "utilize", "utilise", "utilized", "leverage", "commence", "endeavor", "ascertain", "facilitate",
    "subsequently", "prior to", "henceforth", "aforementioned", "thereby", "robust", "seamless",
    "kindly", "pertaining to", "necessitate",
]
CONNECTORS = ["furthermore", "moreover", "additionally", "in addition", "consequently", "thus", "hence"]


@dataclass
class Flag:
    start: int
    end: int
    text: str
    reason: str


@dataclass
class Analysis:
    score: int = 0
    label: str = "natural"
    flags: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def _find_all(text: str, phrases, reason: str) -> list:
    out = []
    for p in phrases:
        for m in re.finditer(r"(?<![\w])" + re.escape(p) + r"(?![\w])", text, flags=re.IGNORECASE):
            out.append(Flag(m.start(), m.end(), text[m.start():m.end()], reason))
    return out


def analyze(text: str) -> Analysis:
    flags: list = []
    template = _find_all(text, TEMPLATE_PHRASES, "templated phrase")
    formal = _find_all(text, FORMAL_WORDS, "overly formal word")
    flags += template + [f for f in formal if not any(t.start <= f.start < t.end for t in template)]

    sentences = [(m.start(), m.group(0)) for m in re.finditer(r"[^.!?\n]+[.!?]?", text) if m.group(0).strip()]
    starters: dict = {}
    repeats = 0
    long_sents = 0
    for start, s in sentences:
        words = re.findall(r"[A-Za-z']+", s)
        if len(words) > 30:
            long_sents += 1
            flags.append(Flag(start, start + len(s), s.strip()[:60] + "...", "very long sentence"))
        if len(words) >= 2:
            key = " ".join(w.lower() for w in words[:2])
            starters[key] = starters.get(key, 0) + 1
            if starters[key] > 1:
                repeats += 1
                off = s.index(words[0])
                end = s.index(words[1], off) + len(words[1])
                flags.append(Flag(start + off, start + end, s[off:end], "repeated sentence opener"))

    n_conn = len(_find_all(text, CONNECTORS, ""))
    score = (min(48, 12 * len(template)) + min(30, 10 * repeats) + min(20, 5 * len(formal))
             + min(12, 6 * long_sents) + (min(10, 5 * (n_conn - 2)) if n_conn > 2 else 0))
    score = max(0, min(100, score))
    label = "natural" if score < 25 else "moderately robotic" if score < 55 else "robotic"
    flags.sort(key=lambda f: f.start)
    return Analysis(score, label, flags, {"templates": len(template), "repeated_openers": repeats,
                                          "formal_words": len(formal), "long_sentences": long_sents})
