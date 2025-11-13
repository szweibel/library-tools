"""Shared test fixtures and configuration."""

import pytest
from unittest.mock import Mock, AsyncMock
import os


@pytest.fixture
def mock_settings():
    """Mock settings with test values."""
    from library_tools.common.config import Settings

    return Settings(
        # Primo
        primo_api_key="test_primo_key",
        primo_vid="01TEST:TEST_VIEW",
        primo_scope="Everything",
        primo_base_url="https://api.test.com/primo/v1/search",
        # OpenAlex
        openalex_email="test@example.com",
        # LibGuides
        libguides_site_id="12345",
        libguides_client_id="test_client_id",
        libguides_client_secret="test_client_secret",
        libguides_base_url="https://lgapi-us.libapps.com/1.2",
        # Repository
        repository_base_url="https://content-out.bepress.com/v2/test.edu",
        repository_api_key="test_repo_key",
    )


@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx response."""
    def _create_response(json_data, status_code=200):
        mock_response = Mock()
        mock_response.json.return_value = json_data
        mock_response.status_code = status_code
        mock_response.raise_for_status = Mock()
        return mock_response

    return _create_response


@pytest.fixture
def mock_async_client(mock_httpx_response):
    """Create a mock async httpx client."""
    def _create_client(response_data, status_code=200):
        mock_client = Mock()
        mock_response = mock_httpx_response(response_data, status_code)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        return mock_client

    return _create_client


@pytest.fixture(autouse=True)
def clear_env_vars():
    """Clear environment variables before each test."""
    env_vars = [
        "PRIMO_API_KEY", "PRIMO_VID", "PRIMO_SCOPE", "PRIMO_BASE_URL",
        "OPENALEX_EMAIL",
        "LIBGUIDES_SITE_ID", "LIBGUIDES_CLIENT_ID", "LIBGUIDES_CLIENT_SECRET", "LIBGUIDES_BASE_URL",
        "REPOSITORY_BASE_URL", "REPOSITORY_API_KEY",
    ]

    # Save original values
    original = {k: os.environ.get(k) for k in env_vars}

    # Clear for test
    for key in env_vars:
        os.environ.pop(key, None)

    yield

    # Restore original values
    for key, value in original.items():
        if value is not None:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)

    # Clear settings cache
    from library_tools.common.config import get_settings
    get_settings.cache_clear()
