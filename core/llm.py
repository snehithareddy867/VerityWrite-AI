"""Thin Gemini wrapper. Everything degrades gracefully when no key / API failure."""
from __future__ import annotations

import json
import os
import re
import time


from pathlib import Path
try:
    from dotenv import load_dotenv
    _root_env = Path(__file__).resolve().parent.parent / ".env"
    if _root_env.is_file():
        load_dotenv(dotenv_path=_root_env)
except Exception:
    pass


class LLMError(Exception):
    pass


DEFAULT_MODEL = "gemini-2.0-flash"


def clean_api_key(val: str | None) -> str:
    """Safely sanitize an API key string, stripping whitespace and surrounding quotes."""
    if not val:
        return ""
    cleaned = str(val).strip()
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1].strip()
    return cleaned


def get_gemini_api_key(custom_key: str | None = None) -> str:
    """Resolve Gemini API key consistently across the app.
    Precedence:
    1. Explicit custom key (e.g. from session override)
    2. Streamlit secrets (GEMINI_API_KEY, GOOGLE_API_KEY)
    3. Environment variables (GEMINI_API_KEY, GOOGLE_API_KEY)
    Returns empty string if no valid key is found. Never logs or prints the key.
    """
    clean_custom = clean_api_key(custom_key)
    if clean_custom:
        return clean_custom

    # Streamlit secrets check (if streamlit is active/configured)
    try:
        import streamlit as st
        for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            if var in st.secrets and st.secrets[var]:
                cleaned = clean_api_key(st.secrets[var])
                if cleaned:
                    return cleaned
    except Exception:
        pass

    # Environment variables
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        val = os.getenv(var)
        cleaned = clean_api_key(val)
        if cleaned:
            return cleaned

    return ""


def diagnose_gemini_key(custom_key: str | None = None, env_path: Path | str | None = None) -> dict:
    """Safe diagnostic that reports detection status and configuration issues.
    Never exposes, prints, or returns the actual secret key value.
    """
    if env_path is None:
        env_path = Path(__file__).resolve().parent.parent / ".env"
    else:
        env_path = Path(env_path)

    # 1. Check custom key
    if custom_key and clean_api_key(custom_key):
        return {
            "detected": True,
            "source": "Session API Key Override",
            "variable_name": "custom_key",
            "env_file_found": env_path.is_file(),
            "env_file_path": str(env_path),
            "issue": None,
            "suggestion": None,
        }

    # 2. Check Streamlit secrets
    try:
        import streamlit as st
        for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            if var in st.secrets and st.secrets[var]:
                if clean_api_key(st.secrets[var]):
                    return {
                        "detected": True,
                        "source": f"Streamlit Secrets ({var})",
                        "variable_name": var,
                        "env_file_found": env_path.is_file(),
                        "env_file_path": str(env_path),
                        "issue": None,
                        "suggestion": None,
                    }
    except Exception:
        pass

    # 3. Check environment variables
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        val = os.getenv(var)
        if val is not None and clean_api_key(val):
            return {
                "detected": True,
                "source": f"Environment / .env ({var})",
                "variable_name": var,
                "env_file_found": env_path.is_file(),
                "env_file_path": str(env_path),
                "issue": None,
                "suggestion": None,
            }

    # 4. If key is NOT detected, inspect .env file for specific actionable diagnostics
    env_exists = env_path.is_file()
    if not env_exists:
        return {
            "detected": False,
            "source": "None",
            "variable_name": "None",
            "env_file_found": False,
            "env_file_path": str(env_path),
            "issue": f"No .env file found at {env_path.name} ({env_path}).",
            "suggestion": "Create a .env file with GEMINI_API_KEY=your_key or configure secrets in Streamlit.",
        }

    try:
        content = env_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {
            "detected": False,
            "source": "None",
            "variable_name": "None",
            "env_file_found": True,
            "env_file_path": str(env_path),
            "issue": f"Could not read .env file: {e}",
            "suggestion": "Check file permissions for .env.",
        }

    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]
    parsed_vars = {}
    for line in lines:
        if "=" in line:
            k, v = line.split("=", 1)
            parsed_vars[k.strip()] = clean_api_key(v)

    if "GEMINI_API_KEY" in parsed_vars:
        if not parsed_vars["GEMINI_API_KEY"]:
            return {
                "detected": False,
                "source": "None",
                "variable_name": "GEMINI_API_KEY",
                "env_file_found": True,
                "env_file_path": str(env_path),
                "issue": ".env file exists, but GEMINI_API_KEY is empty or contains only whitespace.",
                "suggestion": "Open your .env file and set GEMINI_API_KEY=your_key_here, or provide a key in Settings.",
            }

    if "GOOGLE_API_KEY" in parsed_vars:
        if not parsed_vars["GOOGLE_API_KEY"]:
            return {
                "detected": False,
                "source": "None",
                "variable_name": "GOOGLE_API_KEY",
                "env_file_found": True,
                "env_file_path": str(env_path),
                "issue": ".env file exists, but GOOGLE_API_KEY is empty or contains only whitespace.",
                "suggestion": "Open your .env file and set GEMINI_API_KEY=your_key_here, or provide a key in Settings.",
            }

    # Check for suspected typos or common alternative names
    suspect_names = ["GEMINI_KEY", "API_KEY", "GEMINI_TOKEN", "GEMINI_API_TOKEN", "GOOGLE_KEY", "GOOGLE_API"]
    for s in suspect_names:
        if s in parsed_vars:
            return {
                "detected": False,
                "source": "None",
                "variable_name": s,
                "env_file_found": True,
                "env_file_path": str(env_path),
                "issue": f"Found '{s}' in .env, but VerityWrite requires 'GEMINI_API_KEY' (or 'GOOGLE_API_KEY').",
                "suggestion": f"Rename '{s}' to 'GEMINI_API_KEY' in your .env file.",
            }

    return {
        "detected": False,
        "source": "None",
        "variable_name": "None",
        "env_file_found": True,
        "env_file_path": str(env_path),
        "issue": ".env file exists, but neither GEMINI_API_KEY nor GOOGLE_API_KEY is defined.",
        "suggestion": "Add GEMINI_API_KEY=your_key to your .env file.",
    }


