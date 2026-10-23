"""FactLock: deterministic extraction of protected facts (scores, dates, numbers, names, terms)."""
from __future__ import annotations

import re
from dataclasses import dataclass

_MONTHS = ["january", "february", "march", "april", "may", "june", "july",
           "august", "september", "october", "november", "december"]
_SHORT = [m[:3] for m in _MONTHS]

MONTH = (r"(?:January|February|March|April|May|June|July|August|September|October|"
         r"November|December|Sept|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b\.?")

TECH_TERMS = [
    "Python", "SQL", "NoSQL", "JavaScript", "TypeScript", "Java", "C++", "C#", "Rust", "Kotlin", "Swift",
    "React", "Next.js", "Node.js", "Angular", "Vue", "Django", "Flask", "FastAPI", "Spring Boot",
    "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Git", "GitHub", "Linux", "Jenkins", "Terraform",
    "TensorFlow", "PyTorch", "scikit-learn", "NumPy", "pandas", "Excel", "Tableau", "Power BI",
    "MongoDB", "PostgreSQL", "MySQL", "Redis", "Kafka", "GraphQL", "REST", "API", "CI/CD",
    "machine learning", "deep learning", "data structures", "algorithms", "system design",
    "query optimization", "SQL query optimization", "object-oriented programming", "microservices",
    "unit testing", "agile", "scrum",
]

STOP = {w.lower() for w in """
The A An This That These Those Our Their His Her Its My Your We I He She They It You In On At For With As By To From
Of And But Or So If While Although However Overall Additionally Furthermore Moreover Therefore Thus Hence Please
Thanks Thank Hi Hello Dear Hey Regards Best Sincerely Kind Warm Next After Before During Based Given Since Because
Also Both Each Every Some Many Most Several There Here What Which Who When Where Why How Can Could Would Should Will
Is Are Was Were Do Does Did Have Has Had Not No Yes All Any One Two Three First Second Third Final Strong Good
Great Excellent Candidate Interview Recruiter Team Role Position Summary Report Feedback Question Questions
Assessment Technical Behavioral Monday Tuesday Wednesday Thursday Friday Saturday Sunday
January February March April May June July August September October November December
""".split()}

_WORD = r"[A-Z][a-z]+(?:[’']s)?(?:-[A-Z][a-z]+)?(?![A-Za-z])"
_RUN = re.compile(rf"(?<![A-Za-z]){_WORD}(?:[ ]+{_WORD})*")

