from pathlib import Path
from types import SimpleNamespace

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def _mock_audio_input(monkeypatch):
    import streamlit

    monkeypatch.setattr(
        streamlit,
        "audio_input",
        lambda *args, **kwargs: SimpleNamespace(
            type="audio/wav",
            getvalue=lambda: b"mock audio bytes",
        ),
    )


def _transcribe_button(app):
    return next(button for button in app.button if button.key == "btn_transcribe_voice")


def test_voice_transcribe_ui_shows_busy_state_and_delivers_transcript(monkeypatch):
    import core.media
    import streamlit

    monkeypatch.setenv("GEMINI_API_KEY", "mock_ui_test_key")
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    _mock_audio_input(monkeypatch)
    busy_states = []

    def transcribe(*args, **kwargs):
        busy_states.append(streamlit.session_state["voice_transcribing"])
        return "Mock transcript from audio."

    monkeypatch.setattr(core.media, "transcribe_audio", transcribe)
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()

    assert not _transcribe_button(app).disabled
    _transcribe_button(app).click().run()

    assert not app.exception
    assert busy_states == [True]
    assert app.session_state["voice_transcribed_text"] == "Mock transcript from audio."
    assert any(
        widget.key == "input_text" and widget.value == "Mock transcript from audio."
        for widget in app.text_area
    )


def test_voice_transcribe_ui_displays_api_failure(monkeypatch):
    import core.media
    from core.llm import LLMError

    monkeypatch.setenv("GEMINI_API_KEY", "mock_ui_test_key")
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    _mock_audio_input(monkeypatch)

    def transcribe(*args, **kwargs):
        raise LLMError("Mock Gemini failure.")

    monkeypatch.setattr(core.media, "transcribe_audio", transcribe)
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    _transcribe_button(app).click().run()

    assert not app.exception
    assert any("Transcription error: Mock Gemini failure." in item.value for item in app.error)
    assert app.session_state["voice_transcribed_text"] == ""


def test_voice_transcribe_controls_are_disabled_while_busy(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "mock_ui_test_key")
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    _mock_audio_input(monkeypatch)

    app = AppTest.from_file(APP_PATH, default_timeout=30)
    app.session_state["voice_transcribing"] = True
    app.run()

    assert _transcribe_button(app).disabled
    run_button = next(button for button in app.button if button.key == "btn_transcribe_and_run")
    assert run_button.disabled


def test_voice_transcript_flows_into_workspace_and_pipeline(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GOOGLE_API_KEY", "")

    app = AppTest.from_file(APP_PATH, default_timeout=30)
    app.session_state["pending_text"] = "The transcript is ready for review."
    app.session_state["pending_humanize"] = True
    app.run()

    assert not app.exception
    assert any(
        widget.key == "input_text"
        and widget.value == "The transcript is ready for review."
        for widget in app.text_area
    )
    assert app.session_state["result"] is not None

    transcribe_button = next(button for button in app.button if button.label.endswith("Transcribe"))
    assert transcribe_button.disabled
