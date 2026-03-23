from __future__ import annotations

import httpx
import pytest
import respx

SERVER = "https://analytics.example.com"
API_KEY = "proj_testkey123"


@pytest.fixture()
def mock_api():
    """Mock all tgram-analytics API endpoints to return 202."""
    with respx.mock:
        respx.post(f"{SERVER}/api/v1/track").mock(
            return_value=httpx.Response(202, json={"status": "accepted"})
        )
        respx.post(f"{SERVER}/api/v1/pageview").mock(
            return_value=httpx.Response(202, json={"status": "accepted"})
        )
        yield
