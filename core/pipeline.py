"""Orchestrator: analyze -> (skip gate) -> rewrite -> verify -> retry/fallback -> result."""
from __future__ import annotations

from dataclasses import dataclass, field

from .analyzer import Analysis, analyze
from .facts import Fact, extract_facts
from .llm import LLMClient, LLMError, judge
from .rewriter import build_prompt, rewrite_fallback, rewrite_llm
from .verifier import FactReport, Item, verify_output

MAX_RETRIES = 2


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
        return self.report.verdict == "PASS"

    @property
    def unchanged(self) -> bool:
        return self.output == self.original

    @property
    def status(self) -> str:
        if self.mode == "skipped":
            return "skipped"
        if self.unchanged:
            return "unchanged"
        if self.mode == "gemini":
            return "rewritten"
        return self.mode


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
    retry_limit = min(max(max_retries, 0), MAX_RETRIES)
    for attempts in range(1, retry_limit + 2):
        mode = "fallback"
        if llm is not None and llm.available:
            try:
                output = rewrite_llm(llm, build_prompt(text, context, tone, facts, analysis, voice_profile,
                                                       voice_examples, feedback))
                mode = "gemini"
            except LLMError as e:
                notes.append(f"Gemini rewrite failed ({e}). Used the offline fallback instead.")
                output = rewrite_fallback(text)
        else:
            output = rewrite_fallback(text)
        report = verify_output(text, facts, output, strict)
        if report.verdict != "BLOCKED":
            break
        feedback = _feedback(report)
        if mode == "fallback":
            notes.append(f"Fallback failed verification on attempt {attempts}; no further fallback retry was attempted.")
            break
        if attempts <= retry_limit:
            notes.append(f"Gemini attempt {attempts} failed verification; retrying with feedback.")
        else:
            notes.append(f"Gemini verification failed after {attempts} attempts; retry limit reached.")

    if mode == "gemini" and use_judge and report.verdict != "BLOCKED":
        j = judge(llm, text, output)
        add_judge_items(report, j)
    if report.verdict == "BLOCKED":
        notes.append("Verification failed. This rewrite is NOT approved or verified; do not treat it as safe to use.")
    elif report.verdict == "REVIEW":
        notes.append("Human review required. This result is NOT approved until its warnings are resolved and verification passes.")
    if mode == "fallback":
        if output == text:
            notes.append("The offline fallback made no changes; the original text is shown unchanged, not as a rewrite.")
        elif llm is None:
            notes.append("No Gemini client was provided; used the basic offline fallback.")
        elif not llm.available and not any("Gemini rewrite failed" in note for note in notes):
            notes.append("Gemini is unavailable; used the basic offline fallback.")
        elif not any("Gemini rewrite failed" in note for note in notes):
            notes.append("Used the basic offline fallback.")
    return Result(text, output, mode, analysis, facts, report, j, attempts, notes)