_TECH_RE = re.compile(
    r"(?<![\w+#])(?:" + "|".join(re.escape(t) for t in sorted(TECH_TERMS, key=len, reverse=True)) + r")(?![\w+#])",
    re.IGNORECASE,
)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_NUMDATE = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b")
_DMY = re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?({MONTH})(?:,?\s+(\d{{4}}))?(?!\d)")
_MDY = re.compile(rf"\b({MONTH})\s+(\d{{1,2}})(?:st|nd|rd|th)?(?!\d)(?:,?\s+(\d{{4}}))?")
_MY = re.compile(rf"\b({MONTH})\s+(\d{{4}})\b")
_TIME = re.compile(r"\b(\d{1,2}):(\d{2})\s*([AaPp]\.?[Mm]\.?)?")
_SCORE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)(?![\w/])")
_OUTOF = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s+out\s+of\s+(\d+(?:\.\d+)?)(?!\w)", re.IGNORECASE)
_PCT = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*(?:%|percent\b|per cent\b)", re.IGNORECASE)
_QUANTITY_UNITS = (
    "years?", "yrs?", "months?", "weeks?", "days?", "hours?", "hrs?", "minutes?", "mins?",
    "seconds?", "secs?", "people", "users?", "employees?", "customers?", "candidates?",
    "reports?", "records?", "items?", "files?", "requests?", "calls?", "tests?", "points?",
    "emails?", "messages?", "transactions?", "applications?", "tasks?", "projects?", "issues?",
    "bugs?", "tickets?", "pages?", "words?", "characters?",
    "kilometers?", "kilometres?", "meters?", "metres?", "miles?", "kilograms?", "grams?",
    "pounds?", "liters?", "litres?", "milliliters?", "millilitres?", "dollars?", "euros?",
    "pounds sterling", "times",
)
_NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
}
_QUANTITY_NUMBER = r"(?:\d+(?:,\d{3})*(?:\.\d+)?|" + "|".join(reversed(tuple(_NUMBER_WORDS))) + r")"
_QUANTITY = re.compile(
    r"(?<![\w.])(?P<currency>[$€£])?\s*(?P<number>" + _QUANTITY_NUMBER + r")"
    r"\s*(?P<unit>" + "|".join(_QUANTITY_UNITS) + r")\b",
    re.IGNORECASE,
)
_CURRENCY_AMOUNT = re.compile(r"(?<![\w.])(?P<currency>[$€£])\s*(?P<number>\d+(?:,\d{3})*(?:\.\d+)?)(?![\w.])")
_NUM = re.compile(r"(?<![\w.])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?![\w])")
_ACR = re.compile(r"\b[A-Z]{2,6}\b")
NUM_TOKEN = re.compile(r"\d[\d,]*(?:\.\d+)?")
_AUXILIARIES = (
    "do|does|did|is|are|was|were|has|have|had|will|would|can|could|should|must|may|might"
)
_POLARITY = re.compile(
    rf"\b(?P<aux>{_AUXILIARIES})(?P<contract>n't)?"
    r"(?:\s+(?P<not>not))?\s+(?P<verb>[a-z]+)\b",
    re.IGNORECASE,
)
_NEGATIVE_PREDICATE = re.compile(
    r"\b(?:never|failed\s+to|unable\s+to|not\s+able\s+to)\s+(?P<verb>[a-z]+)\b"
    r"|\bwithout\s+(?P<gerund>[a-z]+ing)\b",
    re.IGNORECASE,
)
_POSITIVE_PREDICATE = re.compile(r"\bable\s+to\s+(?P<verb>[a-z]+)\b", re.IGNORECASE)


@dataclass
class Fact:
    kind: str          # date, time, score, pct, num, email, term, name, custom
    text: str          # as written in the source
    key: str           # normalized key used for comparison
    span: tuple
    meta: tuple | None = None
    weak: bool = False  # e.g. a capitalized word at sentence start (maybe not a name)


def norm_num(s: str) -> str:
    s = s.replace(",", "")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def month_num(word: str) -> int:
    return _SHORT.index(word.lower().rstrip(".")[:3]) + 1


def _verb_stem(verb: str) -> str:
    word = verb.lower()
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("ing") and len(word) > 5:
        word = word[:-3]
        if len(word) > 2 and word[-1] == word[-2]:
            word = word[:-1]
    elif word.endswith("ed") and len(word) > 4:
        word = word[:-2]
    elif word.endswith("s") and len(word) > 3:
        word = word[:-1]
    return word[:-1] if word.endswith("e") and len(word) > 3 else word


def _unit_key(unit: str) -> str:
    normalized = unit.casefold()
    if normalized.endswith("ies"):
        return normalized[:-3] + "y"
    if normalized.endswith("s") and normalized not in {"people", "pounds sterling"}:
        return normalized[:-1]
    return normalized


def _quantity_number(value: str) -> str:
    normalized = value.casefold()
    if normalized in _NUMBER_WORDS:
        return str(_NUMBER_WORDS[normalized])
    return norm_num(value)


def _polarity_facts(text: str) -> list[Fact]:
    facts = []
    for match in _POLARITY.finditer(text):
        if match.group("verb").lower() in {"able", "unable", "hesitate", "only", "just"}:
            continue
        negative = bool(match.group("contract") or match.group("not"))
        verb = _verb_stem(match.group("verb"))
        facts.append(Fact(
            "polarity",
            match.group(0),
            f"polarity:{verb}:{'negative' if negative else 'positive'}",
            match.span(),
            (verb, negative),
        ))
    for match in _NEGATIVE_PREDICATE.finditer(text):
        verb = _verb_stem(match.group("verb") or match.group("gerund"))
        facts.append(Fact(
            "polarity",
            match.group(0),
            f"polarity:{verb}:negative",
            match.span(),
            (verb, True),
        ))
    for match in _POSITIVE_PREDICATE.finditer(text):
        verb = _verb_stem(match.group("verb"))
        facts.append(Fact(
            "polarity",
            match.group(0),
            f"polarity:{verb}:positive",
            match.span(),
            (verb, False),
        ))
    return facts


