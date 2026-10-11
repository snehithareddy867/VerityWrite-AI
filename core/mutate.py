"""Controlled 'bad rewrite' generators used by the demo and the evaluation script."""
from __future__ import annotations

import re

from .facts import extract_facts

_SWAP = {"python": "Java", "sql": "MongoDB", "react": "Angular", "java": "Python",
         "javascript": "TypeScript", "docker": "Kubernetes", "kubernetes": "Docker"}


def change_number(text: str):
    m = re.search(r"\d+", text)
    if not m:
        return None
    n = int(m.group(0))
    new = n + 10 if n < 90 else n - 10
    return text[:m.start()] + str(new) + text[m.end():]


def drop_date(text: str):
    for f in extract_facts(text):
        if f.kind == "date":
            s, e = f.span
            out = (text[:s].rstrip() + " " + text[e:].lstrip()).replace(" ,", ",").replace(" .", ".")
            return re.sub(r"\s{2,}", " ", out).strip()
    return None


def swap_term(text: str):
    """Replace every occurrence of the first known technical term with a different one."""
    for f in extract_facts(text):
        if f.kind == "term" and f.text.lower() in _SWAP:
            pat = r"(?<![\w+#])" + re.escape(f.text) + r"(?![\w+#])"
            return re.sub(pat, _SWAP[f.text.lower()], text, flags=re.IGNORECASE)
    return None


def add_numeric_claim(text: str):
    return text.rstrip() + " They also won a national coding award in 2019."


MUTATIONS = {
    "Change a number": change_number,
    "Drop the date": drop_date,
    "Swap a technical term": swap_term,
    "Invent an achievement": add_numeric_claim,
}
