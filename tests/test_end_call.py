"""Tests for backend.tools.end_call — all code paths."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.tools.tools import ToolResultDirection
from backend.tools.end_call import end_call_tool


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_rtmt():
    """Minimal mock RTMiddleTier with the attributes end_call needs."""
    rtmt = MagicMock()
    rtmt._active_tool_context = None
    return rtmt


def _make_caller():
    """Mock AcsCaller with call_automation_client."""
    caller = MagicMock()
    return caller


# ── Tests ────────────────────────────────────────────────────────────────────

class TestEndCall:
    @pytest.mark.asyncio
    async def test_no_active_context(self):
        rtmt = _make_rtmt()
        rtmt._active_tool_context = None
        tool = end_call_tool(rtmt, _make_caller())
        result = await tool.target({})
        assert "no active context" in result.text.lower()
        assert result.destination == ToolResultDirection.TO_SERVER

    @pytest.mark.asyncio
    async def test_acs_call_success(self):
        rtmt = _make_rtmt()
        caller = _make_caller()
        mock_ws = MagicMock()
        rtmt._active_tool_context = {"client_ws": mock_ws, "is_acs": True}
        rtmt.get_session_id.return_value = "conn-123"

        tool = end_call_tool(rtmt, caller)
        result = await tool.target({})

        caller.call_automation_client.get_call_connection.assert_called_once_with("conn-123")
        caller.call_automation_client.get_call_connection("conn-123").hang_up.assert_called_with(is_for_everyone=True)
        assert "ended successfully" in result.text.lower()

    @pytest.mark.asyncio
    async def test_acs_call_no_connection_id(self):
        rtmt = _make_rtmt()
        caller = _make_caller()
        mock_ws = MagicMock()
        rtmt._active_tool_context = {"client_ws": mock_ws, "is_acs": True}
        rtmt.get_session_id.return_value = None

        tool = end_call_tool(rtmt, caller)
        result = await tool.target({})
        assert "no call connection" in result.text.lower()

    @pytest.mark.asyncio
    async def test_acs_call_hang_up_raises(self):
        rtmt = _make_rtmt()
        caller = _make_caller()
        mock_ws = MagicMock()
        rtmt._active_tool_context = {"client_ws": mock_ws, "is_acs": True}
        rtmt.get_session_id.return_value = "conn-123"
        caller.call_automation_client.get_call_connection.return_value.hang_up.side_effect = RuntimeError("ACS error")

        tool = end_call_tool(rtmt, caller)
        result = await tool.target({})
        assert "failed to end call" in result.text.lower()

    @pytest.mark.asyncio
    async def test_web_session_close(self):
        rtmt = _make_rtmt()
        mock_ws = AsyncMock()
        rtmt._active_tool_context = {"client_ws": mock_ws, "is_acs": False}

        tool = end_call_tool(rtmt, None)
        result = await tool.target({})

        mock_ws.close.assert_awaited_once()
        assert "session ended successfully" in result.text.lower()

    @pytest.mark.asyncio
    async def test_web_session_close_raises(self):
        rtmt = _make_rtmt()
        mock_ws = AsyncMock()
        mock_ws.close.side_effect = RuntimeError("WS error")
        rtmt._active_tool_context = {"client_ws": mock_ws, "is_acs": False}

        tool = end_call_tool(rtmt, None)
        result = await tool.target({})
        assert "failed to end session" in result.text.lower()
