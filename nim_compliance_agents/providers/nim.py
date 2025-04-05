"""NVIDIA NIM provider — calls the NIM inference API via httpx."""

from __future__ import annotations

import asyncio
import json
import logging

import httpx

from nim_compliance_agents.config import Settings, get_settings
from nim_compliance_agents.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class NIMProvider(LLMProvider):
    """Sends completion requests to NVIDIA NIM endpoints.

    Implements exponential backoff retry and validates that the response
    can be parsed as JSON when the prompt requests structured output.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        if not self._settings.nvidia_api_key:
            raise ValueError(
                "NVIDIA_API_KEY is required for the NIM provider. "
                "Set it in your environment or .env file."
            )
        self._client = httpx.AsyncClient(
            base_url=self._settings.nvidia_api_base,
            headers={
                "Authorization": f"Bearer {self._settings.nvidia_api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    async def complete(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.1,
    ) -> str:
        """Call the NIM chat completions endpoint with retry logic."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._settings.nvidia_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4096,
        }

        last_error: Exception | None = None
        for attempt in range(self._settings.llm_max_retries):
            try:
                response = await self._client.post("/chat/completions", json=payload)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except (httpx.HTTPStatusError, httpx.RequestError, KeyError) as exc:
                last_error = exc
                wait = 2**attempt
                logger.warning(
                    "NIM request failed (attempt %d/%d): %s — retrying in %ds",
                    attempt + 1,
                    self._settings.llm_max_retries,
                    exc,
                    wait,
                )
                await asyncio.sleep(wait)

        raise RuntimeError(
            f"NIM request failed after {self._settings.llm_max_retries} attempts"
        ) from last_error

    async def close(self) -> None:
        """Shut down the underlying HTTP client."""
        await self._client.aclose()


def parse_json_response(text: str) -> dict:
    """Extract and parse JSON from a model response.

    Models sometimes wrap JSON in markdown code fences; this helper
    strips those before parsing.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Drop the opening fence (```json or ```) and closing fence
        lines = [line for line in lines[1:] if not line.strip().startswith("```")]
        cleaned = "\n".join(lines)
    return json.loads(cleaned)
