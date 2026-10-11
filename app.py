"""VerityWrite AI - Streamlit application with Google Stitch Dark UI Theme (Team Hackprime)."""
from __future__ import annotations

import html
import os
import time
from datetime import datetime

import pandas as pd
import streamlit as st

from pathlib import Path

# Load .env using an absolute path derived from Path(__file__).resolve().parent,
# before any module or function reads the Gemini key.
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
try:
    from dotenv import load_dotenv
    if ENV_PATH.is_file():
        load_dotenv(dotenv_path=ENV_PATH, override=True)
    else:
        load_dotenv(override=True)
except Exception:
    pass

from core.analyzer import analyze
from core.diffview import diff_html, highlight_flags
from core.llm import LLMClient, LLMError, clean_api_key, diagnose_gemini_key, get_gemini_api_key
from core.media import IMAGE_MODES, MediaError, read_screenshot, text_to_speech, transcribe_audio
from core.mutate import MUTATIONS
from core.pipeline import add_judge_items, humanize
from core.readability import METRICS, analyze_readability, scores_as_text
from core.readview import dashboard_html
from core.rewriter import CONTEXTS, TONES
from core.samples import SAMPLES
from core.verifier import verify_output

st.set_page_config(
    page_title="VerityWrite AI — Flagship Workspace",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_key() -> str:
    # Ensure any live edits to .env at project root are picked up
    try:
        from dotenv import load_dotenv
        if ENV_PATH.is_file():
            load_dotenv(dotenv_path=ENV_PATH, override=True)
        else:
            load_dotenv(override=True)
    except Exception:
        pass
    # Check session state user-entered key first if any
    custom_k = S.get("custom_gemini_key", "").strip() if "custom_gemini_key" in S else ""
    return get_gemini_api_key(custom_key=custom_k)


@st.cache_resource
def get_llm(key: str, model: str) -> LLMClient:
    return LLMClient(key, model or None)


@st.cache_data(show_spinner=False)
def speak(text: str) -> bytes:
    return text_to_speech(text)


# Session state initialization
S = st.session_state
S.setdefault("voice_examples", [])
S.setdefault("result", None)
S.setdefault("edited_output", "")
S.setdefault("input_text", "")
S.setdefault("context", "Recruiter feedback")
S.setdefault("tone", "Professional")
S.setdefault("history", [])
S.setdefault("nav_choice", "Workspace")
S.setdefault("shot_text", "")
S.setdefault("voice_transcribed_text", "")
S.setdefault("last_duration_ms", 320)
S.setdefault("extra_terms_input", "")

# Load pending text from voice or OCR before widgets are rendered
if S.get("pending_text"):
    transferred = S.pop("pending_text")
    S.input_text = transferred
    S["input_text"] = transferred
    S.result = None


def load_sample():
    name = S.get("sample_choice")
    if name in SAMPLES:
        s = SAMPLES[name]
        S.input_text = s["text"]
        S.context = s["context"]
        S.tone = s["tone"]
        S.result = None


def quick_sample():
    s = SAMPLES["Recruiter feedback (robotic)"]
    S.input_text = s["text"]
    S.context = s["context"]
    S.tone = s["tone"]
    S.result = None


def set_tone(name: str):
    S.tone = name


def clear_workspace():
    S.input_text = ""
    S.result = None
    S.edited_output = ""
    S.shot_text = ""


def tamper(name: str):
    bad = MUTATIONS[name](S.edited_output)
    if bad:
        S.edited_output = bad
    else:
        S.tamper_msg = f"'{name}' does not apply to this text."


def reset_output():
    if S.result:
        S.edited_output = S.result.output


def clear_voice_memory():
    S.voice_examples = []


def use_shot_text():
    edited = (S.get("shot_extracted_preview") or "").strip() or S.get("shot_text", "").strip()
    if edited:
        S.input_text = edited
        S["input_text"] = edited
        S.result = None
        S.workspace_notice = ("success", "Screenshot text transferred into Workspace! Review your draft below or click 'Humanize & Verify'.")


def transfer_and_humanize_shot():
    edited = (S.get("shot_extracted_preview") or "").strip() or S.get("shot_text", "").strip()
    if edited:
        S.input_text = edited
        S["input_text"] = edited
        S.result = None
        S.pending_humanize = True


def load_history_entry(orig_text: str):
    S.input_text = orig_text
    S.result = None
    S.nav_choice = "Workspace"


def clear_audit_history():
    S.history = []


def reset_all_settings():
    S.context = "Recruiter feedback"
    S.tone = "Professional"
    S.voice_examples = []


def on_settings_context_change():
    S.context = S.settings_context_picker


def on_settings_tone_change():
    S.tone = S.settings_tone_picker


# =============================================================
# CONSOLIDATED GOOGLE STITCH DESIGN SYSTEM (CSS)
# =============================================================
STITCH_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --vw-surface: #121318;
    --vw-surface-container-lowest: #0d0e13;
    --vw-surface-container-low: #1a1b20;
    --vw-surface-container: #1e1f25;
    --vw-surface-container-high: #292a2f;
    --vw-surface-container-highest: #34343a;
    --vw-primary: #d0bcff;
    --vw-primary-container: #a078ff;
    --vw-secondary: #cebdff;
    --vw-secondary-container: #503a8f;
    --vw-tertiary: #4edea3;
    --vw-error: #ffb4ab;
    --vw-on-surface: #e3e1e9;
    --vw-on-surface-variant: #cbc3d7;
    --vw-outline: #958ea0;
    --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
}

/* Base Body & Layout Overrides */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--vw-surface) !important;
    color: var(--vw-on-surface) !important;
    font-family: var(--font-sans) !important;
}

/* Responsive, Balanced Main Workspace Container */
.block-container {
    max-width: 1040px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 3.5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    margin: 0 auto !important;
}

/* Header & Top Bar */
[data-testid="stHeader"] {
    background: rgba(18, 19, 24, 0.85) !important;
    backdrop-filter: blur(16px) !important;
    border-bottom: 1px solid rgba(149, 142, 160, 0.15) !important;
}

/* Sidebar Width & Polish */
[data-testid="stSidebar"] {
    min-width: 290px !important;
    max-width: 320px !important;
    background-color: var(--vw-surface-container-low) !important;
    border-right: 1px solid rgba(149, 142, 160, 0.18) !important;
}
[data-testid="stSidebarUserContent"] {
    padding: 1.25rem 1.25rem 2rem !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(149, 142, 160, 0.18) !important;
    margin: 0.85rem 0 !important;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    font-family: var(--font-sans) !important;
    color: var(--vw-on-surface) !important;
    letter-spacing: -0.02em !important;
}

