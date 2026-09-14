from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from groq import Groq

from app.core.settings import settings


def extract_json(text: str) -> dict[str, Any]:
    payload = text.strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", payload, re.IGNORECASE)
    if fenced:
        payload = fenced.group(1)
    start = payload.find("{")
    end = payload.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model did not return JSON")
    return json.loads(payload[start : end + 1])


class GroqLlmProvider:
    name = "groq"

    def __init__(self) -> None:
        self._client: Groq | None = None

    def is_ready(self) -> bool:
        return bool(settings.groq_api_key)

    def _client_or_raise(self) -> Groq:
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")
        if self._client is None:
            self._client = Groq(
                api_key=settings.groq_api_key,
                base_url=settings.groq_client_base_url,
                timeout=settings.groq_timeout_seconds,
            )
        return self._client

    def _complete_json_sync(self, system: str, user: str) -> dict[str, Any]:
        client = self._client_or_raise()
        completion = client.chat.completions.create(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        content = completion.choices[0].message.content or ""
        return extract_json(content)

    async def complete_json(self, system: str, user: str) -> dict[str, Any]:
        return await asyncio.to_thread(self._complete_json_sync, system, user)
