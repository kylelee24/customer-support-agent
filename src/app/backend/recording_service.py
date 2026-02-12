import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger("voicerag")


class RecordingService:
    """Manages call recording storage and SAS URL generation using Azure Blob Storage."""

    def __init__(self, storage_connection_string: str):
        self._connection_string = storage_connection_string
        self._blob_service_client = None
        self._account_name = None
        self._account_key = None
        self._container_name = "recordings"

        if not storage_connection_string:
            return

        try:
            from azure.storage.blob import BlobServiceClient

            self._blob_service_client = BlobServiceClient.from_connection_string(
                storage_connection_string
            )
            # Parse account name and key from connection string for SAS generation
            parts = dict(
                part.split("=", 1)
                for part in storage_connection_string.split(";")
                if "=" in part
            )
            self._account_name = parts.get("AccountName")
            self._account_key = parts.get("AccountKey")
        except Exception as e:
            logger.error(f"Failed to initialize RecordingService: {e}")
            self._blob_service_client = None

    def is_configured(self) -> bool:
        return self._blob_service_client is not None and self._account_key is not None

    def ensure_container_exists(self):
        """Create the recordings container if it doesn't exist."""
        if not self.is_configured():
            return
        try:
            container_client = self._blob_service_client.get_container_client(
                self._container_name
            )
            if not container_client.exists():
                self._blob_service_client.create_container(self._container_name)
                logger.info(f"Created blob container: {self._container_name}")
            else:
                logger.info(f"Blob container already exists: {self._container_name}")
        except Exception as e:
            logger.error(f"Failed to ensure container exists: {e}")

    def get_container_url(self) -> str:
        """Return the full URL of the recordings container for BYOS."""
        return f"https://{self._account_name}.blob.core.windows.net/{self._container_name}"

    def find_recording_blob(self, recording_id: str) -> str | None:
        """List blobs with the recording_id prefix and return the first .wav name."""
        if not self.is_configured():
            return None
        try:
            container_client = self._blob_service_client.get_container_client(
                self._container_name
            )
            blobs = container_client.list_blobs(name_starts_with=recording_id)
            for blob in blobs:
                if blob.name.endswith(".wav"):
                    return blob.name
        except Exception as e:
            logger.error(f"Failed to find recording blob: {e}")
        return None

    def generate_sas_url(self, blob_name: str, expiry_days: int = 90) -> str | None:
        """Generate a read-only SAS URL for a recording blob."""
        if not self.is_configured():
            return None
        try:
            from azure.storage.blob import BlobSasPermissions, generate_blob_sas

            sas_token = generate_blob_sas(
                account_name=self._account_name,
                container_name=self._container_name,
                blob_name=blob_name,
                account_key=self._account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.now(timezone.utc) + timedelta(days=expiry_days),
            )
            return f"https://{self._account_name}.blob.core.windows.net/{self._container_name}/{blob_name}?{sas_token}"
        except Exception as e:
            logger.error(f"Failed to generate SAS URL: {e}")
            return None