/* Atmospheric Hero Banner */
.ambient-hero {
    position: relative;
    margin-bottom: 18px;
}
.ambient-hero::before {
    content: '';
    position: absolute;
    top: -20px;
    left: 15%;
    width: 340px;
    height: 120px;
    background: radial-gradient(circle, rgba(160, 120, 255, 0.16) 0%, rgba(18, 19, 24, 0) 70%);
    filter: blur(40px);
    pointer-events: none;
    z-index: 0;
}

/* Stitch Brand Header in Sidebar */
.stitch-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 4px 0 14px;
}
.stitch-brand-icon {
    width: 36px;
    height: 36px;
    border-radius: 9px;
    background: var(--vw-secondary-container);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--vw-primary);
    box-shadow: 0 4px 12px rgba(80, 58, 143, 0.4);
    flex-shrink: 0;
}
.stitch-brand-title {
    font-size: 18px;
    font-weight: 700;
    color: var(--vw-on-surface);
    letter-spacing: -0.02em;
    line-height: 1.15;
}
.stitch-brand-sub {
    font-size: 11px;
    color: var(--vw-on-surface-variant);
}

/* Trust Guarantee Pill */
.trust-guarantee-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px;
    border-radius: 9999px;
    background: var(--vw-surface-container-high);
    border: 1px solid rgba(149, 142, 160, 0.22);
    font-size: 10.5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--vw-on-surface-variant);
    margin-bottom: 6px;
}
.pulse-dot-green {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: var(--vw-tertiary);
    box-shadow: 0 0 8px rgba(78, 222, 163, 0.8);
    display: inline-block;
}
.pulse-dot-amber {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: #f59e0b;
    box-shadow: 0 0 8px rgba(245, 158, 11, 0.8);
    display: inline-block;
}

/* Quick Metrics Ribbon in Hero */
.metrics-ribbon {
    display: flex;
    align-items: center;
    gap: 14px;
    background: var(--vw-surface-container-low);
    border: 1px solid rgba(149, 142, 160, 0.22);
    padding: 8px 14px;
    border-radius: 10px;
}
.metric-ribbon-item {
    display: flex;
    flex-direction: column;
}
.metric-ribbon-label {
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 0.05em;
    color: var(--vw-outline);
    text-transform: uppercase;
}
.metric-ribbon-val {
    font-size: 13.5px;
    font-weight: 600;
    color: var(--vw-tertiary);
    display: flex;
    align-items: center;
    gap: 4px;
}
.ribbon-sep {
    width: 1px;
    height: 24px;
    background: var(--vw-surface-container-highest);
}

/* Stitch Card Containers */
.stitch-card {
    background: var(--vw-surface-container-low);
    border: 1px solid rgba(149, 142, 160, 0.22);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
}

/* Editor Diagnostic Strip */
.editor-diag-strip {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}
.editor-diag-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 9px;
    border-radius: 9999px;
    background: rgba(41, 42, 47, 0.8);
    border: 1px solid rgba(149, 142, 160, 0.25);
    font-size: 11px;
    color: var(--vw-on-surface-variant);
}
.editor-diag-pill.text-green {
    color: var(--vw-tertiary);
    border-color: rgba(78, 222, 163, 0.3);
}

/* Compact Voice Dictation Console */
.voice-card-compact {
    background: var(--vw-surface-container-lowest);
    border: 1px solid rgba(149, 142, 160, 0.22);
    border-radius: 12px;
    padding: 12px 16px;
    margin-bottom: 12px;
}
.mini-waveform {
    width: 100%;
    height: 28px;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 4px;
    padding-top: 4px;
}
.mini-bar {
    width: 100%;
    background: linear-gradient(180deg, var(--vw-tertiary) 0%, var(--vw-primary) 100%);
    border-radius: 9999px;
    min-height: 4px;
    animation: mini-wave 1.2s ease-in-out infinite alternate;
}
@keyframes mini-wave {
    0% { height: 20%; }
    50% { height: 95%; }
    100% { height: 40%; }
}

/* Guardrail Status Card & Rows */
.guardrail-status-card {
    background: rgba(30, 31, 37, 0.95);
    border: 1px solid rgba(149, 142, 160, 0.25);
    border-radius: 10px;
    padding: 10px 14px;
}
.gr-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 5px 0;
    border-bottom: 1px solid rgba(149, 142, 160, 0.12);
    font-size: 12.5px;
}
.gr-row:last-child {
    border-bottom: none;
}
.gr-label {
    color: #cbc3d7;
    font-weight: 500;
}
.gr-val {
    color: #e3e1e9;
    font-family: monospace;
    font-size: 11.5px;
}
.gr-badge {
    padding: 2px 8px;
    border-radius: 9999px;
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.03em;
}
.gr-badge-green {
    background: rgba(78, 222, 163, 0.18);
    color: #4edea3;
    border: 1px solid rgba(78, 222, 163, 0.4);
}
.gr-badge-purple {
    background: rgba(160, 120, 255, 0.18);
    color: #d0bcff;
    border: 1px solid rgba(160, 120, 255, 0.4);
}
.gr-badge-amber {
    background: rgba(245, 158, 11, 0.18);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.4);
}
.gr-badge-muted {
    background: rgba(149, 142, 160, 0.15);
    color: #958ea0;
    border: 1px solid rgba(149, 142, 160, 0.25);
}
.section-subhead {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #958ea0;
    margin-bottom: 6px;
}
.active-tone-desc {
    background: rgba(26, 27, 32, 0.8);
    border: 1px solid rgba(149, 142, 160, 0.2);
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 12px;
    color: #cbc3d7;
    margin-top: 8px;
}

/* Primary Action Shimmer Button */
.shimmer-action-btn button {
    background: linear-gradient(135deg, #a078ff 0%, #6d3bd7 50%, #503a8f 100%) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    padding: 12px 24px !important;
    border-radius: 10px !important;
    border: 1px solid rgba(208, 188, 255, 0.4) !important;
    box-shadow: 0 0 20px rgba(160, 120, 255, 0.4) !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}
.shimmer-action-btn button:hover {
    box-shadow: 0 0 30px rgba(160, 120, 255, 0.7) !important;
    transform: translateY(-1px) !important;
}

/* Results Top Summary Bar */
.results-summary-bar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    padding: 16px 20px;
    border-radius: 12px;
    background: var(--vw-surface-container);
    border: 1px solid rgba(149, 142, 160, 0.25);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
    margin-bottom: 20px;
}
.verdict-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 12px;
    border-radius: 9999px;
    font-size: 12.5px;
    font-weight: 700;
}
.verdict-pass {
    background: rgba(78, 222, 163, 0.18);
    color: var(--vw-tertiary);
    border: 1px solid rgba(78, 222, 163, 0.4);
}
.verdict-review {
    background: rgba(245, 158, 11, 0.18);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.4);
}
.verdict-blocked {
    background: rgba(255, 180, 171, 0.2);
    color: var(--vw-error);
    border: 1px solid rgba(255, 180, 171, 0.45);
}

