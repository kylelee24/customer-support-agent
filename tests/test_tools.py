"""Tests for backend.tools.tools — ToolResult, ToolResultDirection, Tool, RTToolCall."""

import json

from backend.tools.tools import Tool, ToolResult, ToolResultDirection, RTToolCall


class TestToolResultDirection:
    def test_to_server_value(self):
        assert ToolResultDirection.TO_SERVER.value == 1

    def test_to_client_value(self):
        assert ToolResultDirection.TO_CLIENT.value == 2


class TestToolResult:
    def test_to_text_string(self):
        result = ToolResult("hello", ToolResultDirection.TO_SERVER)
        assert result.to_text() == "hello"

    def test_to_text_dict(self):
        data = {"key": "value", "n": 42}
        result = ToolResult(data, ToolResultDirection.TO_SERVER)
        assert result.to_text() == json.dumps(data)

    def test_to_text_none(self):
        result = ToolResult(None, ToolResultDirection.TO_SERVER)
        assert result.to_text() == ""

    def test_to_text_list(self):
        data = [1, 2, 3]
        result = ToolResult(data, ToolResultDirection.TO_CLIENT)
        assert result.to_text() == json.dumps(data)


class TestToolAndRTToolCall:
    def test_tool_stores_target_and_schema(self):
        target = lambda args: None
        schema = {"type": "function", "name": "test"}
        tool = Tool(target=target, schema=schema)
        assert tool.target is target
        assert tool.schema is schema

    def test_rt_tool_call_stores_ids(self):
        tc = RTToolCall("call-123", "prev-456")
        assert tc.tool_call_id == "call-123"
        assert tc.previous_id == "prev-456"
