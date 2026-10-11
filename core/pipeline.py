"""Orchestrator: analyze -> (skip gate) -> rewrite -> verify -> retry/fallback -> result."""
from __future__ import annotations

from dataclasses import dataclass, field

from .analyzer import Analysis, analyze
from .facts import Fact, extract_facts
from .llm import LLMClient, LLMError, judge
from .rewriter import build_prompt, rewrite_fallback, rewrite_llm
from .verifier import FactReport, Item, verify_output


@dataclass
class Result:
    original: str
    output: str
    mode: str                    # gemini | fallback | skipped
    analysis: Analysis
    facts: list
    report: FactReport
    judge: dict | None = None
    attempts: int = 0
    notes: list = field(default_factory=list)

    @property
    def approved(self) -> bool:
        return self.report.verdict != "BLOCKED"


def add_judge_items(report: FactReport, j: dict | None) -> None:
    if not j:
        return
    if not j["meaning_preserved"]:
        report.items.append(Item("meaning", "", "", "review", "warning",
                                 "AI judge thinks the meaning may have changed. " + j["notes"]))
    for c in j["added_claims"]:
        report.items.append(Item("claim", "", c, "review", "warning", "AI judge: possible unsupported claim."))
    for c in j["removed_claims"]:
        report.items.append(Item("claim", c, "", "review", "warning", "AI judge: possibly dropped or weakened."))


def _feedback(report: FactReport) -> str:
    return "\n".join(f"- {i.message} (source: '{i.source}', rewrite: '{i.output}')"
                     for i in report.items if i.severity == "critical")


def humanize(text: str, context: str, tone: str, llm: LLMClient | None = None, voice_profile: str = "",
             voice_examples=(), extra_terms=(), skip_threshold: int = 25, use_skip_gate: bool = True,
             strict: bool = False, use_judge: bool = True, max_retries: int = 2) -> Result:
    facts = extract_facts(text, extra_terms)
    analysis = analyze(text)

    if use_skip_gate and analysis.score < skip_threshold:
        rep = verify_output(text, facts, text, strict)
        return Result(text, text, "skipped", analysis, facts, rep,
                      notes=["Already reads naturally, so it was left unchanged (resistance to unnecessary rewriting)."])

    notes, feedback, output, mode, j = [], "", text, "fallback", None
    report = verify_output(text, facts, text, strict)
    attempts = 0
    for attempts in range(1, max_retries + 2):
        mode = "fallback"
        if llm is not None and llm.available:
            try:
                output = rewrite_llm(llm, build_prompt(text, context, tone, facts, analysis, voice_profile,
                                                       voice_examples, feedback))
                mode = "gemini"
            except LLMError as e:
                notes.append(f"Gemini unavailable ({e}). Used the offline rule-based rewriter.")
                output = rewrite_fallback(text)
        else:
            output = rewrite_fallback(text)
        report = verify_output(text, facts, output, strict)
        if report.verdict != "BLOCKED":
            break
        feedback = _feedback(report)
        notes.append(f"Attempt {attempts} failed verification; retrying with feedback.")
        if mode == "fallback":
            break  # deterministic fallback would repeat itself

    if mode == "gemini" and use_judge and report.verdict != "BLOCKED":
        j = judge(llm, text, output)
        add_judge_items(report, j)
    if report.verdict == "BLOCKED":
        notes.append("Verification failed. The rewrite is shown for review but NOT approved.")
    if mode == "fallback" and not any("Gemini" in n for n in notes):
        notes.append("No Gemini key configured: using the basic offline rewriter (demo mode).")
    return Result(text, output, mode, analysis, facts, report, j, attempts, notes)
