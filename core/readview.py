"""HTML for the Multi-Readability Suite dashboard (same role as diffview.py: rendering only)."""
from __future__ import annotations

from .readability import (METRICS, Readability, audience_for_ease, audience_for_grade, band_for_score,
                          level_for_ease, level_for_grade, tip_for)

# accent colour and icon per metric
ACCENT = {"fre": "#2E9A5B", "fk": "#2B6CD9", "fog": "#6C5CC9", "smog": "#E59A1B", "cli": "#1F9AA6", "ari": "#4A7FB5"}
ICON = {"fre": "\U0001F4D6", "fk": "\U0001F393", "fog": "\U0001F32B\uFE0F", "smog": "\U0001F4CA",
        "cli": "\U0001F9EE", "ari": "\U0001F524"}
LEVEL_DOT = {"Easy": "#2E9A5B", "Standard": "#2B6CD9", "College": "#6C5CC9", "Professional": "#E59A1B"}
SCALE = [(30, "#D94F5C", "Very hard"), (20, "#F0A030", "Hard"), (20, "#F2C94C", "Standard"),
         (20, "#8BCB8F", "Easy"), (10, "#2E9A5B", "Very easy")]
TICKS = [0, 30, 50, 70, 100]

CSS = """<style>
.rs{font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif;color:#e3e1e9;margin:4px 0 8px}
.rs *{box-sizing:border-box}
.rs-head{display:flex;justify-content:space-between;align-items:flex-end;gap:12px;flex-wrap:wrap;margin-bottom:14px}
.rs-h{font-size:26px;font-weight:700;line-height:1.2;color:#e3e1e9}
.rs-sub{font-size:14px;color:#958ea0;margin-top:2px}
.rs-count{font-size:14px;color:#958ea0}
.rs-grid{display:grid;grid-template-columns:5fr 7fr;gap:16px;align-items:start}
.rs-col{display:flex;flex-direction:column;gap:16px}
.rs-card{background:#1a1b20;border:1px solid rgba(149,142,160,0.25);border-radius:12px;padding:16px 18px}
.rs-title{font-size:15px;font-weight:600;color:#e3e1e9;margin-bottom:12px}
.rs-cards{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.rs-m{background:#1e1f25;border:1px solid rgba(149,142,160,0.2);border-left:4px solid var(--a,#999);border-radius:10px;padding:12px 14px}
.rs-m-top{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:600;color:#e3e1e9}
.rs-m-val{font-size:34px;font-weight:700;line-height:1.15;margin-top:6px}
.rs-m-lvl{font-size:14px;font-weight:600}
.rs-m-unit{font-size:12px;color:#958ea0;margin-top:6px}
.rs-m-aud{font-size:12px;color:#958ea0;margin-top:2px;line-height:1.35}
.rs-m-was{font-size:12px;color:#958ea0;margin-top:8px;padding-top:6px;border-top:1px dashed rgba(149,142,160,0.25)}
.rs-glance{display:flex;gap:18px;align-items:center;flex-wrap:wrap}
.rs-ring{width:128px;height:128px;border-radius:50%;display:grid;place-items:center;flex:none}
.rs-ring-in{width:98px;height:98px;border-radius:50%;background:#1a1b20;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
.rs-ring-in b{font-size:34px;line-height:1;color:#e3e1e9}
.rs-ring-in span{font-size:11px;color:#958ea0;margin-top:3px;line-height:1.2}
.rs-gtext{flex:1;min-width:200px}
.rs-gtext p{font-size:14px;color:#e3e1e9;margin:0 0 10px;line-height:1.45}
.rs-ticks{position:relative;height:16px;font-size:11px;color:#958ea0}
.rs-ticks span{position:absolute;transform:translateX(-50%)}
.rs-bar{position:relative;display:flex;height:8px;border-radius:4px;overflow:visible;margin:2px 0 4px}
.rs-seg{height:8px}
.rs-seg:first-child{border-radius:4px 0 0 4px}.rs-seg:last-child{border-radius:0 4px 4px 0}
.rs-dot{position:absolute;top:-4px;width:16px;height:16px;border-radius:50%;transform:translateX(-50%);border:3px solid #1a1b20;box-shadow:0 0 0 1px #e3e1e9;background:#e3e1e9}
.rs-dot.o{background:#1a1b20;box-shadow:0 0 0 1.5px #958ea0;width:12px;height:12px;top:-2px;border:2px solid #1a1b20}
.rs-names{display:flex;font-size:11px;color:#958ea0}
.rs-names span{text-align:center;white-space:nowrap;overflow:visible}
.rs-tip{margin-top:14px;background:rgba(160,120,255,0.12);border:1px solid rgba(160,120,255,0.28);border-radius:8px;padding:10px 12px;font-size:13px;color:#e3e1e9}
.rs-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.rs-st{background:#1e1f25;border:1px solid rgba(149,142,160,0.2);border-radius:8px;padding:8px 10px}
.rs-st small{display:block;font-size:11px;color:#958ea0}
.rs-st b{font-size:17px;color:#e3e1e9}
.rs-st i{font-style:normal;font-size:12px;color:#958ea0}
.rs-legend{display:grid;grid-template-columns:1fr 1fr;gap:6px 18px;margin-top:2px}
.rs-lg{display:flex;align-items:center;gap:8px;font-size:13px;color:#e3e1e9}
.rs-lg u{width:9px;height:9px;border-radius:50%;flex:none;text-decoration:none}
.rs-note{font-size:12px;color:#958ea0;margin-top:10px}
@media (max-width:900px){.rs-grid{grid-template-columns:1fr}}
@media (max-width:560px){.rs-cards,.rs-legend{grid-template-columns:1fr}.rs-stats{grid-template-columns:1fr 1fr}}
</style>"""


