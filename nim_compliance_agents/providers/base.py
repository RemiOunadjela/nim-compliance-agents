"""Abstract base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Interface that all LLM backends must implement.

    The provider pattern decouples agent logic from the inference backend,
    making it straightforward to swap between NVIDIA NIM, local models, or
    mock implementations for testing.
    """

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.1,
    ) -> str:
        """Send a completion request and return the response text."""
        ...