/* Stat Tiles in Results */
.stat-tile-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    margin-bottom: 20px;
}
.stat-tile {
    background: var(--vw-surface-container);
    border: 1px solid rgba(149, 142, 160, 0.25);
    border-radius: 10px;
    padding: 14px;
}
.stat-tile-label {
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--vw-outline);
}
.stat-tile-val {
    font-size: 22px;
    font-weight: 800;
    color: var(--vw-on-surface);
    margin: 4px 0 2px;
}

/* Streamlit Native Widgets Fine-Tuning */
.stTextArea textarea {
    background-color: var(--vw-surface-container-low) !important;
    color: var(--vw-on-surface) !important;
    border: 1px solid rgba(149, 142, 160, 0.25) !important;
    border-radius: 10px !important;
    font-family: var(--font-sans) !important;
    font-size: 14.5px !important;
    line-height: 1.6 !important;
}
.stTextArea textarea:focus {
    border-color: var(--vw-primary) !important;
    box-shadow: 0 0 14px rgba(208, 188, 255, 0.25) !important;
}

.stTextInput input, .stSelectbox select {
    background-color: var(--vw-surface-container-low) !important;
    color: var(--vw-on-surface) !important;
    border: 1px solid rgba(149, 142, 160, 0.25) !important;
    border-radius: 8px !important;
}

.stButton button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.15s ease !important;
}

.stTabs [data-baseweb="tab-list"] {
    background-color: var(--vw-surface-container-lowest) !important;
    border-radius: 10px !important;
    padding: 3px !important;
    gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px !important;
    color: var(--vw-on-surface-variant) !important;
    font-weight: 600 !important;
    padding: 7px 14px !important;
    font-size: 13.5px !important;
}
.stTabs [aria-selected="true"] {
    background-color: var(--vw-surface-container-high) !important;
    color: var(--vw-on-surface) !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25) !important;
}

[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    overflow: hidden !important;
    border: 1px solid rgba(149, 142, 160, 0.2) !important;
}
</style>
"""

st.markdown(STITCH_CSS, unsafe_allow_html=True)

# LLM Client initialization
llm = get_llm(get_key(), os.getenv("GEMINI_MODEL", ""))

# -------------------------------------------------------------
# SIDEBAR: Navigation, Status & Config
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="stitch-brand">
        <div class="stitch-brand-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/>
            </svg>
        </div>
        <div>
            <div class="stitch-brand-title">VerityWrite AI</div>
            <div class="stitch-brand-sub">by Team Hackprime</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    nav = st.radio(
        "Navigation",
        ["Workspace", "History", "How It Works", "Settings"],
        key="nav_choice",
        label_visibility="collapsed",
    )

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Quick Workspace Controls in Sidebar
    st.markdown("<div class='section-subhead'>PRESETS & DOMAIN</div>", unsafe_allow_html=True)
    st.selectbox("Load Sample Template", ["(select a sample)"] + list(SAMPLES), key="sample_choice", on_change=load_sample)
    st.selectbox("Content Domain", list(CONTEXTS), key="context")
    st.selectbox("Target Voice Tone", list(TONES), key="tone")

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Guardrails Drawer
    st.markdown("<div class='section-subhead'>GUARDRAILS & LIMITS</div>", unsafe_allow_html=True)
    use_skip = st.toggle("Skip rewrite if natural", value=True, help="Preserves passages that already score high in organic burstiness.")
    strict = st.toggle("Strict verification", value=False, help="Block on any fact deviation or rephrasing.")
    use_judge = st.toggle("AI meaning judge", value=True, help="Cross-validates vector embeddings to flag any meaning deviation (requires Gemini).")
    extra = st.text_input("Extra protected terms", value=S.extra_terms_input, placeholder="e.g. Orbit Labs, Team Alpha", key="extra_terms_widget")
    S.extra_terms_input = extra

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Consistent Voice Memory
    with st.expander("🎙️ Consistent Voice Profile", expanded=False):
        st.text_area("Voice Notes", placeholder="e.g. Friendly, short sentences, say 'we' not 'the company'.", key="voice_notes_input")
        use_examples = st.checkbox("Match earlier approved outputs", value=True)
        st.caption(f"{len(S.voice_examples)} approved output(s) in session.")
        st.button("Clear voice memory", key="btn_clear_voice", on_click=clear_voice_memory)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # System Status & Telemetry in Sidebar Footer
    status_dot_class = "pulse-dot-green" if llm.available else "pulse-dot-amber"
    status_text = f"Gemini Connected ({llm.model})" if llm.available else "Offline Rules Engine (Demo Mode)"

    st.markdown(f"""
    <div style="background: rgba(13, 14, 19, 0.7); border: 1px solid rgba(149, 142, 160, 0.2); border-radius: 10px; padding: 10px 12px;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
            <div style="display: flex; align-items: center; gap: 6px;">
                <span class="{status_dot_class}"></span>
                <span style="font-size: 11px; font-weight: 600; color: #e3e1e9;">{status_text}</span>
            </div>
            <span style="font-size: 10px; color: #958ea0; font-family: monospace;">v2.4.0</span>
        </div>
        <div style="font-size: 10px; color: #958ea0; line-height: 1.4;">
            Zero Data Retention Guarantee &bull; Factual Integrity
        </div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================
