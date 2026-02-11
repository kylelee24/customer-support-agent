"""Tests for backend.transcript_manager — TranscriptEntry, TranscriptManager."""

import json

import pytest

from backend.transcript_manager import TranscriptEntry, TranscriptManager


# ── TranscriptEntry ──────────────────────────────────────────────────────────

class TestTranscriptEntry:
    def test_to_dict(self):
        entry = TranscriptEntry("user", "Hello!", "2025-01-01T00:00:00")
        d = entry.to_dict()
        assert d == {
            "speaker": "user",
            "text": "Hello!",
            "timestamp": "2025-01-01T00:00:00",
        }

    def test_attributes(self):
        entry = TranscriptEntry("assistant", "Hi there", "ts1")
        assert entry.speaker == "assistant"
        assert entry.text == "Hi there"
        assert entry.timestamp == "ts1"


# ── TranscriptManager: session lifecycle ─────────────────────────────────────

class TestSessionLifecycle:
    def test_create_session(self, transcript_manager):
        transcript_manager.create_session("s1")
        assert "s1" in transcript_manager.transcripts
        assert transcript_manager.transcripts["s1"] == []

    def test_create_session_with_metadata(self, transcript_manager):
        transcript_manager.create_session("s1", {"phone": "+1234"})
        assert transcript_manager.session_metadata["s1"]["phone"] == "+1234"

    def test_add_entry(self, transcript_manager):
        transcript_manager.create_session("s1")
        transcript_manager.add_entry("s1", "user", "Hello")
        entries = transcript_manager.get_transcript("s1")
        assert len(entries) == 1
        assert entries[0].speaker == "user"
        assert entries[0].text == "Hello"

    def test_add_entry_strips_whitespace(self, transcript_manager):
        transcript_manager.create_session("s1")
        transcript_manager.add_entry("s1", "user", "  Hi  ")
        assert transcript_manager.get_transcript("s1")[0].text == "Hi"

    def test_add_entry_skips_empty(self, transcript_manager):
        transcript_manager.create_session("s1")
        transcript_manager.add_entry("s1", "user", "")
        transcript_manager.add_entry("s1", "user", "   ")
        assert len(transcript_manager.get_transcript("s1")) == 0

    def test_add_entry_auto_creates_session(self, transcript_manager):
        transcript_manager.add_entry("new", "user", "Auto")
        assert "new" in transcript_manager.transcripts
        assert len(transcript_manager.get_transcript("new")) == 1

    def test_get_transcript_unknown_session(self, transcript_manager):
        assert transcript_manager.get_transcript("nope") == []

    def test_get_session_metadata(self, transcript_manager):
        transcript_manager.create_session("s1", {"foo": "bar"})
        assert transcript_manager.get_session_metadata("s1") == {"foo": "bar"}

    def test_get_session_metadata_unknown(self, transcript_manager):
        assert transcript_manager.get_session_metadata("nope") == {}

    def test_update_session_metadata(self, transcript_manager):
        transcript_manager.create_session("s1", {"a": 1})
        transcript_manager.update_session_metadata("s1", {"b": 2})
        meta = transcript_manager.get_session_metadata("s1")
        assert meta == {"a": 1, "b": 2}

    def test_update_session_metadata_creates_if_missing(self, transcript_manager):
        transcript_manager.update_session_metadata("s1", {"x": 10})
        assert transcript_manager.session_metadata["s1"]["x"] == 10


# ── Formatting ───────────────────────────────────────────────────────────────

class TestFormatting:
    def test_format_as_text_with_entries(self, transcript_manager):
        transcript_manager.create_session("s1")
        transcript_manager.add_entry("s1", "user", "Hello")
        transcript_manager.add_entry("s1", "assistant", "Hi there")
        text = transcript_manager.format_as_text("s1")
        assert "user: Hello" in text
        assert "assistant: Hi there" in text

    def test_format_as_text_empty(self, transcript_manager):
        transcript_manager.create_session("s1")
        assert transcript_manager.format_as_text("s1") == "No transcript available."

    def test_format_as_html_basic_structure(self, transcript_manager):
        transcript_manager.create_session("s1")
        transcript_manager.add_entry("s1", "user", "Hello")
        html = transcript_manager.format_as_html("s1")
        assert "<!DOCTYPE html>" in html
        assert "Call Transcript" in html
        assert "Hello" in html

    def test_format_as_html_empty(self, transcript_manager):
        transcript_manager.create_session("s1")
        html = transcript_manager.format_as_html("s1")
        assert html == "<p>No transcript available.</p>"

    def test_format_as_html_with_summary(self, transcript_manager):
        transcript_manager.create_session("s1")
        transcript_manager.add_entry("s1", "user", "Hello")
        summary = {
            "summary": "A brief call.",
            "lead_info_table": "| Name | Email |\n|---|---|\n| John | john@test.com |",
            "consultation_info_table": "No consultation scheduled during this call.",
        }
        html = transcript_manager.format_as_html("s1", summary_data=summary)
        assert "AI-Generated Call Summary" in html
        assert "A brief call." in html
        assert "Lead Qualification" in html
        # consultation_info has "No consultation scheduled" — rendered as italic
        assert "No consultation scheduled" in html

    def test_format_as_html_with_metadata(self, transcript_manager):
        transcript_manager.create_session("s1", {
            "target_number": "+1234",
            "duration_seconds": 150,
        })
        transcript_manager.add_entry("s1", "user", "Hi")
        html = transcript_manager.format_as_html("s1")
        assert "+1234" in html
        assert "2m 30s" in html


class TestRenderMarkdownTableOrText:
    def test_markdown_table(self, transcript_manager):
        parts = []
        content = "| Name | Value |\n|---|---|\n| A | 1 |"
        transcript_manager._render_markdown_table_or_text(parts, content)
        html = "\n".join(parts)
        assert "<table" in html
        assert "<th" in html
        assert "<td" in html

    def test_plain_text(self, transcript_manager):
        parts = []
        transcript_manager._render_markdown_table_or_text(parts, "Just plain text")
        html = "\n".join(parts)
        assert "<p" in html
        assert "Just plain text" in html


# ── File I/O ─────────────────────────────────────────────────────────────────

class TestFileIO:
    def test_save_transcript(self, transcript_manager, tmp_path):
        transcript_manager.create_session("s1")
        transcript_manager.add_entry("s1", "user", "Hello")
        filepath = transcript_manager.save_transcript("s1")
        assert filepath.exists()
        data = json.loads(filepath.read_text())
        assert data["session_id"] == "s1"
        assert len(data["entries"]) == 1

    def test_save_transcript_custom_filename(self, transcript_manager, tmp_path):
        transcript_manager.create_session("s1")
        transcript_manager.add_entry("s1", "user", "Hi")
        filepath = transcript_manager.save_transcript("s1", filename="custom.json")
        assert filepath.name == "custom.json"
        assert filepath.exists()

    def test_close_session_saves(self, transcript_manager, tmp_path):
        transcript_manager.create_session("s1")
        transcript_manager.add_entry("s1", "user", "Hello")
        transcript_manager.close_session("s1")
        # close_session saves if entries > 0 — check log_dir
        saved_files = list(tmp_path.glob("transcript_s1_*.json"))
        assert len(saved_files) == 1

    def test_close_session_empty_no_save(self, transcript_manager, tmp_path):
        transcript_manager.create_session("s1")
        transcript_manager.close_session("s1")
        saved_files = list(tmp_path.glob("*.json"))
        assert len(saved_files) == 0
