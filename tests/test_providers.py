"""Tests for LLM providers."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from nim_compliance_agents.config import Settings
from nim_compliance_agents.providers.mock import MockProvider
from nim_compliance_agents.providers.nim import NIMProvider, parse_json_response


class TestMockProvider:
    @pytest.mark.asyncio
    async def test_returns_violations(self, mock_provider: MockProvider):
        result = await mock_provider.complete("test", system="policy classifier")
        data = json.loads(result)
        assert "violations" in data
        assert len(data["violations"]) > 0

    @pytest.mark.asyncio
    async def test_returns_clean(self, clean_provider: MockProvider):
        result = await clean_provider.complete("test", system="policy classifier")
        data = json.loads(result)
        assert data["violations"] == []

    @pytest.mark.asyncio
    async def test_error_mode(self, error_provider: MockProvider):
        with pytest.raises(RuntimeError, match="Simulated"):
            await error_provider.complete("test")

    @pytest.mark.asyncio
    async def test_detects_risk_agent(self, mock_provider: MockProvider):
        result = await mock_provider.complete("test", system="risk assessment specialist")
        data = json.loads(result)
        assert "severity" in data

    @pytest.mark.asyncio
    async def test_detects_evidence_agent(self, mock_provider: MockProvider):
        result = await mock_provider.complete("test", system="evidence extraction")
        data = json.loads(result)
        assert "evidence" in data

    @pytest.mark.asyncio
    async def test_detects_report_agent(self, mock_provider: MockProvider):
        result = await mock_provider.complete("test", system="report synthesis")
        assert "# Compliance Review Report" in result


class TestNIMProviderInit:
    def test_missing_key_raises_value_error(self):
        settings = Settings(nvidia_api_key="")
        with pytest.raises(ValueError, match="NVIDIA_API_KEY"):
            NIMProvider(settings=settings)

    def test_missing_key_message_includes_export_hint(self):
        settings = Settings(nvidia_api_key="")
        with pytest.raises(ValueError) as exc_info:
            NIMProvider(settings=settings)
        assert "export" in str(exc_info.value).lower()

    def test_missing_key_message_includes_env_file_hint(self):
        settings = Settings(nvidia_api_key="")
        with pytest.raises(ValueError) as exc_info:
            NIMProvider(settings=settings)
        assert ".env" in str(exc_info.value)


class TestNIMProviderComplete:
    def _make_provider(self, mock_client: AsyncMock) -> NIMProvider:
        settings = Settings(nvidia_api_key="nvapi-test-key")
        with patch("nim_compliance_agents.providers.nim.httpx.AsyncClient", return_value=mock_client):
            return NIMProvider(settings=settings)

    def _make_http_error(self, status_code: int) -> httpx.HTTPStatusError:
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = status_code
        return httpx.HTTPStatusError(
            f"{status_code}", request=MagicMock(), response=mock_response
        )

    @pytest.mark.asyncio
    async def test_401_raises_permission_error_immediately(self):
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = self._make_http_error(401)
        mock_client.post.return_value = mock_response

        provider = self._make_provider(mock_client)
        with pytest.raises(PermissionError, match="authentication failed"):
            await provider.complete("test prompt")

    @pytest.mark.asyncio
    async def test_401_does_not_retry(self):
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = self._make_http_error(401)
        mock_client.post.return_value = mock_response

        provider = self._make_provider(mock_client)
        with pytest.raises(PermissionError):
            await provider.complete("test prompt")
        assert mock_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_403_raises_permission_error(self):
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = self._make_http_error(403)
        mock_client.post.return_value = mock_response

        provider = self._make_provider(mock_client)
        with pytest.raises(PermissionError, match="HTTP 403"):
            await provider.complete("test prompt")

    @pytest.mark.asyncio
    async def test_permission_error_message_includes_key_hint(self):
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = self._make_http_error(401)
        mock_client.post.return_value = mock_response

        provider = self._make_provider(mock_client)
        with pytest.raises(PermissionError) as exc_info:
            await provider.complete("test prompt")
        assert "NVIDIA_API_KEY" in str(exc_info.value)


class TestParseJsonResponse:
    def test_plain_json(self):
        assert parse_json_response('{"key": "value"}') == {"key": "value"}

    def test_json_with_code_fence(self):
        text = '```json\n{"key": "value"}\n```'
        assert parse_json_response(text) == {"key": "value"}

    def test_json_with_bare_fence(self):
        text = '```\n{"key": "value"}\n```'
        assert parse_json_response(text) == {"key": "value"}

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            parse_json_response("not json at all")
