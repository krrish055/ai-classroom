from __future__ import annotations

import asyncio
from typing import Any

from groq import Groq

from app.core.settings import settings


class GroqSttProvider:
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

    def _transcribe_sync(
        self, data: bytes, filename: str, mime_type: str
    ) -> dict[str, Any]:
        client = self._client_or_raise()
        result = client.audio.transcriptions.create(
            file=(filename or "speech.webm", data, mime_type or "audio/webm"),
            model=settings.stt_model,
            language=settings.stt_language,
        )
        return {"provider": self.name, "text": (result.text or "").strip()}

    async def transcribe(
        self, data: bytes, filename: str, mime_type: str
    ) -> dict[str, Any]:
        return await asyncio.to_thread(self._transcribe_sync, data, filename, mime_type)


class BrowserSttProvider:
    name = "browser"

    def is_ready(self) -> bool:
        return True

    async def transcribe(
        self, data: bytes, filename: str, mime_type: str
    ) -> dict[str, Any]:
        del data, filename, mime_type
        return {"provider": self.name, "text": "", "client_side": True}
