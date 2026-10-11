"""Evaluation: python eval/run_eval.py  (uses Gemini if GEMINI_API_KEY is set, else offline fallback).
Writes eval/results.md. Numbers are from YOUR run; report them as-is."""
import json, os, pathlib, statistics, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except Exception:
    pass

from core.analyzer import analyze
from core.llm import LLMClient
from core.mutate import MUTATIONS
from core.pipeline import humanize
from core.verifier import verify_output

llm = LLMClient(os.getenv("GEMINI_API_KEY"))
cases = json.loads((ROOT / "data" / "test_cases.json").read_text())
engine = f"Gemini ({llm.model})" if llm.available else "offline rule-based fallback"

rewritten = skipped_ok = natural_total = preserved_ok = 0
before, after = [], []
tamper = {k: [0, 0] for k in MUTATIONS}   # detected, tried
rows = []
for c in cases:
    r = humanize(c["text"], c["context"], c["tone"], llm)
    if c["already_natural"]:
        natural_total += 1
        skipped_ok += r.mode == "skipped"
    else:
        rewritten += 1
        preserved_ok += r.report.verdict != "BLOCKED"
        before.append(r.analysis.score)
        after.append(analyze(r.output).score)
    for name, fn in MUTATIONS.items():
        bad = fn(r.output)
        if bad is None:
            continue
        tamper[name][1] += 1
        tamper[name][0] += verify_output(c["text"], r.facts, bad).verdict == "BLOCKED"
    rows.append(f"| {c['id']} | {c['context']} | {r.mode} | {r.analysis.score} | {analyze(r.output).score} | "
                f"{r.report.verdict} | {r.report.preserved}/{r.report.total_facts} |")

lines = [f"# VerityWrite evaluation ({engine})", "", f"Test cases: {len(cases)} synthetic ({rewritten} robotic, {natural_total} already natural)", "",
         f"- Rewrites with all protected facts verified (not blocked): **{preserved_ok}/{rewritten}**",
         f"- Already-natural texts correctly left unchanged: **{skipped_ok}/{natural_total}**",
         f"- Average robotic score: **{statistics.mean(before):.0f} -> {statistics.mean(after):.0f}**", "",
         "## Tamper detection (deterministic checks on deliberately corrupted rewrites)", "",
         "| Corruption | Detected | Tried |", "|---|---|---|"]
for k, (d, t) in tamper.items():
    lines.append(f"| {k} | {d} | {t} |")
lines += ["", "Limitation: invented claims that contain no number, date or name are NOT caught by the deterministic "
          "checks; they rely on the AI judge and human review.", "",
          "## Per-case", "", "| id | context | mode | robotic before | after | verdict | facts kept |", "|---|---|---|---|---|---|---|"] + rows
out = "\n".join(lines)
(ROOT / "eval" / "results.md").write_text(out)
print(out)