def _fmt(v: float) -> str:
    return f"{v:.1f}"


def _card(key: str, after: Readability, before: Readability) -> str:
    name, tip = METRICS[key]
    a, b = after.scores.get(key, 0.0), before.scores.get(key, 0.0)
    color = ACCENT[key]
    if key == "fre":
        level, unit, aud = level_for_ease(a), "0\u2013100 (Higher is easier to read)", audience_for_ease(a)
    else:
        level, unit, aud = level_for_grade(a), "U.S. Grade Level", audience_for_grade(a)
    same = abs(a - b) < 0.05
    was = f"Original {_fmt(b)}" + (" (unchanged)" if same else "")
    return (f'<div class="rs-m" style="--a:{color}" title="{tip}">'
            f'<div class="rs-m-top"><span>{ICON[key]}</span><span>{name}</span></div>'
            f'<div class="rs-m-val" style="color:{color}">{_fmt(a)}</div>'
            f'<div class="rs-m-lvl" style="color:{color}">{level}</div>'
            f'<div class="rs-m-unit">{unit}</div><div class="rs-m-aud">{aud}</div>'
            f'<div class="rs-m-was">{was}</div></div>')


def _scale(after: Readability, before: Readability) -> str:
    ticks = "".join(f'<span style="left:{t}%">{t}</span>' for t in TICKS)
    segs = "".join(f'<div class="rs-seg" style="width:{w}%;background:{c}"></div>' for w, c, _ in SCALE)
    names = "".join(f'<span style="width:{w}%">{n}</span>' for w, _, n in SCALE)
    hollow = ""
    if abs(after.overall - before.overall) >= 1:
        hollow = f'<div class="rs-dot o" title="Original: {before.overall:.0f}" style="left:{before.overall:.1f}%"></div>'
    return (f'<div class="rs-ticks">{ticks}</div>'
            f'<div class="rs-bar">{segs}{hollow}<div class="rs-dot" title="Rewritten: {after.overall:.0f}" '
            f'style="left:{after.overall:.1f}%"></div></div><div class="rs-names">{names}</div>')


