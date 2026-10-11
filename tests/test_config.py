from __future__ import annotations

import os
import sys
import pathlib
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from core.llm import LLMClient, LLMError, clean_api_key, diagnose_gemini_key, get_gemini_api_key


def test_clean_api_key():
    assert clean_api_key(None) == ""
    assert clean_api_key("") == ""
    assert clean_api_key("   ") == ""
    assert clean_api_key("  \t\n  ") == ""
    assert clean_api_key("valid_api_key_123") == "valid_api_key_123"
    assert clean_api_key("  valid_api_key_123  ") == "valid_api_key_123"
    assert clean_api_key('"quoted_key_456"') == "quoted_key_456"
    assert clean_api_key("'single_quoted_789'") == "single_quoted_789"
    assert clean_api_key(' " nested_quoted " ') == "nested_quoted"


def test_get_gemini_api_key_from_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "dummy_gemini_key_test")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert get_gemini_api_key() == "dummy_gemini_key_test"


def test_get_gemini_api_key_fallback_to_google(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy_google_key_fallback")
    assert get_gemini_api_key() == "dummy_google_key_fallback"


def test_get_gemini_api_key_gemini_takes_precedence_over_google(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "primary_gemini_key")
    monkeypatch.setenv("GOOGLE_API_KEY", "fallback_google_key")
    assert get_gemini_api_key() == "primary_gemini_key"


def test_get_gemini_api_key_empty_or_whitespace(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "   ")
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    assert get_gemini_api_key() == ""


def test_get_gemini_api_key_custom_key_override(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env_key")
    assert get_gemini_api_key(custom_key="override_key_from_session") == "override_key_from_session"


def test_diagnose_gemini_key_when_present(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "mock_key_present")
    fake_env = tmp_path / ".env"
    fake_env.write_text("GEMINI_API_KEY=mock_key_present", encoding="utf-8")

    diag = diagnose_gemini_key(env_path=fake_env)
    assert diag["detected"] is True
    assert "GEMINI_API_KEY" in diag["source"]
    assert diag["issue"] is None


def test_diagnose_gemini_key_empty_in_env_file(monkeypatch, tmp_path):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    fake_env = tmp_path / ".env"
    fake_env.write_text("GEMINI_API_KEY=\n# comments", encoding="utf-8")

    diag = diagnose_gemini_key(env_path=fake_env)
    assert diag["detected"] is False
    assert diag["env_file_found"] is True
    assert "empty or contains only whitespace" in diag["issue"]
    assert diag["suggestion"] is not None


def test_diagnose_gemini_key_missing_env_file(monkeypatch, tmp_path):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    fake_env = tmp_path / "non_existent.env"

    diag = diagnose_gemini_key(env_path=fake_env)
    assert diag["detected"] is False
    assert diag["env_file_found"] is False
    assert "No .env file found" in diag["issue"]


def test_diagnose_gemini_key_suspect_variable_name(monkeypatch, tmp_path):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    fake_env = tmp_path / ".env"
    fake_env.write_text("GEMINI_KEY=my_secret_key", encoding="utf-8")

    diag = diagnose_gemini_key(env_path=fake_env)
    assert diag["detected"] is False
    assert "Found 'GEMINI_KEY' in .env" in diag["issue"]
    assert "Rename 'GEMINI_KEY' to 'GEMINI_API_KEY'" in diag["suggestion"]


def test_llm_client_available_with_explicit_key():
    llm = LLMClient(api_key="mock_test_key_for_client")
    assert llm.api_key == "mock_test_key_for_client"
    assert llm.available is True


def test_llm_client_unavailable_with_empty_key():
    llm = LLMClient(api_key="")
    assert llm.api_key is None
    assert llm.available is False


def test_llm_client_resolves_env_when_no_arg(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "auto_resolved_env_key")
    llm = LLMClient()
    assert llm.api_key == "auto_resolved_env_key"
    assert llm.available is True
