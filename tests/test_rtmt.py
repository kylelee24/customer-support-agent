"""Tests for backend.rtmt — transcript capture and session management."""

from unittest.mock import MagicMock

import pytest

from backend.rtmt import RTMiddleTier
from backend.transcript_manager import TranscriptManager


# ── _capture_transcript ──────────────────────────────────────────────────────

class TestCaptureTranscript:
    @pytest.fixture
    def setup(self, rtmt, mock_ws, transcript_manager):
        """Wire up RTMiddleTier with a real TranscriptManager and a mock ws."""
        rtmt.transcript_manager = transcript_manager
        rtmt.set_session_id(mock_ws, "session-1")
        return rtmt, mock_ws, transcript_manager

    def test_user_audio_transcription(self, setup):
        rtmt, ws, tm = setup
        msg = {
            "type": "conversation.item.input_audio_transcription.completed",
            "transcript": "Hello agent",
        }
        rtmt._capture_transcript(msg, ws)
        entries = tm.get_transcript("session-1")
        assert len(entries) == 1
        assert entries[0].speaker == "user"
        assert entries[0].text == "Hello agent"

    def test_assistant_audio_delta_then_done(self, setup):
        rtmt, ws, tm = setup
        # Send deltas
        rtmt._capture_transcript({
            "type": "response.audio_transcript.delta",
            "delta": "Hi ",
            "response_id": "r1",
        }, ws)
        rtmt._capture_transcript({
            "type": "response.audio_transcript.delta",
            "delta": "there!",
            "response_id": "r1",
        }, ws)
        # Done without explicit transcript — should flush buffer
        rtmt._capture_transcript({
            "type": "response.audio_transcript.done",
            "response_id": "r1",
        }, ws)

        entries = tm.get_transcript("session-1")
        assert len(entries) == 1
        assert entries[0].speaker == "assistant"
        assert entries[0].text == "Hi there!"

    def test_assistant_audio_done_with_explicit_transcript(self, setup):
        rtmt, ws, tm = setup
        rtmt._capture_transcript({
            "type": "response.audio_transcript.done",
            "response_id": "r2",
            "transcript": "Explicit text",
        }, ws)
        entries = tm.get_transcript("session-1")
        assert len(entries) == 1
        assert entries[0].text == "Explicit text"

    def test_conversation_item_created_input_text(self, setup):
        rtmt, ws, tm = setup
        msg = {
            "type": "conversation.item.created",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "Type this"}],
            },
        }
        rtmt._capture_transcript(msg, ws)
        entries = tm.get_transcript("session-1")
        assert len(entries) == 1
        assert entries[0].speaker == "user"
        assert entries[0].text == "Type this"

    def test_no_transcript_manager(self, rtmt, mock_ws):
        """No transcript_manager set — should silently return."""
        rtmt.transcript_manager = None
        msg = {
            "type": "conversation.item.input_audio_transcription.completed",
            "transcript": "Ignored",
        }
        # Should not raise
        rtmt._capture_transcript(msg, mock_ws)

    def test_no_session_in_map(self, rtmt, mock_ws, transcript_manager):
        """WebSocket not in _session_map — should silently return."""
        rtmt.transcript_manager = transcript_manager
        # Don't call set_session_id
        msg = {
            "type": "conversation.item.input_audio_transcription.completed",
            "transcript": "Ignored",
        }
        rtmt._capture_transcript(msg, mock_ws)
        # No session created, no entries
        assert len(transcript_manager.transcripts) == 0

    def test_audio_done_clears_buffer(self, setup):
        rtmt, ws, tm = setup
        rtmt._capture_transcript({
            "type": "response.audio_transcript.delta",
            "delta": "Part 1",
            "response_id": "r3",
        }, ws)
        rtmt._capture_transcript({
            "type": "response.audio_transcript.done",
            "response_id": "r3",
        }, ws)
        # Buffer should be cleared
        assert all("r3" not in k for k in rtmt._transcript_buffer)


# ── Session management ───────────────────────────────────────────────────────

class TestSessionManagement:
    def test_set_and_get_session_id(self, rtmt, mock_ws, transcript_manager):
        rtmt.transcript_manager = transcript_manager
        rtmt.set_session_id(mock_ws, "sess-abc", {"phone": "+1"})
        assert rtmt.get_session_id(mock_ws) == "sess-abc"
        assert "sess-abc" in transcript_manager.transcripts

    def test_get_session_id_unknown(self, rtmt, mock_ws):
        assert rtmt.get_session_id(mock_ws) is None

    def test_close_session(self, rtmt, mock_ws, transcript_manager):
        rtmt.transcript_manager = transcript_manager
        rtmt.set_session_id(mock_ws, "sess-close")
        transcript_manager.add_entry("sess-close", "user", "Bye")
        rtmt.close_session(mock_ws)
        assert mock_ws not in rtmt._session_map

    def test_close_session_no_transcript_manager(self, rtmt, mock_ws):
        """close_session with no transcript_manager should not error."""
        rtmt._session_map[mock_ws] = "some-session"
        rtmt.close_session(mock_ws)
        assert mock_ws not in rtmt._session_map