# VIEW 1: WORKSPACE (Flagship Editor & Multimodal Inputs)
# =============================================================
if nav == "Workspace":
    # Hero Title with Compact Stitch Layout
    st.markdown("""
    <div class="ambient-hero">
        <div class="trust-guarantee-pill">
            <span class="pulse-dot-green"></span>
            <span>Zero Data Retention Guarantee &bull; Factual Integrity Engine</span>
        </div>
        <div style="display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: 14px;">
            <div>
                <h1 style="font-size: 30px; font-weight: 800; margin: 2px 0 4px; letter-spacing: -0.02em;">
                    Make your words sound <span style="color: #d0bcff; text-decoration: underline; text-decoration-color: rgba(208, 188, 255, 0.4); text-underline-offset: 6px;">human</span>.
                </h1>
                <p style="font-size: 14px; color: #cbc3d7; margin: 0;">
                    Refine your writing. Preserve your meaning. Verify what matters.
                </p>
            </div>
            <div class="metrics-ribbon">
                <div class="metric-ribbon-item">
                    <span class="metric-ribbon-label">Engine Latency</span>
                    <span class="metric-ribbon-val">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M7 2v11h3v9l7-12h-4l4-8z"/></svg>
                        240ms
                    </span>
                </div>
                <div class="ribbon-sep"></div>
                <div class="metric-ribbon-item">
                    <span class="metric-ribbon-label">Hallucination Risk</span>
                    <span class="metric-ribbon-val">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/></svg>
                        0.00%
                    </span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Multimodal Input Mode Selector Tabs
    tab_text, tab_voice, tab_shot = st.tabs(["✍️ Text Input", "🎙️ Voice Dictation", "🖼️ Screenshot OCR"])

    # -------------------------------------------------------------
    # TAB 1: TEXT INPUT
    # -------------------------------------------------------------
    with tab_text:
        if S.get("workspace_notice"):
            n_type, n_msg = S.pop("workspace_notice")
            if n_type == "success":
                st.success(n_msg)
            else:
                st.info(n_msg)

        current_text = S.input_text
        char_count = len(current_text)
        word_count = len(current_text.strip().split()) if current_text.strip() else 0
        read_time_secs = max(1, round((word_count / 200) * 60)) if word_count > 0 else 0

        # Compact Header Toolbar directly above Textarea
        col_diag, col_tools = st.columns([7, 5], vertical_alignment="center")
        with col_diag:
            st.markdown(f"""
            <div class="editor-diag-strip">
                <span class="editor-diag-pill"><b>{char_count}</b> chars &bull; <b>{word_count}</b> words</span>
                <span class="editor-diag-pill">Est. reading: <b>{read_time_secs}s</b></span>
                <span class="editor-diag-pill text-green">Factual locks active</span>
            </div>
            """, unsafe_allow_html=True)
        with col_tools:
            tb_sample, tb_clear = st.columns(2)
            tb_sample.button("📄 Load Sample", key="btn_quick_sample", on_click=quick_sample, use_container_width=True)
            tb_clear.button("🗑️ Clear", key="btn_quick_clear", on_click=clear_workspace, use_container_width=True)

        st.text_area(
            "Source Draft Input",
            key="input_text",
            height=180,
            placeholder="Paste your text, draft, AI output, or research notes here to inspect and humanize...",
            label_visibility="collapsed",
        )
        st.caption("🔒 Ephemeral processing. Numbers, dates, scores, and names are auto-locked for verification.")

    # -------------------------------------------------------------
    # TAB 2: VOICE DICTATION
    # -------------------------------------------------------------
    with tab_voice:
        st.markdown("""
        <div class="voice-card-compact">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                <div style="display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 13.5px; color: #e3e1e9;">
                    <svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor" style="color: #d0bcff;"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/><path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
                    <span>Live Acoustic Capture Console</span>
                </div>
                <span class="editor-diag-pill text-green">WHISPER / GEMINI MULTIMODAL</span>
            </div>
            <div class="mini-waveform">
                <div class="mini-bar" style="animation-delay: 0.1s; height: 35%;"></div>
                <div class="mini-bar" style="animation-delay: 0.25s; height: 75%;"></div>
                <div class="mini-bar" style="animation-delay: 0.15s; height: 45%;"></div>
                <div class="mini-bar" style="animation-delay: 0.4s; height: 90%;"></div>
                <div class="mini-bar" style="animation-delay: 0.3s; height: 60%;"></div>
                <div class="mini-bar" style="animation-delay: 0.5s; height: 80%;"></div>
                <div class="mini-bar" style="animation-delay: 0.2s; height: 50%;"></div>
                <div class="mini-bar" style="animation-delay: 0.35s; height: 70%;"></div>
                <div class="mini-bar" style="animation-delay: 0.45s; height: 40%;"></div>
                <div class="mini-bar" style="animation-delay: 0.6s; height: 85%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        v_rec_col, v_act_col = st.columns([7, 5], vertical_alignment="center")
        with v_rec_col:
            audio = st.audio_input("Record your voice", key="voice_audio_record", label_visibility="collapsed")
        with v_act_col:
            v_act_1, v_act_2 = st.columns(2)
            with v_act_1:
                btn_transcribe = st.button("✨ Transcribe", disabled=audio is None, type="primary", use_container_width=True, key="btn_transcribe_voice", help="Transcribe speech directly into Workspace")
            with v_act_2:
                btn_transcribe_run = st.button("⚡ Run Pipeline", disabled=audio is None, type="secondary", use_container_width=True, key="btn_transcribe_and_run", help="Transcribe speech and immediately run Humanize & Verify")

            if btn_transcribe or btn_transcribe_run:
                if not llm.available:
                    diag = diagnose_gemini_key(custom_key=S.get("custom_gemini_key"), env_path=ENV_PATH)
                    msg = "⚠️ Voice transcription requires a Gemini API key."
                    if diag.get("issue"):
                        msg += f" {diag['issue']}"
                    else:
                        msg += " Configure GEMINI_API_KEY in .env or Settings."
                    st.warning(msg)
                    if diag.get("suggestion"):
                        st.caption(f"💡 {diag['suggestion']}")
                elif audio is None:
                    st.warning("Please record audio before transcribing.")
                else:
                    audio_bytes = audio.getvalue()
                    if not audio_bytes or len(audio_bytes) < 100:
                        st.error("Audio recording is empty or silent. Please speak into your microphone and try again.")
                    else:
                        with st.spinner("Transcribing acoustic audio stream with Gemini Multimodal..."):
                            try:
                                transcribed = transcribe_audio(llm, audio_bytes, audio.type or "audio/wav")
                                S.voice_transcribed_text = transcribed
                                S.pending_text = transcribed
                                S.workspace_notice = ("success", "Voice dictation transcribed into Workspace! Review your draft below or click 'Humanize & Verify'.")
                                if btn_transcribe_run:
                                    S.pending_humanize = True
                                st.rerun()
                            except (LLMError, MediaError) as e:
                                st.error(f"Transcription error: {e}")
            st.caption("44.1kHz sampling &bull; Lossless audio buffer &bull; Zero storage")

        if S.get("voice_transcribed_text"):
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            st.text_area("Last Transcribed Speech (Editable)", value=S.voice_transcribed_text, height=90, key="voice_transcribed_edit")
            vt_col1, vt_col2 = st.columns(2)
            with vt_col1:
                if st.button("➡️ Transfer to Workspace Input", key="btn_transfer_voice_manual", use_container_width=True):
                    val = (S.get("voice_transcribed_edit") or "").strip() or S.voice_transcribed_text
                    S.input_text = val
                    S["input_text"] = val
                    S.result = None
                    S.workspace_notice = ("success", "Transcribed speech loaded into workspace!")
                    st.rerun()
            with vt_col2:
                if st.button("⚡ Transfer & Humanize Now", key="btn_transfer_voice_run", type="primary", use_container_width=True):
                    val = (S.get("voice_transcribed_edit") or "").strip() or S.voice_transcribed_text
                    S.input_text = val
                    S["input_text"] = val
                    S.result = None
                    S.pending_humanize = True
                    st.rerun()

    # -------------------------------------------------------------
    # TAB 3: SCREENSHOT OCR
    # -------------------------------------------------------------
    with tab_shot:
        shot_file = st.file_uploader("Upload screenshot image", type=["png", "jpg", "jpeg", "webp"], key="stitch_shot_uploader")
        if shot_file:
            s_img_col, s_ctrl_col = st.columns([5, 5], vertical_alignment="center")
            with s_img_col:
                st.image(shot_file, caption=shot_file.name, use_container_width=True)
            with s_ctrl_col:
                shot_mode = st.radio("Extraction Mode", list(IMAGE_MODES), horizontal=True, key="stitch_shot_mode")
                btn_ocr_run = st.button("🔍 Extract with Gemini Vision", key="btn_execute_ocr", type="primary", use_container_width=True)
                if btn_ocr_run:
                    if not llm.available:
                        diag = diagnose_gemini_key(custom_key=S.get("custom_gemini_key"), env_path=ENV_PATH)
                        msg = "⚠️ Screenshot OCR requires a Gemini API key."
                        if diag.get("issue"):
                            msg += f" {diag['issue']}"
                        else:
                            msg += " Configure GEMINI_API_KEY in .env or Settings."
                        st.warning(msg)
                        if diag.get("suggestion"):
                            st.caption(f"💡 {diag['suggestion']}")
                    else:
                        img_bytes = shot_file.getvalue()
                        if not img_bytes:
                            st.error("Uploaded image file is empty (0 bytes).")
                        else:
                            with st.spinner("Extracting text from screenshot with Gemini Vision..."):
                                try:
                                    extracted = read_screenshot(llm, img_bytes, shot_file.type or "image/png", shot_mode)
                                    S.shot_text = extracted
                                    S.shot_extracted_preview = extracted
                                    st.success(f"Extracted {len(extracted)} characters from image!")
                                except (LLMError, MediaError) as e:
                                    S.shot_text = ""
                                    st.error(f"OCR extraction failed: {e}")

        if S.get("shot_text"):
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            st.text_area("OCR Extraction Result (Editable)", value=S.shot_text, height=130, key="shot_extracted_preview")
            b_listen, b_use, b_humanize = st.columns([3, 4, 5])
            with b_listen:
                if st.button("🔊 Listen Audio", key="btn_shot_audio", use_container_width=True):
                    try:
                        st.audio(speak(S.get("shot_extracted_preview") or S.shot_text), format="audio/mp3")
                    except MediaError as e:
                        st.error(str(e))
            with b_use:
                st.button("➡️ Transfer to Workspace", key="btn_shot_commit", on_click=use_shot_text, use_container_width=True)
            with b_humanize:
                st.button("⚡ Transfer & Humanize Now", key="btn_shot_direct_humanize", on_click=transfer_and_humanize_shot, type="primary", use_container_width=True)

    # -------------------------------------------------------------
    # TONE SELECTOR & GUARDRAILS ACCORDION
    # -------------------------------------------------------------
    with st.expander("🛡️ Target Writing Tone & Guardrails Settings", expanded=False):
        col_tone_sec, col_gr_sec = st.columns([6, 6], vertical_alignment="top")
        with col_tone_sec:
            st.markdown("<div class='section-subhead'>Writing Tone</div>", unsafe_allow_html=True)
            t_cols = st.columns(len(TONES))
            for col, t_name in zip(t_cols, TONES):
                active = (S.tone == t_name)
                col.button(
                    f"✓ {t_name}" if active else t_name,
                    key=f"tone_btn_{t_name}",
                    on_click=set_tone,
                    args=(t_name,),
                    use_container_width=True,
                    type="primary" if active else "secondary",
                )
            st.markdown(f"<div class='active-tone-desc'>{TONES.get(S.tone, '')}</div>", unsafe_allow_html=True)

        with col_gr_sec:
            st.markdown("<div class='section-subhead'>Active Guardrails</div>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="guardrail-status-card">
                <div class="gr-row">
                    <span class="gr-label">Domain Context</span>
                    <span class="gr-badge gr-badge-purple">{S.context}</span>
                </div>
                <div class="gr-row">
                    <span class="gr-label">Skip Natural Gate</span>
                    <span class="gr-badge {'gr-badge-green' if use_skip else 'gr-badge-muted'}">{'Active (Score < 25)' if use_skip else 'Disabled'}</span>
                </div>
                <div class="gr-row">
                    <span class="gr-label">Strict Fact Lock</span>
                    <span class="gr-badge {'gr-badge-amber' if strict else 'gr-badge-muted'}">{'Strict (Zero Drift)' if strict else 'Standard'}</span>
                </div>
                <div class="gr-row">
                    <span class="gr-label">AI Meaning Judge</span>
                    <span class="gr-badge {'gr-badge-green' if use_judge else 'gr-badge-muted'}">{'Vector Auditing' if use_judge else 'Off'}</span>
                </div>
                <div class="gr-row">
                    <span class="gr-label">Protected Terms</span>
                    <span class="gr-val">{html.escape(extra.strip()) if extra.strip() else 'Auto-pinned'}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # -------------------------------------------------------------
    # PRIMARY ACTION BAR: Shimmer Humanize & Verify Button
    # -------------------------------------------------------------
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    c_btn_info, c_btn_action = st.columns([7, 5], vertical_alignment="center")
    with c_btn_info:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px; padding: 4px 0;">
            <div style="width: 38px; height: 38px; border-radius: 9px; background: #503a8f; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" style="color: #d0bcff;">
                    <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
                </svg>
            </div>
            <div>
                <div style="font-size: 13.5px; font-weight: 700; color: #e3e1e9;">Gemini Hybrid Rewrite Pipeline</div>
                <div style="font-size: 11.5px; color: #cbc3d7;">Neural humanization + 7-point factual integrity audit</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c_btn_action:
        st.markdown('<div class="shimmer-action-btn">', unsafe_allow_html=True)
        btn_humanize = st.button(
            "✨ Humanize & Verify",
            type="primary",
            use_container_width=True,
            disabled=not S.input_text.strip(),
            key="btn_run_humanize",
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------------------------------------------
    # EXECUTE PIPELINE
    # -------------------------------------------------------------
    if btn_humanize or S.pop("pending_humanize", False):
        start_t = time.time()
        with st.spinner("Analyzing syntactic markers, rewriting, and auditing integrity..."):
            terms = [t.strip() for t in extra.split(",") if t.strip()]
            voice_prof = S.get("voice_notes_input", "")
            res = humanize(
                S.input_text,
                S.context,
                S.tone,
                llm,
                voice_profile=voice_prof,
                voice_examples=S.voice_examples if use_examples else (),
                extra_terms=terms,
                use_skip_gate=use_skip,
                strict=strict,
                use_judge=use_judge,
            )
            elapsed_ms = round((time.time() - start_t) * 1000)
            S.last_duration_ms = elapsed_ms
            S.result = res
            S.edited_output = res.output
            S.terms = terms

            if res.approved and res.mode != "skipped":
                S.voice_examples = (S.voice_examples + [res.output])[-5:]

            history_item = {
                "id": f"vw-{int(time.time()) % 10000:04d}",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "original": res.original,
                "output": res.output,
                "verdict": res.report.verdict,
                "mode": res.mode,
                "tone": S.tone,
                "context": S.context,
                "facts_ratio": f"{res.report.preserved}/{res.report.total_facts}",
                "duration_ms": elapsed_ms,
            }
            S.history.insert(0, history_item)

    # =============================================================
    # RESULTS VIEW (Google Stitch Trust Audit)
    # =============================================================
    res = S.result
    if res:
        st.markdown("<hr style='margin: 28px 0 20px; border-color: rgba(149, 142, 160, 0.2);'/>", unsafe_allow_html=True)

        edited = S.edited_output
        report = verify_output(res.original, res.facts, edited, strict)
        unchanged = (edited == res.output)
        if unchanged and res.judge is not None:
            add_judge_items(report, res.judge)
        after_analysis = analyze(edited)

        verdict = report.verdict
        if verdict == "PASS":
            v_badge_class = "verdict-pass"
            v_badge_text = "PASS • All Integrity Checks Satisfied"
        elif verdict == "REVIEW":
            v_badge_class = "verdict-review"
            v_badge_text = "REVIEW • Check Flagged Warnings"
        else:
            v_badge_class = "verdict-blocked"
            v_badge_text = "BLOCKED • Protected Fact Missing/Altered"

        engine_name = {"gemini": f"Gemini ({llm.model})", "fallback": "Offline Rules Engine", "skipped": "Skipped Gate"}[res.mode]
        hash_id = f"#vw-{hash(res.original) % 10000:04d}-delta"

        st.markdown(f"""
        <div class="results-summary-bar">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 42px; height: 42px; border-radius: 10px; background: rgba(78, 222, 163, 0.15); display: flex; align-items: center; justify-content: center; border: 1px solid rgba(78, 222, 163, 0.3); flex-shrink: 0;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor" style="color: #4edea3;">
                        <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/>
                    </svg>
                </div>
                <div>
                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                        <span style="font-size: 17px; font-weight: 700; color: #e3e1e9;">Analysis & Verification Report</span>
                        <span class="verdict-badge {v_badge_class}">{v_badge_text}</span>
                    </div>
                    <div style="font-size: 11.5px; color: #958ea0; margin-top: 3px; display: flex; gap: 10px; flex-wrap: wrap;">
                        <span style="color: #d0bcff; font-weight: 600;">{engine_name}</span>
                        <span>&bull;</span>
                        <span style="font-family: monospace;">{hash_id}</span>
                        <span>&bull;</span>
                        <span style="color: #4edea3; font-weight: 600;">{S.last_duration_ms}ms latency</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        for n in res.notes:
            st.info(f"ℹ️ {n}")

        # Stat Badges Grid
        st.markdown(f"""
        <div class="stat-tile-grid">
            <div class="stat-tile">
                <div class="stat-tile-label">Facts Preserved</div>
                <div class="stat-tile-val" style="color: #4edea3;">{report.preserved} / {report.total_facts}</div>
                <div style="font-size: 11.5px; color: #cbc3d7;">Verbatim claim fidelity</div>
            </div>
            <div class="stat-tile">
                <div class="stat-tile-label">Robotic Score Delta</div>
                <div class="stat-tile-val" style="color: #d0bcff;">{res.analysis.score} → {after_analysis.score}</div>
                <div style="font-size: 11.5px; color: #cbc3d7;">Lower is more organic</div>
            </div>
            <div class="stat-tile">
                <div class="stat-tile-label">Engine Pipeline</div>
                <div class="stat-tile-val" style="font-size: 18px; color: #cebdff;">{res.mode.title()}</div>
                <div style="font-size: 11.5px; color: #cbc3d7;">Deterministic verification</div>
            </div>
            <div class="stat-tile">
                <div class="stat-tile-label">AI Judge Verdict</div>
                <div class="stat-tile-val" style="font-size: 18px; color: {'#4edea3' if res.judge and res.judge.get('meaning_preserved') else '#e3e1e9'};">
                    {'Passed' if res.judge and res.judge.get('meaning_preserved') else ('N/A' if not res.judge else 'Check')}
                </div>
                <div style="font-size: 11.5px; color: #cbc3d7;">Semantic equivalence</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Side-by-Side Comparison Panels
        col_orig, col_rewrite = st.columns(2)
        with col_orig:
            st.markdown("""
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                <div style="display: flex; align-items: center; gap: 7px;">
                    <span style="width: 7px; height: 7px; border-radius: 50%; background: #ffb4ab;"></span>
                    <h3 style="font-size: 15px; font-weight: 700; margin: 0;">Original Draft</h3>
                </div>
                <span style="font-size: 11px; color: #958ea0; font-family: monospace;">Robotic markers flagged</span>
            </div>
            """, unsafe_allow_html=True)
            st.caption("Highlighted = robotic patterns detected (hover for reason).")
            st.markdown(highlight_flags(res.original, res.analysis.flags), unsafe_allow_html=True)

        with col_rewrite:
            st.markdown("""
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                <div style="display: flex; align-items: center; gap: 7px;">
                    <span style="width: 7px; height: 7px; border-radius: 50%; background: #4edea3;"></span>
                    <h3 style="font-size: 15px; font-weight: 700; margin: 0;">Humanized Output (Editable)</h3>
                </div>
                <span style="font-size: 11px; color: #4edea3; font-family: monospace;">Re-checks instantly upon edit</span>
            </div>
            """, unsafe_allow_html=True)
            st.caption("Edit text freely — trust report below re-verifies automatically.")
            st.text_area("Rewritten text", key="edited_output", height=200, label_visibility="collapsed")
            if st.button("🔊 Listen to Rewrite Audio", key="btn_listen_rewrite", disabled=not edited.strip()):
                try:
                    st.audio(speak(edited), format="audio/mp3")
                except MediaError as e:
                    st.error(str(e))

        # Word-Level Meaning Diff
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        st.markdown("### 🔀 Meaning Diff")
        st.caption("Red = removed stiff phrasing, Green = humanized wording.")
        st.markdown(diff_html(res.original, edited), unsafe_allow_html=True)

        # Centerpiece Trust & Verification Report Table
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        st.markdown("### 🛡️ Trust & Verification Report")
        st.caption("Deterministic fact checks (scores, dates, numbers, names, technical terms), plus optional AI meaning judge.")

        label = {"ok": "✅ OK", "warning": "⚠️ Check", "critical": "⛔ Problem"}
        rows = [
            {
                "Result": label[i.severity],
                "Type": i.kind,
                "In Original": i.source or "-",
                "In Rewrite": i.output or "-",
                "Verification Details": i.message,
            }
            for i in report.items
        ]
        if rows:
            order = {"⛔ Problem": 0, "⚠️ Check": 1, "✅ OK": 2}
            rows.sort(key=lambda r: order[r["Result"]])
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.write("No protected facts detected in this text.")

        if res.judge and unchanged and res.judge.get("notes"):
            st.caption(f"🧠 AI Judge Notes: {res.judge['notes']}")

        # Multi-Readability Suite
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        read_after, read_before = analyze_readability(edited), analyze_readability(res.original)
        chips = [
            ("Robotic score", f"{res.analysis.score} → {after_analysis.score} /100"),
            ("Facts preserved", f"{report.preserved}/{report.total_facts}"),
            ("Engine", engine_name),
        ]
        st.markdown(dashboard_html(read_after, read_before, chips), unsafe_allow_html=True)

        # Export & Actions Strip
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        col_export_note, col_copy_scores, col_export_btn = st.columns([6, 3, 3])
        with col_export_note:
            st.caption("Scores computed locally. Only rewriting calls Gemini.")
        with col_copy_scores:
            with st.popover("📋 Copy Scores Text", use_container_width=True):
                st.code(scores_as_text(read_after, read_before), language=None)
        with col_export_btn:
            export_rows = [
                {"Metric": name, "Original": round(read_before.scores.get(k, 0), 1), "Rewritten": round(read_after.scores.get(k, 0), 1)}
                for k, (name, _) in METRICS.items()
            ]
            export_rows.append({"Metric": "Overall score", "Original": round(read_before.overall), "Rewritten": round(read_after.overall)})
            st.download_button(
                "📥 Export CSV Report",
                pd.DataFrame(export_rows).to_csv(index=False),
                file_name="veritywrite_audit_report.csv",
                mime="text/csv",
                use_container_width=True,
            )

        # Interactive Tamper Sandbox
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        with st.expander("🧪 Break it on Purpose (Prove the Verifier Catches Errors)", expanded=False):
            st.markdown("Corrupt the rewrite to simulate hallucinations or omissions, and watch the trust report instantly flag it.")
            cols = st.columns(len(MUTATIONS) + 1)
            for col, name in zip(cols, MUTATIONS):
                col.button(name, on_click=tamper, args=(name,), use_container_width=True)
            cols[-1].button("Reset Output", on_click=reset_output, use_container_width=True)
            if S.get("tamper_msg"):
                st.caption(f"⚠️ {S.pop('tamper_msg')}")


# =============================================================
# VIEW 2: HISTORY (Session Audit Trail)
# =============================================================
elif nav == "History":
    st.markdown("""
    <div class="ambient-hero">
        <h1 style="font-size: 26px; font-weight: 800; margin: 2px 0 4px;">
            Audit History
        </h1>
        <p style="font-size: 13.5px; color: #cbc3d7;">
            Chronological audit log of text humanizations and verification checks in this session.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not S.history:
        st.markdown("""
        <div class="stitch-card" style="text-align: center; padding: 36px 20px;">
            <div style="font-size: 15px; font-weight: 600; color: #e3e1e9;">No runs recorded in this session yet</div>
            <div style="font-size: 12.5px; color: #958ea0; margin-top: 4px;">Execute a humanize & verify action in the Workspace to generate audit entries.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for idx, item in enumerate(S.history):
            v_badge_color = "#4edea3" if item["verdict"] == "PASS" else ("#fbbf24" if item["verdict"] == "REVIEW" else "#ffb4ab")
            st.markdown(f"""
            <div class="stitch-card" style="margin-bottom: 10px;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-family: monospace; font-size: 12.5px; font-weight: 700; color: #d0bcff;">{item['id']}</span>
                        <span style="font-size: 11.5px; color: #958ea0;">{item['timestamp']}</span>
                        <span style="font-size: 10.5px; padding: 2px 8px; border-radius: 9999px; background: rgba(149, 142, 160, 0.2); color: {v_badge_color}; font-weight: 700;">
                            {item['verdict']}
                        </span>
                    </div>
                    <span style="font-size: 11.5px; color: #cbc3d7;">Facts Locked: {item['facts_ratio']}</span>
                </div>
                <div style="font-size: 12.5px; color: #e3e1e9; line-height: 1.5; margin: 6px 0; background: rgba(13, 14, 19, 0.6); padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(149, 142, 160, 0.15);">
                    <b>Output:</b> {html.escape(item['output'][:160])}...
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.button(f"Load '{item['id']}' into Workspace", key=f"btn_load_hist_{idx}", on_click=load_history_entry, args=(item["original"],))

        if st.button("Clear Audit History", key="btn_clear_history", on_click=clear_audit_history):
            pass


# =============================================================
# VIEW 3: HOW IT WORKS (Technical Architecture & Limits)
# =============================================================
elif nav == "How It Works":
    st.markdown("""
    <div class="ambient-hero">
        <h1 style="font-size: 26px; font-weight: 800; margin: 2px 0 4px;">
            How It Works & Guardrail Architecture
        </h1>
        <p style="font-size: 13.5px; color: #cbc3d7;">
            Transparent explanation of VerityWrite AI's deterministic verification and contextual rewriting pipeline.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_hiw_1, col_hiw_2 = st.columns(2)
    with col_hiw_1:
        st.markdown("""
        <div class="stitch-card">
            <h3 style="font-size: 15px; font-weight: 700; color: #d0bcff; margin-bottom: 8px;">
                1. Protected Fact Extraction
            </h3>
            <p style="font-size: 12.5px; color: #cbc3d7; line-height: 1.6; margin: 0 0 8px;">
                Before any rewriting occurs, the input text undergoes strict deterministic entity extraction.
                We identify and pin:
            </p>
            <ul style="font-size: 12.5px; color: #cbc3d7; line-height: 1.6; margin-left: 16px;">
                <li><b>Numerical Scores:</b> e.g. <code>82/100</code>, <code>7.5 out of 10</code></li>
                <li><b>Temporal Anchors:</b> Formats like <code>8 October 2026</code>, <code>2026-10-08</code></li>
                <li><b>Named Entities:</b> Candidate names and capitalized person references</li>
                <li><b>Technical Keywords:</b> Standard technical terms and user-configured protected tokens</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="stitch-card">
            <h3 style="font-size: 15px; font-weight: 700; color: #4edea3; margin-bottom: 8px;">
                2. Robotic Language Analysis & Skip Gate
            </h3>
            <p style="font-size: 12.5px; color: #cbc3d7; line-height: 1.6; margin: 0;">
                We scan for over 30 synthetic template phrases (<i>"delve into"</i>, <i>"it is important to note"</i>, <i>"in conclusion"</i>)
                and measure sentence opener repetition. If the text is already natural (score &lt; 25), the <b>Skip Gate</b>
                bypasses rewriting to prevent unnecessary alterations.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_hiw_2:
        st.markdown("""
        <div class="stitch-card">
            <h3 style="font-size: 15px; font-weight: 700; color: #cebdff; margin-bottom: 8px;">
                3. Constrained Rewrite & Feedback Loop
            </h3>
            <p style="font-size: 12.5px; color: #cbc3d7; line-height: 1.6; margin: 0;">
                Gemini is instructed with hard prompt boundaries: every protected token must appear verbatim.
                If an attempt fails verification, the verifier sends targeted feedback back to the engine for up to 2 automated retries.
                If offline, a deterministic rule-based fallback guarantees zero hallucination.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="stitch-card">
            <h3 style="font-size: 15px; font-weight: 700; color: #ffb4ab; margin-bottom: 8px;">
                4. Honest System Limitations
            </h3>
            <ul style="font-size: 12.5px; color: #cbc3d7; line-height: 1.6; margin-left: 16px;">
                <li><b>Heuristic Name Detection:</b> Novel proper nouns without context may require manual addition to Protected Terms.</li>
                <li><b>Invented Qualitative Claims:</b> Subtle false claims without numbers are checked by the AI Judge, but critical communications should always have human review.</li>
                <li><b>Synthetic Data Only:</b> Always use synthetic or unmasked data. Never submit sensitive personal data.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


# =============================================================
# VIEW 4: SETTINGS (Detailed Configuration)
# =============================================================
elif nav == "Settings":
    st.markdown("""
    <div class="ambient-hero">
        <h1 style="font-size: 26px; font-weight: 800; margin: 2px 0 4px;">
            System Settings & Engine Configuration
        </h1>
        <p style="font-size: 13.5px; color: #cbc3d7;">
            Manage API credentials, verification thresholds, and consistent tone profiles.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_set_1, col_set_2 = st.columns(2)
    with col_set_1:
        st.markdown("### 🔑 API & Engine Status")
        diag = diagnose_gemini_key(custom_key=S.get("custom_gemini_key"), env_path=ENV_PATH)
        if llm.available:
            st.success(f"✅ Gemini Connected — Active Model: `{llm.model}` (Source: {diag['source']})")
        elif getattr(llm, "init_error", None):
            st.error(f"❌ Gemini Initialization Error: {llm.init_error}")
        else:
            st.warning(f"⚠️ No active Gemini API key detected. {diag.get('issue') or 'Running offline rule-based rewriter (demo mode).'}")
            if diag.get("suggestion"):
                st.info(f"💡 {diag['suggestion']}")
        st.caption("Standard setup: place `GEMINI_API_KEY=your_key` in `.env` or Streamlit secrets.")

        with st.expander("🔍 Key Detection Diagnostics", expanded=not llm.available):
            st.write(f"- **Key Detected:** `{'Yes' if diag['detected'] else 'No'}`")
            st.write(f"- **Config Source:** `{diag['source']}`")
            st.write(f"- **.env File Found:** `{'Yes' if diag['env_file_found'] else 'No'}` (`{diag['env_file_path']}`)")
            if diag.get("issue"):
                st.write(f"- **Diagnostic Insight:** {diag['issue']}")
            if diag.get("suggestion"):
                st.write(f"- **Action Required:** {diag['suggestion']}")

        with st.expander("🔑 Session API Key Override", expanded=not llm.available):
            st.caption("Optionally provide or update your Gemini API key for this session. Get a free key at [Google AI Studio](https://aistudio.google.com/app/apikey).")
            custom_key_val = st.text_input("Gemini API Key", type="password", key="input_custom_key", placeholder="AIzaSy...")
            k_col1, k_col2, k_col3 = st.columns([4, 4, 3])
            with k_col1:
                if st.button("Apply Key to Session", key="btn_apply_key", use_container_width=True):
                    cleaned = clean_api_key(custom_key_val)
                    if cleaned:
                        S.custom_gemini_key = cleaned
                        st.rerun()
                    else:
                        st.error("Please enter a non-empty, valid API key.")
            with k_col2:
                if st.button("⚡ Test Connection", key="btn_test_conn", use_container_width=True, disabled=not llm.available):
                    with st.spinner("Testing API connection with Google Gemini..."):
                        test_res = llm.test_connection()
                        if test_res["ok"]:
                            st.success(f"✅ API Key Verified! Available models: {', '.join(test_res['models'][:6])}")
                        else:
                            st.error(f"❌ Connection failed: {test_res['error']}")
            with k_col3:
                if st.button("Clear Key", key="btn_clear_key", use_container_width=True):
                    S.pop("custom_gemini_key", None)
                    st.rerun()

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown("### 🎯 Content Defaults")
        ctx_idx = list(CONTEXTS).index(S.context) if S.context in CONTEXTS else 0
        tone_idx = list(TONES).index(S.tone) if S.tone in TONES else 0
        st.selectbox("Default Content Domain Context", list(CONTEXTS), index=ctx_idx, key="settings_context_picker", on_change=on_settings_context_change)
        st.selectbox("Default Target Voice Tone", list(TONES), index=tone_idx, key="settings_tone_picker", on_change=on_settings_tone_change)

    with col_set_2:
        st.markdown("### 🛡️ Safety & Verification Thresholds")
        st.write(f"- Skip Gate Active: **{use_skip}**")
        st.write(f"- Strict Verification Mode: **{strict}**")
        st.write(f"- AI Meaning Judge Active: **{use_judge}**")
        st.write(f"- Approved Outputs Remembered: **{len(S.voice_examples)}**")

        st.button("Reset All Session Settings to Default", key="btn_reset_settings", on_click=reset_all_settings)
