"""Verify-before-deliver: compares a rewrite against the protected facts of the source."""
from __future__ import annotations

from dataclasses import dataclass, field

from .facts import NUM_TOKEN, _polarity_facts, _verb_stem, extract_facts, norm_num

CRITICAL_ADD_KINDS = {"date", "time", "score", "pct", "quantity", "num", "email"}


@dataclass
class Item:
    kind: str
    source: str
    output: str
    status: str      # preserved | partial | missing | changed | added | review
    severity: str    # ok | warning | critical
    message: str


@dataclass
class FactReport:
    items: list = field(default_factory=list)
    total_facts: int = 0

    @property
    def verdict(self) -> str:
        if any(i.severity == "critical" for i in self.items):
            return "BLOCKED"
        if any(i.severity == "warning" for i in self.items):
            return "REVIEW"
        return "PASS"

    @property
    def preserved(self) -> int:
        return sum(1 for i in self.items if i.status == "preserved")

    def problems(self) -> list:
        return [i for i in self.items if i.severity != "ok"]


def _date_match(src, out):
    sd, sm, sy = src
    od, om, oy = out
    if sm != om:
        return None
    quality = "ok"
    if sd is not None:
        if od is None:
            quality = "partial"
        elif od != sd:
            return None
    elif od is not None:
        quality = "partial"
    if sy and oy and sy != oy:
        return None
    if sy and not oy:
        quality = "partial"
    return quality


def _num_tokens(text: str) -> set:
    return {norm_num(t.rstrip(",")) for t in NUM_TOKEN.findall(text)}


