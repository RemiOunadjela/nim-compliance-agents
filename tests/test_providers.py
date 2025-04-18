"""Tests for LLM providers."""

from __future__ import annotations

import json

import pytest

from nim_compliance_agents.providers.mock import MockProvider
from nim_compliance_agents.providers.nim import parse_json_response


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