def _sentence_start(s: str, pos: int) -> bool:
    i = pos - 1
    while i >= 0 and s[i] in " \t\"'“‘([":
        i -= 1
    return i < 0 or s[i] in ".!?\n:•*-–—"


def extract_facts(text: str, extra_terms=()) -> list:
    facts: list = []
    work = text

    def scan(pattern, make):
        nonlocal work
        for m in pattern.finditer(work):
            f = make(m)
            if f:
                facts.append(f)
        work = pattern.sub(lambda m: " " * len(m.group(0)), work)

    def F(kind, m, key, meta=None, weak=False):
        return Fact(kind, text[m.start():m.end()].strip(), key, (m.start(), m.end()), meta, weak)

    def date(m, d, mo, y):
        return F("date", m, f"date:{d or ''}-{mo}-{y or ''}", (d, mo, y))

    scan(_EMAIL, lambda m: F("email", m, "email:" + m.group(0).lower()))
    scan(_ISO, lambda m: date(m, int(m.group(3)), int(m.group(2)), int(m.group(1))))
    scan(_NUMDATE, lambda m: date(m, int(m.group(1)), int(m.group(2)), int(m.group(3))))
    scan(_DMY, lambda m: date(m, int(m.group(1)), month_num(m.group(2)), int(m.group(3)) if m.group(3) else None))
    scan(_MDY, lambda m: date(m, int(m.group(2)), month_num(m.group(1)), int(m.group(3)) if m.group(3) else None))
    scan(_MY, lambda m: date(m, None, month_num(m.group(1)), int(m.group(2))))
    scan(_TIME, lambda m: F("time", m, "time:%d:%s%s" % (int(m.group(1)), m.group(2),
                                                        (m.group(3) or "").lower().replace(".", ""))))
    scan(_SCORE, lambda m: F("score", m, f"score:{norm_num(m.group(1))}/{norm_num(m.group(2))}"))
    scan(_OUTOF, lambda m: F("score", m, f"score:{norm_num(m.group(1))}/{norm_num(m.group(2))}"))
    scan(_PCT, lambda m: F("pct", m, f"pct:{norm_num(m.group(1))}"))
    scan(_QUANTITY, lambda m: F(
        "quantity", m,
        f"quantity:{_quantity_number(m.group('number'))}:"
        f"{(m.group('currency') or '').lower()}{_unit_key(m.group('unit'))}",
    ))
    scan(_CURRENCY_AMOUNT, lambda m: F(
        "quantity", m,
        f"quantity:{norm_num(m.group('number'))}:{m.group('currency')}",
    ))
    scan(_TECH_RE, lambda m: F("term", m, "term:" + m.group(0).lower()))
    scan(_ACR, lambda m: F("term", m, "term:" + m.group(0).lower()))

    # names: runs of capitalized words, minus common sentence-starter words
    for m in _RUN.finditer(work):
        words = [re.sub(r"[’']s$", "", w) for w in m.group(0).split()]
        stripped = 0
        while words and words[0].lower() in STOP:
            words.pop(0)
            stripped += 1
        if len(words) == 1 and words[0].lower() in STOP:
            continue
        if not words:
            continue
        name = " ".join(words)
        weak = len(words) == 1 and stripped == 0 and _sentence_start(work, m.start())
        facts.append(Fact("name", name, "name:" + name.lower(), (m.start(), m.end()), None, weak))
    work = _RUN.sub(lambda m: " " * len(m.group(0)), work)

    scan(_NUM, lambda m: F("num", m, "num:" + norm_num(m.group(0))))

    low = text.lower()
    for t in extra_terms:
        t = (t or "").strip()
        if t and t.lower() in low:
            i = low.index(t.lower())
            facts.append(Fact("custom", text[i:i + len(t)], "custom:" + t.lower(), (i, i + len(t))))

    seen, out = set(), []
    for f in sorted(facts, key=lambda x: x.span[0]):
        if (f.kind, f.key) not in seen:
            seen.add((f.kind, f.key))
            out.append(f)
    return out
