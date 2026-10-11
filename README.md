# VerityWrite AI (Team Hackprime)
**Make AI sound natural. Keep every fact intact.**
Google Student Club Welcome Hackathon 2026, Problem Statement 2: AI Humanization & Natural Language Refinement.

## Pipeline
`Input -> FactLock (extract protected facts) -> Robotic-language detector -> Skip gate -> Contextual rewrite (Gemini)
-> Verify (deterministic checks + AI judge) -> Retry on failure -> Trust report + meaning diff`

| Requirement in the brief | Where |
|---|---|
| Robotic language detection | `core/analyzer.py` |
| Entity preservation / factuality protection | `core/facts.py`, `core/verifier.py` |
| Context-aware tone, configurable levels | `core/rewriter.py` (CONTEXTS, TONES) |
| Meaning/factuality check | `core/verifier.py` + `core/llm.py::judge` |
| Consistency | voice notes + earlier approved outputs fed into the prompt (`app.py`, `core/rewriter.py`) |
| Resistance to unnecessary rewriting | skip gate in `core/pipeline.py` |
| Voice in / voice out | `core/media.py` (Gemini speech-to-text, gTTS text-to-speech), UI in `app.py` |
| Screenshot to text or voice | `core/media.py::read_screenshot` (extract text or explain), UI in `app.py` |

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then paste your Gemini key (https://aistudio.google.com/apikey)
streamlit run app.py
```
Without a key the app still runs in offline demo mode (basic rule-based rewriter; verification works fully).

## Readability dashboard
The results section opens with a Multi-Readability Suite: six formulas (Flesch Reading Ease, Flesch-Kincaid, Gunning Fog, SMOG, Coleman-Liau, ARI), an overall score gauge, and the original-vs-rewrite comparison. Scores are calculated locally in `core/readability.py`; the HTML lives in `core/readview.py`. *Export results* downloads a CSV and *Copy all scores* copies them as text.

## Voice and screenshots
- **Speak:** record in the app, click *Transcribe*; the transcript lands in the text box so you can edit it before humanizing.
- **Listen:** every rewrite (and screenshot result) has a 🔊 button that reads it aloud.
- **Screenshot:** upload an image, choose *Extract the text* or *Explain what it shows*, then listen to it or send it to the rewriter.
- Voice input and screenshot reading need a Gemini key; listening uses gTTS and needs internet access.
- Audio and images are sent to Gemini, so use synthetic or non-sensitive content only.

## Test and evaluate
```bash
python -m pytest -q
python eval/run_eval.py            # writes eval/results.md (uses Gemini if a key is set)
```

## Deploy (Streamlit Community Cloud)
1. Push to GitHub. 2. share.streamlit.io -> New app -> pick repo, branch `main`, file `app.py`.
3. Advanced settings -> Secrets: `GEMINI_API_KEY = "..."`. 4. Deploy, then open the URL on your phone to test.

## Responsible AI
Synthetic data only. Observations (detected facts) are separated from conclusions (verdicts); anything uncertain is
marked REVIEW; BLOCKED output is never presented as approved; a human reviews before sending. Limits: names are found
heuristically; invented claims with no number/date/name rely on the AI judge and human review.

## Owners
See `TEAM.md`.
