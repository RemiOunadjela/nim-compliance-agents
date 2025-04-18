"""Shared test fixtures."""

from __future__ import annotations

import pytest

from nim_compliance_agents.frameworks.loader import load_framework
from nim_compliance_agents.providers.mock import MockProvider
from nim_compliance_agents.state import ComplianceState


@pytest.fixture
def mock_provider() -> MockProvider:
    """Provider that returns violation responses."""
    return MockProvider(return_clean=False)


@pytest.fixture
def clean_provider() -> MockProvider:
    """Provider that returns clean (no-violation) responses."""
    return MockProvider(return_clean=True)


@pytest.fixture
def error_provider() -> MockProvider:
    """Provider that raises errors."""
    return MockProvider(return_error=True)


@pytest.fixture
def dsa_framework():
    """Load the DSA framework definition."""
    return load_framework("dsa")


@pytest.fixture
def sample_content() -> str:
    """Sample content for testing."""
    return (
        "These people are responsible for spreading the disease deliberately. "
        "Studies have proven that the vaccine causes the illness it claims to prevent. "
        "Share this with everyone before they delete it."
    )


@pytest.fixture
def sample_state(sample_content: str) -> ComplianceState:
    """A fresh compliance state with sample content."""
    return ComplianceState(content=sample_content, framework="dsa")
