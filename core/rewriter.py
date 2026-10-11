"""Contextual rewriter: Gemini prompt + an offline rule-based fallback."""
from __future__ import annotations

import re

from .llm import LLMClient, LLMError

CONTEXTS = {
    "Recruiter feedback": "Internal feedback a recruiter or interviewer writes about a candidate. Direct, evidence-based, "
                          "fair; keep scores, skills and the recommendation exactly as stated.",
    "Candidate email": "An email sent to a candidate. Warm, clear, respectful; keep dates, times, role and next steps exact.",
    "Interview question": "A question asked aloud in an interview. Short, clear, one idea at a time, easy to say out loud.",
    "Summary": "A short summary for busy readers. Concise, plain wording, no filler.",
    "Report": "A formal report section. Structured and precise but still readable, not stiff.",
}
TONES = {
    "Professional": "Professional: respectful, neutral, concise. Minimal contractions.",
    "Polished": "Polished: smooth and confident, well-structured, natural rhythm, light contractions allowed.",
    "Conversational": "Conversational: the way a thoughtful colleague would say it, contractions fine, short sentences.",
}

PROMPT = """You rewrite AI-generated text so it sounds natural and human, WITHOUT changing its meaning.

CONTEXT: {context_desc}
TONE: {tone_desc}
{voice_block}
HARD RULES
1. Keep every protected fact below EXACTLY as written (same spelling, numbers, dates, scores, names, terms).
2. Do NOT add any claim, achievement, reason, number, name or opinion that is not in the SOURCE.
3. Do NOT drop any fact or the overall recommendation / next step.
4. Fix repetitive sentence openings, filler ("It is important to note"), stiff connectors and over-formal words.
5. If a sentence is already natural, leave it as it is.
6. Do not add a greeting or sign-off unless the SOURCE has one.

PROTECTED FACTS:
{facts}

DETECTED ROBOTIC PATTERNS:
{patterns}
{feedback}
SOURCE:
\"\"\"{source}\"\"\"

Return ONLY JSON: {{"rewrite": "<the rewritten text>"}}"""


def build_prompt(source, context, tone, facts, analysis, voice_profile="", voice_examples=(), feedback=""):
    voice_lines = []
    if voice_profile.strip():
        voice_lines.append(f"VOICE NOTES FROM THE USER (follow them): {voice_profile.strip()}")
    if voice_examples:
        ex = "\n---\n".join(voice_examples[-2:])
        voice_lines.append("EARLIER APPROVED TEXTS (match this voice for consistency):\n" + ex)
    patterns = "\n".join(f"- '{f.text}' ({f.reason})" for f in analysis.flags[:12]) or "- none detected"
    return PROMPT.format(
        context_desc=CONTEXTS.get(context, context), tone_desc=TONES.get(tone, tone),
        voice_block=("\n".join(voice_lines) + "\n") if voice_lines else "",
        facts="\n".join(f"- {f.text}  [{f.kind}]" for f in facts) or "- (none detected)",
        patterns=patterns,
        feedback=(f"\nPREVIOUS ATTEMPT FAILED VERIFICATION. FIX THIS:\n{feedback}\n" if feedback else ""),
        source=source,
    )


def rewrite_llm(llm: LLMClient, prompt: str) -> str:
    data = llm.generate_json(prompt, temperature=0.3)
    text = str(data.get("rewrite", "")).strip()
    if not text:
        raise LLMError("Empty rewrite")
    return text


# ---------- offline fallback (basic, clearly labelled in the UI) ----------
_REPLACE = [
    (r"I hope this email finds you well\.?\s*", ""),
    (r"It is important to note that\s+", ""), (r"It should be noted that\s+", ""),
    (r"It is worth noting that\s+", ""),
    (r"\bFurthermore,\s*", "Also, "), (r"\bMoreover,\s*", "Also, "), (r"\bAdditionally,\s*", "Also, "),
    (r"\bIn addition,\s*", "Also, "),
    (r"\bin order to\b", "to"), (r"\bprior to\b", "before"), (r"\bwith regard to\b", "about"),
    (r"\bwith respect to\b", "about"), (r"\bdue to the fact that\b", "because"),
    (r"\bat this point in time\b", "now"), (r"\butili[sz]ed\b", "used"), (r"\butili[sz]e\b", "use"),
    (r"\bPursuant to\b", "Following"), (r"\bkindly\s+", "please "),
    (r"Please do not hesitate to contact us should you require any further clarification\.?",
     "If you have any questions, just let us know."),
    (r"Please do not hesitate to contact", "Please feel free to contact"),
    (r"We are pleased to inform you that\s+", "Good news: "),
]
_VERB_FIX = {"is": "are", "needs": "need", "has": "have", "was": "were", "demonstrates": "demonstrate",
             "shows": "show", "requires": "require", "performs": "perform", "scores": "score", "lacks": "lack",
             "displays": "display", "meets": "meet", "shows": "show"}


def rewrite_fallback(source: str) -> str:
    text = source
    for pat, rep in _REPLACE:
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)
    sents = re.split(r"(?<=[.!?])\s+", text.strip())
    out, seen = [], False
    for s in sents:
        m = re.match(r"The candidate\b", s)
        if m:
            if seen and not s[m.end():m.end()+1] == ",":
                s = "They" + s[m.end():]
                s = re.sub(r"\b(" + "|".join(_VERB_FIX) + r")\b", lambda x: _VERB_FIX[x.group(1)], s, count=0)
            seen = True
        out.append(s)
    text = " ".join(out)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)
    return text.strip()
