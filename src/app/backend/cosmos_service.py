import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("voicerag")


class CosmosCallLogger:
    """Service for logging call records to Azure Cosmos DB."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.client = None
        self.container = None
        self._database_name = "call_center"
        self._container_name = "calls"

    async def initialize(self):
        """Create the async Cosmos client, database, and container."""
        if not self.connection_string:
            logger.warning("⚠️ Cosmos DB not configured (no connection string)")
            return

        try:
            from azure.cosmos.aio import CosmosClient

            self.client = CosmosClient.from_connection_string(self.connection_string)
            database = await self.client.create_database_if_not_exists(self._database_name)
            self.container = await database.create_container_if_not_exists(
                id=self._container_name,
                partition_key={"paths": ["/phone_number"], "kind": "Hash"},
            )
            logger.info(
                f"Cosmos DB initialized: {self._database_name}/{self._container_name}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            self.client = None
            self.container = None

    def is_configured(self) -> bool:
        return self.container is not None

    async def create_call_record(
        self,
        call_connection_id: str,
        phone_number: str,
        call_direction: str,
        source_number: str,
    ):
        """Create a new call document when a call starts."""
        if not self.is_configured():
            return
        now = datetime.utcnow().isoformat() + "Z"
        document = {
            "id": call_connection_id,
            "phone_number": phone_number,
            "call_direction": call_direction,
            "source_number": source_number,
            "initiated_at": now,
            "connected_at": None,
            "disconnected_at": None,
            "duration_seconds": None,
            "status": "initiated",
            "transcript": None,
            "ai_summary": None,
            "lead_info": None,
            "consultation_info": None,
            "errors": [],
            "created_at": now,
            "updated_at": now,
        }
        try:
            await self.container.upsert_item(document)
            logger.info(f"Cosmos DB: created call record {call_connection_id}")
        except Exception as e:
            logger.error(f"Cosmos DB: failed to create call record: {e}")

    async def update_call_connected(self, call_connection_id: str, phone_number: str):
        """Mark a call as connected."""
        if not self.is_configured():
            return
        now = datetime.utcnow().isoformat() + "Z"
        try:
            item = await self.container.read_item(
                item=call_connection_id, partition_key=phone_number
            )
            item["connected_at"] = now
            item["status"] = "connected"
            item["updated_at"] = now
            await self.container.upsert_item(item)
            logger.info(f"Cosmos DB: call {call_connection_id} connected")
        except Exception as e:
            logger.error(f"Cosmos DB: failed to update call connected: {e}")

    async def update_call_disconnected(
        self,
        call_connection_id: str,
        phone_number: str,
        duration_seconds: Optional[float] = None,
    ):
        """Mark a call as disconnected."""
        if not self.is_configured():
            return
        now = datetime.utcnow().isoformat() + "Z"
        try:
            item = await self.container.read_item(
                item=call_connection_id, partition_key=phone_number
            )
            item["disconnected_at"] = now
            item["duration_seconds"] = duration_seconds
            item["status"] = "summarizing"
            item["updated_at"] = now
            await self.container.upsert_item(item)
            logger.info(f"Cosmos DB: call {call_connection_id} disconnected")
        except Exception as e:
            logger.error(f"Cosmos DB: failed to update call disconnected: {e}")

    async def update_call_transcript_and_summary(
        self,
        call_connection_id: str,
        phone_number: str,
        transcript: Optional[str] = None,
        ai_summary: Optional[str] = None,
        lead_info: Optional[str] = None,
        consultation_info: Optional[str] = None,
    ):
        """Update a call record with transcript and AI summary after post-processing."""
        if not self.is_configured():
            return
        now = datetime.utcnow().isoformat() + "Z"
        try:
            item = await self.container.read_item(
                item=call_connection_id, partition_key=phone_number
            )
            if transcript is not None:
                item["transcript"] = transcript
            if ai_summary is not None:
                item["ai_summary"] = ai_summary
            if lead_info is not None:
                item["lead_info"] = lead_info
            if consultation_info is not None:
                item["consultation_info"] = consultation_info
            item["status"] = "completed"
            item["updated_at"] = now
            await self.container.upsert_item(item)
            logger.info(
                f"Cosmos DB: call {call_connection_id} transcript and summary saved"
            )
        except Exception as e:
            logger.error(
                f"Cosmos DB: failed to update transcript/summary: {e}"
            )

    async def log_call_error(
        self, call_connection_id: str, phone_number: str, stage: str, message: str
    ):
        """Append an error entry to the call record."""
        if not self.is_configured():
            return
        now = datetime.utcnow().isoformat() + "Z"
        try:
            item = await self.container.read_item(
                item=call_connection_id, partition_key=phone_number
            )
            item.setdefault("errors", []).append(
                {"timestamp": now, "stage": stage, "message": message}
            )
            item["status"] = "error"
            item["updated_at"] = now
            await self.container.upsert_item(item)
            logger.info(f"Cosmos DB: logged error for call {call_connection_id}")
        except Exception as e:
            logger.error(f"Cosmos DB: failed to log call error: {e}")
