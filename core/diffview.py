"""HTML helpers: robotic-phrase highlighting and word-level meaning diff."""
from __future__ import annotations

import difflib
import html
import re

_BOX = ("line-height:1.7;padding:14px;border:1px solid rgba(149,142,160,0.25);"
        "border-radius:12px;background:#1a1b20;color:#e3e1e9;white-space:pre-wrap;font-family:'Inter',sans-serif;font-size:15px;")


def highlight_flags(text: str, flags: list) -> str:
    out, pos = [], 0
    for f in sorted(flags, key=lambda x: x.start):
        if f.start < pos:
            continue
        out.append(html.escape(text[pos:f.start]))
        out.append(f'<mark style="background:rgba(255,180,171,0.22);color:#ffb4ab;border:1px solid rgba(255,180,171,0.4);'
                   f'border-radius:4px;padding:2px 4px;font-weight:500" '
                   f'title="{html.escape(f.reason)}">{html.escape(text[f.start:f.end])}</mark>')
        pos = f.end
    out.append(html.escape(text[pos:]))
    return f'<div style="{_BOX}">' + "".join(out) + "</div>"


def diff_html(a: str, b: str) -> str:
    ta, tb = re.findall(r"\S+|\s+", a), re.findall(r"\S+|\s+", b)
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ta, tb, autojunk=False).get_opcodes():
        if op == "equal":
            out.append(html.escape("".join(ta[i1:i2])))
        else:
            if i2 > i1:
                out.append('<del style="background:rgba(255,180,171,0.2);color:#ffb4ab;text-decoration:line-through;'
                           'border-radius:3px;padding:1px 4px;margin:0 1px">'
                           + html.escape("".join(ta[i1:i2])) + "</del>")
            if j2 > j1:
                out.append('<ins style="background:rgba(78,222,163,0.2);color:#4edea3;text-decoration:none;'
                           'font-weight:600;border-radius:3px;padding:1px 4px;margin:0 1px">'
                           + html.escape("".join(tb[j1:j2])) + "</ins>")
    return f'<div style="{_BOX}">' + "".join(out) + "</div>"