def dashboard_html(after: Readability, before: Readability, chips: list[tuple[str, str]]) -> str:
    """`chips` = extra (label, value) pairs shown in the stats card, e.g. facts preserved, engine."""
    ov = after.overall
    ring_color = "#2E9A5B" if ov >= 50 else "#E59A1B" if ov >= 30 else "#D94F5C"
    track = "#292a2f"
    band = band_for_score(ov)
    glance_txt = {
        "Very hard": "Your text is very hard to read. Most readers will need a lot of effort.",
        "Hard": "Your text is hard to read. Readers will need strong reading skills.",
        "Standard": "Your text is fairly easy to read. Most readers with a standard education should understand it with little effort.",
        "Easy": "Your text is easy to read for most people.",
        "Very easy": "Your text is very easy to read for almost everyone.",
    }[band]
    delta = ""
    if abs(ov - before.overall) >= 1:
        delta = f' <span style="color:#6B7280">(original: {before.overall:.0f})</span>'

    cards = "".join(_card(k, after, before) for k in METRICS)
    legend = "".join(f'<div class="rs-lg"><u style="background:{LEVEL_DOT[n]}"></u><span><b>{n}</b> ({r})</span></div>'
                     for n, r in [("Easy", "0\u20136th grade"), ("Standard", "7\u201312th grade"),
                                  ("College", "13\u201316th grade"), ("Professional", "17+ grade")])

    stats = [("Words", f"{after.words:,}"), ("Characters", f"{after.characters:,}"),
             ("Sentences", f"{after.sentences:,}"), ("Paragraphs", f"{after.paragraphs:,}")]
    stat_html = "".join(f'<div class="rs-st"><small>{k}</small><b>{v}</b></div>' for k, v in stats)
    chip_html = "".join(f'<div class="rs-st"><small>{k}</small><b>{v}</b></div>' for k, v in chips)

    note = ""
    if after.words < 100 or after.sentences < 30:
        note = ('<div class="rs-note">These formulas are most reliable on 100+ words, and SMOG is designed for 30+ '
                'sentences, so treat scores for short text as a rough guide.</div>')

    html = (
        CSS + '<div class="rs">'
        '<div class="rs-head"><div><div class="rs-h">Multi-Readability Suite</div>'
        '<div class="rs-sub">Your rewrite, scored across six readability formulas.</div></div>'
        f'<div class="rs-count">{after.words:,} words \u2022 {after.characters:,} characters</div></div>'
        '<div class="rs-grid"><div class="rs-col">'
        '<div class="rs-card"><div class="rs-title">Readability at a Glance</div>'
        f'<div class="rs-glance"><div class="rs-ring" style="background:conic-gradient({ring_color} {ov:.1f}%,{track} 0)">'
        f'<div class="rs-ring-in"><b>{ov:.0f}</b><span>Overall Score<br>(Average)</span></div></div>'
        f'<div class="rs-gtext"><p>{glance_txt}{delta}</p>{_scale(after, before)}</div></div>'
        f'<div class="rs-tip">\U0001F4A1 <b>Tip:</b> {tip_for(after)}</div></div>'
        f'<div class="rs-card"><div class="rs-title">Your Text</div><div class="rs-stats">{stat_html}</div>'
        f'<div class="rs-stats" style="margin-top:8px;grid-template-columns:repeat({max(1, len(chips))},1fr)">{chip_html}</div></div>'
        '</div><div class="rs-col">'
        f'<div class="rs-card"><div class="rs-title">Readability Scores</div><div class="rs-cards">{cards}</div>{note}</div>'
        f'<div class="rs-card"><div class="rs-title">What Do These Scores Mean?</div><div class="rs-legend">{legend}</div></div>'
        '</div></div></div>'
    )
    return html
