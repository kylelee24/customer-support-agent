"""Tests for backend.recording_service — configuration, container URL, SAS, blob lookup."""

from unittest.mock import MagicMock, patch

import pytest

from backend.recording_service import RecordingService


# ── Helpers ──────────────────────────────────────────────────────────────────

FAKE_CONN_STR = (
    "DefaultEndpointsProtocol=https;"
    "AccountName=fakestorage;"
    "AccountKey=ZmFrZWtleQ==;"
    "EndpointSuffix=core.windows.net"
)


def _make_service(connection_string: str = FAKE_CONN_STR) -> RecordingService:
    """Create a RecordingService with a mocked BlobServiceClient."""
    with patch("backend.recording_service.BlobServiceClient", create=True):
        # Patch the import inside __init__
        with patch.dict("sys.modules", {}):
            svc = RecordingService(connection_string)
    return svc


# ── TestIsConfigured ────────────────────────────────────────────────────────


class TestIsConfigured:
    def test_true_when_properly_initialized(self):
        with patch("azure.storage.blob.BlobServiceClient") as mock_cls:
            mock_cls.from_connection_string.return_value = MagicMock()
            svc = RecordingService(FAKE_CONN_STR)
        assert svc.is_configured() is True

    def test_false_when_empty_connection_string(self):
        svc = RecordingService("")
        assert svc.is_configured() is False

    def test_false_when_no_account_key(self):
        conn_str = "DefaultEndpointsProtocol=https;AccountName=fakestorage;EndpointSuffix=core.windows.net"
        with patch("azure.storage.blob.BlobServiceClient") as mock_cls:
            mock_cls.from_connection_string.return_value = MagicMock()
            svc = RecordingService(conn_str)
        assert svc.is_configured() is False


# ── TestGetContainerUrl ─────────────────────────────────────────────────────


class TestGetContainerUrl:
    def test_returns_correct_url(self):
        with patch("azure.storage.blob.BlobServiceClient") as mock_cls:
            mock_cls.from_connection_string.return_value = MagicMock()
            svc = RecordingService(FAKE_CONN_STR)
        assert svc.get_container_url() == "https://fakestorage.blob.core.windows.net/recordings"


# ── TestGenerateSasUrl ──────────────────────────────────────────────────────


class TestGenerateSasUrl:
    def test_returns_url_with_sas_token(self):
        with patch("azure.storage.blob.BlobServiceClient") as mock_cls:
            mock_cls.from_connection_string.return_value = MagicMock()
            svc = RecordingService(FAKE_CONN_STR)

        with patch("backend.recording_service.generate_blob_sas", create=True) as mock_sas:
            # Patch at the point of import inside the method
            with patch.dict("sys.modules", {}):
                pass
            mock_sas.return_value = "sv=2023-01-01&sig=fake"
            # We need to patch where it's imported
            with patch("azure.storage.blob.generate_blob_sas", return_value="sv=2023-01-01&sig=fake"):
                url = svc.generate_sas_url("rec-123/audio.wav")

        assert url is not None
        assert "fakestorage.blob.core.windows.net" in url
        assert "recordings" in url
        assert "rec-123/audio.wav" in url
        assert "sv=2023-01-01&sig=fake" in url

    def test_returns_none_when_not_configured(self):
        svc = RecordingService("")
        assert svc.generate_sas_url("blob.wav") is None


# ── TestFindRecordingBlob ───────────────────────────────────────────────────


class TestFindRecordingBlob:
    def test_returns_wav_blob_name(self):
        with patch("azure.storage.blob.BlobServiceClient") as mock_cls:
            mock_client = MagicMock()
            mock_cls.from_connection_string.return_value = mock_client
            svc = RecordingService(FAKE_CONN_STR)

        mock_container = MagicMock()
        mock_client.get_container_client.return_value = mock_container

        # Simulate blob list with a .wav file
        blob1 = MagicMock()
        blob1.name = "rec-123/metadata.json"
        blob2 = MagicMock()
        blob2.name = "rec-123/audio.wav"
        mock_container.list_blobs.return_value = [blob1, blob2]

        result = svc.find_recording_blob("rec-123")
        assert result == "rec-123/audio.wav"
        mock_container.list_blobs.assert_called_once_with(name_starts_with="rec-123")

    def test_returns_none_when_no_wav(self):
        with patch("azure.storage.blob.BlobServiceClient") as mock_cls:
            mock_client = MagicMock()
            mock_cls.from_connection_string.return_value = mock_client
            svc = RecordingService(FAKE_CONN_STR)

        mock_container = MagicMock()
        mock_client.get_container_client.return_value = mock_container

        blob1 = MagicMock()
        blob1.name = "rec-123/metadata.json"
        mock_container.list_blobs.return_value = [blob1]

        result = svc.find_recording_blob("rec-123")
        assert result is None

    def test_returns_none_when_not_configured(self):
        svc = RecordingService("")
        assert svc.find_recording_blob("rec-123") is None
