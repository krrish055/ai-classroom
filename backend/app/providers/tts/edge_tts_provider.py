from __future__ import annotations

from typing import Any

import edge_tts

from app.core.settings import settings


class EdgeTtsProvider:
    name = "edge"

    def is_ready(self) -> bool:
        return True

    async def synthesize(self, text: str) -> dict[str, Any]:
        communicate = edge_tts.Communicate(
            text=text,
            voice=settings.tts_voice,
            rate=settings.tts_rate,
        )
        chunks: list[bytes] = []
        async for message in communicate.stream():
            if message["type"] == "audio":
                chunks.append(message["data"])
        audio = b"".join(chunks)
        if not audio:
            raise RuntimeError("Edge TTS returned empty audio")
        return {
            "provider": self.name,
            "mime_type": "audio/mpeg",
            "audio": audio,
        }


class BrowserTtsProvider:
    name = "browser"

    def is_ready(self) -> bool:
        return True

    async def synthesize(self, text: str) -> dict[str, Any]:
        return {
            "provider": self.name,
            "mime_type": "application/json",
            "text": text,
            "speechRate": settings.tts_speech_rate,
        }
