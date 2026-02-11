import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from aiohttp import web
from azure.core.credentials import AzureKeyCredential

# Add src/app to path so "from backend.xxx import ..." works
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "app"))

from backend.transcript_manager import TranscriptManager
from backend.rtmt import RTMiddleTier


@pytest.fixture
def transcript_manager(tmp_path):
    """TranscriptManager that writes to a temp directory."""
    return TranscriptManager(log_dir=tmp_path)


@pytest.fixture
def rtmt():
    """RTMiddleTier with a fake API key (no real Azure calls)."""
    rt = RTMiddleTier(
        endpoint="https://fake.openai.azure.com",
        deployment="test-deployment",
        credentials=AzureKeyCredential("fake-key"),
    )
    return rt


@pytest.fixture
def mock_ws():
    """Mock aiohttp WebSocketResponse."""
    ws = MagicMock(spec=web.WebSocketResponse)
    return ws
