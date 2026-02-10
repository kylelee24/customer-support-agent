import logging
from backend.tools.tools import Tool, ToolResult, ToolResultDirection

logger = logging.getLogger("voicerag")

_end_call_tool_schema = {
    "type": "function",
    "name": "end_call",
    "description": (
        "End the current phone call or voice session. Use this after you have "
        "delivered your closing message and said goodbye to the caller. This "
        "will disconnect the call."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
}


def end_call_tool(rtmt, caller) -> Tool:
    """Factory: create the end_call Tool that hangs up the active call."""

    async def _end_call(args) -> ToolResult:
        ctx = rtmt._active_tool_context
        if not ctx:
            logger.warning("end_call invoked without active tool context")
            return ToolResult("Could not end call — no active context.", ToolResultDirection.TO_SERVER)

        client_ws = ctx["client_ws"]
        is_acs = ctx["is_acs"]

        if is_acs and caller:
            call_connection_id = rtmt.get_session_id(client_ws)
            if call_connection_id:
                try:
                    logger.info(f"📞 end_call: hanging up ACS call {call_connection_id}")
                    caller.call_automation_client.get_call_connection(call_connection_id).hang_up(is_for_everyone=True)
                    return ToolResult("Call ended successfully.", ToolResultDirection.TO_SERVER)
                except Exception as e:
                    logger.error(f"📞 end_call: hang_up failed: {e}")
                    return ToolResult(f"Failed to end call: {e}", ToolResultDirection.TO_SERVER)
            else:
                logger.warning("end_call: no call_connection_id found for websocket")
                return ToolResult("Could not end call — no call connection ID.", ToolResultDirection.TO_SERVER)
        else:
            # Web session — close the WebSocket
            try:
                logger.info("📞 end_call: closing web WebSocket session")
                await client_ws.close()
                return ToolResult("Session ended successfully.", ToolResultDirection.TO_SERVER)
            except Exception as e:
                logger.error(f"📞 end_call: WebSocket close failed: {e}")
                return ToolResult(f"Failed to end session: {e}", ToolResultDirection.TO_SERVER)

    return Tool(schema=_end_call_tool_schema, target=_end_call)
