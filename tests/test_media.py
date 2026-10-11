import sys, pathlib, types
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest
from core.llm import LLMError
from core import media
from core.media import MediaError, read_screenshot, text_to_speech, transcribe_audio


class FakeLLM:
    available = True

    def __init__(self, reply):
        self.reply, self.calls = reply, []

    def generate_json(self, contents, temperature=0.3):
        self.calls.append(contents)
        return self.reply


class NoKey:
    available = False


def test_transcribe_returns_text_and_sends_audio_part():
    llm = FakeLLM({"text": " Hello team. "})
    assert transcribe_audio(llm, b"RIFFxxxx") == "Hello team."
    assert len(llm.calls[0]) == 2  # [audio part, prompt]


def test_transcribe_errors():
    with pytest.raises(LLMError):
        transcribe_audio(NoKey(), b"x")
    with pytest.raises(MediaError):
        transcribe_audio(FakeLLM({"text": ""}), b"x")
    with pytest.raises(MediaError):
        transcribe_audio(FakeLLM({"text": "hi"}), b"")


def test_read_screenshot_modes_and_errors():
    llm = FakeLLM({"text": "Score: 82/100"})
    assert read_screenshot(llm, b"png", "image/png", "Extract the text") == "Score: 82/100"
    assert read_screenshot(llm, b"png", "image/png", "Explain what it shows") == "Score: 82/100"
    with pytest.raises(MediaError):
        read_screenshot(llm, b"png", mode="bogus")
    with pytest.raises(MediaError):
        read_screenshot(FakeLLM({"text": ""}), b"png")
    with pytest.raises(MediaError):
        read_screenshot(llm, b"x" * (media.MAX_IMAGE_BYTES + 1))
    with pytest.raises(LLMError):
        read_screenshot(NoKey(), b"png")


def _fake_gtts(monkeypatch, record):
    class G:
        def __init__(self, text, lang):
            record.update(text=text, lang=lang)

        def write_to_fp(self, fp):
            fp.write(b"MP3")
    monkeypatch.setitem(sys.modules, "gtts", types.SimpleNamespace(gTTS=G))


def test_tts_returns_bytes_and_trims_long_text(monkeypatch):
    rec = {}
    _fake_gtts(monkeypatch, rec)
    assert text_to_speech("Hello there.") == b"MP3" and rec["lang"] == "en"
    text_to_speech("Short sentence. " * 1000)
    assert len(rec["text"]) <= media.MAX_TTS_CHARS and rec["text"].endswith(".")


def test_tts_empty_and_failure(monkeypatch):
    with pytest.raises(MediaError):
        text_to_speech("   ")

    class Boom:
        def __init__(self, **k):
            raise RuntimeError("offline")
    monkeypatch.setitem(sys.modules, "gtts", types.SimpleNamespace(gTTS=Boom))
    with pytest.raises(MediaError):
        text_to_speech("hi")


def test_audio_mime_normalization():
    assert media.normalize_audio_mime("audio/webm;codecs=opus", b"") == "audio/webm"
    assert media.normalize_audio_mime("audio/wav", b"") == "audio/wav"
    assert media.normalize_audio_mime(None, b"RIFF1234WAVEfmt ") == "audio/wav"
    assert media.normalize_audio_mime(None, b"\x1aE\xdf\xa3dummy") == "audio/webm"
    assert media.normalize_audio_mime(None, b"OggSdummy") == "audio/ogg"
    assert media.normalize_audio_mime(None, b"ID3dummy") == "audio/mp3"


def test_image_mime_normalization():
    assert media.normalize_image_mime("image/jpg", b"") == "image/jpeg"
    assert media.normalize_image_mime("image/pjpeg", b"") == "image/jpeg"
    assert media.normalize_image_mime("image/png", b"") == "image/png"
    assert media.normalize_image_mime(None, b"\x89PNG\r\n\x1a\n") == "image/png"
    assert media.normalize_image_mime(None, b"\xff\xd8\xff") == "image/jpeg"
    assert media.normalize_image_mime(None, b"RIFF1234WEBP") == "image/webp"


def test_read_screenshot_invalid_image_fails_cleanly():
    llm = FakeLLM({"text": "anything"})
    corrupt_image_bytes = b"This is plain text and definitely not an image file (over 16 bytes)"
    with pytest.raises(MediaError) as exc:
        read_screenshot(llm, corrupt_image_bytes)
    assert "not a valid or readable image" in str(exc.value)


def test_read_screenshot_valid_image_success():
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (20, 20), color="blue").save(buf, format="PNG")
    valid_png = buf.getvalue()

    llm = FakeLLM({"text": "Invoice #4402 Total: $120.00"})
    extracted = read_screenshot(llm, valid_png, "image/png", "Extract the text")
    assert extracted == "Invoice #4402 Total: $120.00"


def test_llm_json_parsing_resilience():
    from core.llm import _parse_json
    # Standard JSON
    assert _parse_json('{"text": "transcribed speech"}') == {"text": "transcribed speech"}
    # Code block wrapped
    assert _parse_json('```json\n{"text": "wrapped"}\n```') == {"text": "wrapped"}
    # Plain text without JSON brackets (Gemini multimodal fallback)
    assert _parse_json("Direct transcription text without json") == {"text": "Direct transcription text without json"}
    # Empty
    assert _parse_json("") == {"text": ""}
