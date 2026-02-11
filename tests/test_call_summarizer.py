"""Tests for backend.call_summarizer — early returns, response parsing, constructor."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.call_summarizer import CallSummarizer


# ── Constructor ──────────────────────────────────────────────────────────────

class TestConstructor:
    @patch("backend.call_summarizer.AsyncAzureOpenAI")
    def test_api_key_creates_client(self, mock_cls):
        cs = CallSummarizer(endpoint="https://fake.openai.azure.com", api_key="key123")
        mock_cls.assert_called_once()
        assert cs.client is not None

    @patch("backend.call_summarizer.get_bearer_token_provider", return_value=lambda: "tok")
    @patch("backend.call_summarizer.AsyncAzureOpenAI")
    def test_credentials_creates_client(self, mock_cls, mock_provider):
        creds = MagicMock()
        cs = CallSummarizer(endpoint="https://fake.openai.azure.com", credentials=creds)
        mock_cls.assert_called_once()

    def test_no_key_no_credentials_raises(self):
        with pytest.raises(ValueError, match="Either api_key or credentials"):
            CallSummarizer(endpoint="https://fake.openai.azure.com")


# ── Early returns (no mocking required) ─────────────────────────────────────

class TestEarlyReturns:
    @pytest.fixture
    def summarizer(self):
        with patch("backend.call_summarizer.AsyncAzureOpenAI"):
            return CallSummarizer(endpoint="https://fake", api_key="k")

    @pytest.mark.asyncio
    async def test_empty_string(self, summarizer):
        result = await summarizer.summarize_call("")
        assert "No conversation content" in result["summary"]

    @pytest.mark.asyncio
    async def test_whitespace_only(self, summarizer):
        result = await summarizer.summarize_call("   ")
        assert "No conversation content" in result["summary"]

    @pytest.mark.asyncio
    async def test_no_transcript_available(self, summarizer):
        result = await summarizer.summarize_call("No transcript available.")
        assert "No conversation content" in result["summary"]
        assert "No consultation scheduled" in result["consultation_info_table"]

    @pytest.mark.asyncio
    async def test_none_input(self, summarizer):
        result = await summarizer.summarize_call(None)
        assert "No conversation content" in result["summary"]


# ── Response parsing (mocked OpenAI) ────────────────────────────────────────

class TestResponseParsing:
    @pytest.fixture
    def summarizer(self):
        with patch("backend.call_summarizer.AsyncAzureOpenAI"):
            return CallSummarizer(endpoint="https://fake", api_key="k")

    @pytest.mark.asyncio
    async def test_well_structured_response(self, summarizer):
        full_response = (
            "## Call Summary\nThe caller asked about villas.\n\n"
            "## Lead Qualification\n| Name | Budget |\n|---|---|\n| John | 500k |\n\n"
            "## Consultation Details\n| Date | Time |\n|---|---|\n| Jan 5 | 2pm |"
        )
        mock_choice = MagicMock()
        mock_choice.message.content = full_response
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        summarizer.client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await summarizer.summarize_call("User: Hi\nAssistant: Hello")
        assert "villas" in result["summary"]
        assert "John" in result["lead_info_table"]
        assert "Jan 5" in result["consultation_info_table"]
        assert result["full_response"] == full_response

    @pytest.mark.asyncio
    async def test_missing_sections(self, summarizer):
        full_response = "## Call Summary\nBrief call with no details."
        mock_choice = MagicMock()
        mock_choice.message.content = full_response
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        summarizer.client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await summarizer.summarize_call("User: Hello")
        assert "Brief call" in result["summary"]
        assert result["lead_info_table"] == "No lead information extracted."
        assert result["consultation_info_table"] == "No consultation information extracted."

    @pytest.mark.asyncio
    async def test_openai_exception(self, summarizer):
        summarizer.client.chat.completions.create = AsyncMock(side_effect=RuntimeError("API down"))

        result = await summarizer.summarize_call("User: Help")
        assert "Error" in result["summary"]
        assert "error" in result
