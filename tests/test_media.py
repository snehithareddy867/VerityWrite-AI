import io
import sys, pathlib, types, wave
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest
from core.llm import LLMError
from core import media
from core.media import MediaError, read_screenshot, text_to_speech, transcribe_audio


class FakeLLM:
    available = True

    def __init__(self, reply):
        self.reply, self.calls, self.audio_calls = reply, [], []

    def generate_json(self, contents, temperature=0.3):
        self.calls.append(contents)
        return self.reply

    def generate_audio_text(self, audio, mime_type, prompt):
        self.audio_calls.append((audio, mime_type, prompt))
        return str(self.reply.get("text", "")).strip()


class NoKey:
    available = False


def _wav_bytes(frames=b"\x00\x00" * 1600):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(frames)
    return buffer.getvalue()


def test_transcribe_returns_text_and_passes_audio_payload():
    llm = FakeLLM({"text": " Hello team. "})
    audio = _wav_bytes()
    assert transcribe_audio(llm, audio, "audio/wav") == "Hello team."
    sent_audio, sent_mime, prompt = llm.audio_calls[0]
    assert sent_audio == audio
    assert sent_mime == "audio/wav"
    assert "Transcribe this audio exactly" in prompt


def test_transcribe_errors():
    with pytest.raises(LLMError):
        transcribe_audio(NoKey(), b"x")
    with pytest.raises(MediaError):
        transcribe_audio(FakeLLM({"text": ""}), _wav_bytes())
    with pytest.raises(MediaError):
        transcribe_audio(FakeLLM({"text": "hi"}), b"")
    with pytest.raises(MediaError, match="malformed or unreadable"):
        transcribe_audio(FakeLLM({"text": "hi"}), b"not a wav file", "audio/wav")
    with pytest.raises(MediaError, match="Unsupported audio format"):
        transcribe_audio(FakeLLM({"text": "hi"}), b"\x1aE\xdf\xa3data", "audio/webm")


def test_transcribe_rejects_empty_wav_and_oversized_audio():
    with pytest.raises(MediaError, match="no audio frames"):
        transcribe_audio(FakeLLM({"text": "hi"}), _wav_bytes(b""))
    with pytest.raises(MediaError, match="too large"):
        transcribe_audio(FakeLLM({"text": "hi"}), b"x" * (media.MAX_AUDIO_BYTES + 1), "audio/wav")


def test_media_api_errors_are_reported_as_llm_errors():
    from google.genai import types
    from core.llm import LLMClient

    class FailingModels:
        def generate_content(self, **kwargs):
            raise RuntimeError("403 API_KEY_INVALID")

    class FailingInteractions:
        def create(self, **kwargs):
            raise RuntimeError("403 API_KEY_INVALID")

    class FailingClient:
        models = FailingModels()
        interactions = FailingInteractions()

    llm = LLMClient(api_key="")
    llm._types = types
    llm._client = FailingClient()

    with pytest.raises(LLMError, match="rejected the API key"):
        transcribe_audio(llm, _wav_bytes())
    with pytest.raises(LLMError, match="authentication failed"):
        read_screenshot(llm, b"png")


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