def _parse_json(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        return {"text": ""}
    cleaned = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    a, b = cleaned.find("{"), cleaned.rfind("}")
    if a != -1 and b > a:
        try:
            parsed = json.loads(cleaned[a:b + 1])
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    # If model emitted plain text without JSON structure, wrap in {"text": ...}
    return {"text": cleaned}


class LLMClient:
    def __init__(self, api_key: str | None = None, model: str | None = None, timeout_s: int = 30):
        if api_key is None:
            resolved = get_gemini_api_key()
        else:
            resolved = clean_api_key(api_key)
        self.api_key = resolved or None
        chosen = (model or os.getenv("GEMINI_MODEL") or "").strip()
        # Correct legacy or invalid placeholder model
        if not chosen or chosen == "gemini-2.5-flash":
            chosen = DEFAULT_MODEL
        self.model = chosen
        self.init_error = ""
        self._client = None
        if self.api_key:
            try:
                from google import genai
                from google.genai import types
                self._types = types
                self._client = genai.Client(api_key=self.api_key,
                                            http_options=types.HttpOptions(timeout=timeout_s * 1000))
            except Exception as e:  # missing package, bad key format, etc.
                self.init_error = str(e)

    @property
    def available(self) -> bool:
        return self._client is not None

    def test_connection(self) -> dict:
        """Test API connectivity and retrieve available generateContent models."""
        if not self.available:
            return {"ok": False, "error": "No Gemini API key configured."}
        try:
            models = []
            for m in self._client.models.list():
                name = getattr(m, "name", "") or str(m)
                short = name.split("/")[-1] if "/" in name else name
                methods = getattr(m, "supported_generation_methods", []) or getattr(m, "supported_actions", []) or []
                models.append(short)
            return {"ok": True, "models": models[:12]}
        except Exception as e:
            err = str(e)
            hint = ""
            if "404" in err or "NOT_FOUND" in err:
                hint = ("\n\n💡 Google returned 404 NOT_FOUND: Ensure 'Generative Language API' is enabled in your Google Cloud project, "
                        "or generate a standard API key from Google AI Studio: https://aistudio.google.com/app/apikey")
            elif "400" in err or "403" in err or "API_KEY_INVALID" in err:
                hint = "\n\n💡 Authentication failed: Check that the API key was copied completely and has not expired."
            return {"ok": False, "error": f"{err}{hint}"}

    def generate_json(self, prompt: str | list, temperature: float = 0.3) -> dict:
        if not self.available:
            raise LLMError("No Gemini API key configured")
        last = None
        models_to_try = [self.model]
        for fallback_m in ("gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash"):
            if fallback_m not in models_to_try:
                models_to_try.append(fallback_m)

        for current_model in models_to_try:
            try:
                resp = self._client.models.generate_content(
                    model=current_model, contents=prompt,
                    config=self._types.GenerateContentConfig(
                        temperature=temperature, response_mime_type="application/json"))
                self.model = current_model
                raw_text = ""
                try:
                    raw_text = resp.text or ""
                except Exception:
                    # When text property raises or is empty, extract from parts
                    if getattr(resp, "candidates", None) and resp.candidates:
                        c = resp.candidates[0]
                        if getattr(c, "content", None) and getattr(c.content, "parts", None):
                            raw_text = "".join(getattr(p, "text", "") for p in c.content.parts if getattr(p, "text", None))
                return _parse_json(raw_text)
            except LLMError as e:
                last = e
            except Exception as e:
                err_str = str(e)
                if "API_KEY_INVALID" in err_str or "400" in err_str or "403" in err_str:
                    last = LLMError(f"Gemini authentication failed: {err_str}")
                    break
                if "404" in err_str or "not found" in err_str.lower():
                    last = LLMError(
                        f"Gemini model '{current_model}' returned 404 NOT_FOUND. "
                        "This typically indicates that the 'Generative Language API' is not enabled for this project, "
                        "or the API key has restricted access. Get a key from Google AI Studio: https://aistudio.google.com/app/apikey"
                    )
                    continue
                last = LLMError(f"Gemini call failed: {err_str}")
            time.sleep(0.5)
        raise last or LLMError("Unknown LLM error")


JUDGE_PROMPT = """You are a strict fact-checker. Compare ORIGINAL and REWRITE.
Return ONLY JSON: {{"meaning_preserved": true|false, "added_claims": [str], "removed_claims": [str], "notes": str}}
- added_claims: statements in REWRITE that the ORIGINAL does not support (achievements, praise, reasons, results).
- removed_claims: important statements in ORIGINAL that REWRITE dropped or weakened.
- Do not penalize wording changes that keep the same meaning.

ORIGINAL:
{source}

REWRITE:
{output}
"""


def judge(llm: LLMClient, source: str, output: str) -> dict | None:
    """Independent semantic check. Returns None if unavailable (never blocks on failure)."""
    if not llm or not llm.available:
        return None
    try:
        d = llm.generate_json(JUDGE_PROMPT.format(source=source, output=output), temperature=0.0)
        return {
            "meaning_preserved": bool(d.get("meaning_preserved", True)),
            "added_claims": [str(x) for x in d.get("added_claims", []) or []],
            "removed_claims": [str(x) for x in d.get("removed_claims", []) or []],
            "notes": str(d.get("notes", "")),
        }
    except LLMError:
        return None
