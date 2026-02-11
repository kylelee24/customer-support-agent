"""Tests for backend.helpers — ACS <-> OpenAI format transforms."""

from backend.helpers import transform_acs_to_openai_format, transform_openai_to_acs_format
from backend.tools.tools import Tool


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_tool(name: str = "test_tool") -> Tool:
    schema = {"type": "function", "name": name, "parameters": {}}
    return Tool(target=lambda a: None, schema=schema)


# ── transform_acs_to_openai_format ───────────────────────────────────────────

class TestAcsToOpenai:
    def test_audio_metadata_returns_session_update(self):
        msg = {"kind": "AudioMetadata", "audioMetadata": {"subscriptionId": "sub1"}}
        tools = {"t": _make_tool()}
        result = transform_acs_to_openai_format(
            msg, model="gpt-4o", tools=tools,
            system_message="Be helpful.", temperature=0.7,
            max_tokens=100, disable_audio=None, voice="sage",
        )
        assert result["type"] == "session.update"
        session = result["session"]
        assert session["voice"] == "sage"
        assert session["tool_choice"] == "auto"
        assert len(session["tools"]) == 1
        assert session["instructions"] == "Be helpful."
        assert session["temperature"] == 0.7
        assert session["max_response_output_tokens"] == 100

    def test_audio_metadata_no_optional_params(self):
        msg = {"kind": "AudioMetadata", "audioMetadata": {}}
        result = transform_acs_to_openai_format(
            msg, model=None, tools={},
            system_message=None, temperature=None,
            max_tokens=None, disable_audio=None, voice="alloy",
        )
        session = result["session"]
        assert "instructions" not in session
        assert "temperature" not in session
        assert "max_response_output_tokens" not in session
        assert session["tool_choice"] == "none"
        assert session["tools"] == []

    def test_audio_metadata_includes_turn_detection(self):
        msg = {"kind": "AudioMetadata", "audioMetadata": {}}
        result = transform_acs_to_openai_format(
            msg, model=None, tools={},
            system_message=None, temperature=None,
            max_tokens=None, disable_audio=None, voice="sage",
        )
        td = result["session"]["turn_detection"]
        assert td["type"] == "server_vad"
        assert "threshold" in td

    def test_audio_metadata_disable_audio(self):
        msg = {"kind": "AudioMetadata", "audioMetadata": {}}
        result = transform_acs_to_openai_format(
            msg, model=None, tools={},
            system_message=None, temperature=None,
            max_tokens=None, disable_audio=True, voice="sage",
        )
        assert result["session"]["disable_audio"] is True

    def test_audio_data_returns_buffer_append(self):
        msg = {"kind": "AudioData", "audioData": {"data": "AQID"}}
        result = transform_acs_to_openai_format(
            msg, model=None, tools={},
            system_message=None, temperature=None,
            max_tokens=None, disable_audio=None, voice="sage",
        )
        assert result["type"] == "input_audio_buffer.append"
        assert result["audio"] == "AQID"

    def test_unknown_kind_returns_none(self):
        msg = {"kind": "SomethingElse"}
        result = transform_acs_to_openai_format(
            msg, model=None, tools={},
            system_message=None, temperature=None,
            max_tokens=None, disable_audio=None, voice="sage",
        )
        assert result is None


# ── transform_openai_to_acs_format ───────────────────────────────────────────

class TestOpenaiToAcs:
    def test_audio_delta_returns_audio_data(self):
        msg = {"type": "response.audio.delta", "delta": "base64data=="}
        result = transform_openai_to_acs_format(msg)
        assert result["kind"] == "AudioData"
        assert result["audioData"]["data"] == "base64data=="

    def test_speech_started_returns_stop_audio(self):
        msg = {"type": "input_audio_buffer.speech_started"}
        result = transform_openai_to_acs_format(msg)
        assert result["kind"] == "StopAudio"
        assert result["stopAudio"] == {}

    def test_other_type_returns_none(self):
        msg = {"type": "session.created"}
        result = transform_openai_to_acs_format(msg)
        assert result is None

    def test_response_done_returns_none(self):
        msg = {"type": "response.done"}
        result = transform_openai_to_acs_format(msg)
        assert result is None