def verify_output(source: str, facts: list, output: str, strict: bool = False) -> FactReport:
    out_facts = extract_facts(output)
    out_l, src_l = output.casefold(), source.casefold()
    out_keys = {(f.kind, f.key) for f in out_facts}
    src_keys = {(f.kind, f.key) for f in facts}
    out_nums, src_nums = _num_tokens(output), _num_tokens(source)
    out_dates = [f for f in out_facts if f.kind == "date"]
    src_dates = [f for f in facts if f.kind == "date"]

    items: list = []
    missing: list = []
    consumed_additions: set[int] = set()

    source_polarities = _polarity_facts(source)
    output_polarities = _polarity_facts(output)
    for fact in source_polarities:
        verb, negative = fact.meta
        matching = [candidate for candidate in output_polarities if candidate.meta[0] == verb]
        if negative:
            opposite = next((candidate for candidate in matching if not candidate.meta[1]), None)
            if opposite:
                consumed_additions.add(id(opposite))
                scoped = verb in {"think", "believe", "suppose", "expect", "guess"}
                items.append(Item(
                    "polarity", fact.text, opposite.text,
                    "review" if scoped else "changed",
                    "warning" if scoped else "critical",
                    "Negation changed around a statement of belief; review the intended meaning."
                    if scoped else "Meaning-reversing polarity change: a negated action became affirmative.",
                ))
            else:
                same_polarity = next((candidate for candidate in matching if candidate.meta[1]), None)
                if not same_polarity:
                    items.append(Item(
                        "polarity", fact.text, "", "review", "warning",
                        "Negated action was not matched; review whether its meaning was preserved.",
                    ))
        else:
            opposite = next((candidate for candidate in matching if candidate.meta[1]), None)
            if opposite:
                consumed_additions.add(id(opposite))
                scoped = verb in {"think", "believe", "suppose", "expect", "guess"}
                items.append(Item(
                    "polarity", fact.text, opposite.text,
                    "review" if scoped else "changed",
                    "warning" if scoped else "critical",
                    "Negation changed around a statement of belief; review the intended meaning."
                    if scoped else "Meaning-reversing polarity change: an affirmative action became negated.",
                ))

    source_polarity_verbs = {fact.meta[0] for fact in source_polarities}
    for fact in output_polarities:
        if fact.meta[1] and fact.meta[0] not in source_polarity_verbs and id(fact) not in consumed_additions:
            items.append(Item(
                "polarity", "", fact.text, "added", "warning",
                "The rewrite adds an unsupported negated action; review its meaning.",
            ))

    for f in facts:
        if f.kind == "polarity":
            continue
        status, shown = "missing", ""
        if f.kind == "date":
            best = None
            for o in out_dates:
                q = _date_match(f.meta, o.meta)
                if q == "ok":
                    best, shown = q, o.text
                    break
                if q == "partial" and best is None:
                    best, shown = q, o.text
            if best:
                status = "preserved" if best == "ok" else "partial"
        elif f.kind in ("name", "custom"):
            if f.text.casefold() in out_l:
                status, shown = "preserved", f.text
            else:
                parts = [p for p in f.text.split() if len(p) > 2]
                same_name = next(
                    (
                        candidate for candidate in out_facts
                        if f.kind == "name"
                        and candidate.kind == "name"
                        and {word.casefold() for word in candidate.text.split()}
                        == {word.casefold() for word in parts}
                    ),
                    None,
                )
                hit = next((p for p in parts if p.lower() in out_l), None)
                replacement = next(
                    (
                        candidate for candidate in out_facts
                        if f.kind == "name"
                        and candidate.kind == "name"
                        and len(candidate.text.split()) == len(parts)
                        and candidate.text.casefold().split()[0] == parts[0].casefold()
                    ),
                    None,
                )
                if same_name:
                    status, shown = "preserved", same_name.text
                    consumed_additions.add(id(same_name))
                elif replacement:
                    status, shown = "changed", replacement.text
                    consumed_additions.add(id(replacement))
                elif hit and len(parts) > 1:
                    status, shown = "partial", hit
        elif f.kind == "num":
            if f.key.split(":", 1)[1] in out_nums:
                status, shown = "preserved", f.text
        else:
            if (f.kind, f.key) in out_keys:
                status, shown = "preserved", f.text

        if status == "preserved":
            items.append(Item(f.kind, f.text, shown, "preserved", "ok", "Present in the rewrite."))
        elif status == "changed":
            items.append(Item(f.kind, f.text, shown, "changed", "critical",
                              f"Protected {f.kind} changed: '{f.text}' became '{shown}'."))
        elif status == "partial":
            sev = "critical" if strict else "warning"
            items.append(Item(f.kind, f.text, shown, "partial", sev,
                              "Only partly kept (shortened or less specific). Check it is intentional."))
        elif f.weak and not strict:
            items.append(Item(f.kind, f.text, "", "missing", "warning",
                              "Capitalized word not found in the rewrite. It may be a name; check it."))
        else:
            missing.append(f)

    added: list = []
    for o in out_facts:
        if o.kind == "date":
            if not any(_date_match(s.meta, o.meta) for s in src_dates):
                added.append(o)
        elif o.kind == "num":
            if o.key.split(":", 1)[1] not in src_nums:
                added.append(o)
        elif o.kind in CRITICAL_ADD_KINDS:
            if (o.kind, o.key) not in src_keys:
                added.append(o)
        elif o.kind == "term":
            if (o.kind, o.key) not in src_keys and o.text.casefold() not in src_l:
                added.append(o)
        elif o.kind == "name":
            if o.text.casefold() not in src_l:
                added.append(o)

    for kind in {m.kind for m in missing}:
        ms = [m for m in missing if m.kind == kind]
        ads = [a for a in added if a.kind == kind]
        for m, a in zip(ms, ads):
            items.append(Item(kind, m.text, a.text, "changed", "critical",
                              f"Value changed: '{m.text}' became '{a.text}'."))
            missing.remove(m)
            added.remove(a)
    for m in missing:
        items.append(Item(m.kind, m.text, "", "missing", "critical", "Protected fact is missing from the rewrite."))
    for a in added:
        if id(a) in consumed_additions:
            continue
        crit = a.kind in CRITICAL_ADD_KINDS
        items.append(Item(a.kind, "", a.text, "added", "critical" if crit else "warning",
                          "Not in the original text: unsupported addition." if crit
                          else "Not in the original text. Check it was not invented."))
    return FactReport(items=items, total_facts=len(facts))
