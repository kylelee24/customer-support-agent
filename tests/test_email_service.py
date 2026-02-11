"""Tests for backend.email_service — configuration checks, message building."""

from unittest.mock import MagicMock, patch

import pytest

from backend.email_service import EmailService


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_service(configured: bool = True) -> EmailService:
    """Create an EmailService with a mocked client."""
    with patch("backend.email_service.EmailClient") as mock_cls:
        if configured:
            svc = EmailService(
                connection_string="Endpoint=sb://fake;SharedAccessKey=fake",
                sender_address="noreply@test.com",
                default_recipients=["admin@test.com"],
            )
        else:
            svc = EmailService(
                connection_string="",
                sender_address="",
            )
    return svc


# ── is_configured ────────────────────────────────────────────────────────────

class TestIsConfigured:
    def test_true_when_client_exists(self):
        svc = _make_service(configured=True)
        assert svc.is_configured() is True

    def test_false_when_no_client(self):
        svc = _make_service(configured=False)
        assert svc.is_configured() is False


# ── send_transcript_email ────────────────────────────────────────────────────

class TestSendTranscriptEmail:
    @pytest.mark.asyncio
    async def test_returns_false_not_configured(self):
        svc = _make_service(configured=False)
        result = await svc.send_transcript_email("Subject", "<h1>Hi</h1>")
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_no_recipients(self):
        svc = _make_service(configured=True)
        svc.default_recipients = []
        result = await svc.send_transcript_email("Subject", "<h1>Hi</h1>", recipients=[])
        assert result is False

    @pytest.mark.asyncio
    async def test_builds_correct_message(self):
        svc = _make_service(configured=True)
        mock_poller = MagicMock()
        mock_poller.result.return_value = {"id": "msg-1", "status": "Succeeded"}
        svc.client.begin_send = MagicMock(return_value=mock_poller)

        result = await svc.send_transcript_email(
            subject="Test Subject",
            html_content="<p>Hello</p>",
            recipients=["user@test.com"],
            plain_text_content="Hello",
        )
        assert result is True
        call_args = svc.client.begin_send.call_args[0][0]
        assert call_args["senderAddress"] == "noreply@test.com"
        assert call_args["content"]["subject"] == "Test Subject"
        assert call_args["content"]["html"] == "<p>Hello</p>"
        assert call_args["content"]["plainText"] == "Hello"
        assert call_args["recipients"]["to"][0]["address"] == "user@test.com"

    @pytest.mark.asyncio
    async def test_begin_send_error_returns_false(self):
        svc = _make_service(configured=True)
        svc.client.begin_send = MagicMock(side_effect=RuntimeError("Network error"))
        result = await svc.send_transcript_email("Sub", "<p>Hi</p>", recipients=["a@b.com"])
        assert result is False


# ── send_call_transcript ─────────────────────────────────────────────────────

class TestSendCallTranscript:
    @pytest.mark.asyncio
    async def test_subject_with_duration(self):
        svc = _make_service(configured=True)
        mock_poller = MagicMock()
        mock_poller.result.return_value = {"id": "msg-2", "status": "Succeeded"}
        svc.client.begin_send = MagicMock(return_value=mock_poller)

        result = await svc.send_call_transcript(
            call_id="conn-1",
            phone_number="+1234",
            html_transcript="<p>Transcript</p>",
            duration="2m 30s",
        )
        assert result is True
        msg = svc.client.begin_send.call_args[0][0]
        assert msg["content"]["subject"] == "Call Transcript - +1234 (2m 30s)"

    @pytest.mark.asyncio
    async def test_subject_without_duration(self):
        svc = _make_service(configured=True)
        mock_poller = MagicMock()
        mock_poller.result.return_value = {"id": "msg-3", "status": "Succeeded"}
        svc.client.begin_send = MagicMock(return_value=mock_poller)

        result = await svc.send_call_transcript(
            call_id="conn-2",
            phone_number="+1234",
            html_transcript="<p>Transcript</p>",
        )
        assert result is True
        msg = svc.client.begin_send.call_args[0][0]
        assert msg["content"]["subject"] == "Call Transcript - +1234"
