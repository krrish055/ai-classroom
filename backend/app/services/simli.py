from __future__ import annotations

import httpx

from app.core.settings import settings

SIMLI_HTTP_TIMEOUT_SECONDS = 30.0


async def create_simli_session() -> dict[str, str]:
    if not settings.avatar_ready:
        raise RuntimeError("Simli avatar is not configured")

    url = f"{settings.simli_base_url.rstrip('/')}/compose/token"
    payload = {
        "faceId": settings.simli_face_id,
        "handleSilence": True,
        "maxSessionLength": settings.simli_max_session_length,
        "maxIdleTime": settings.simli_max_idle_time,
        "audioInputFormat": "pcm16",
    }
    async with httpx.AsyncClient(timeout=SIMLI_HTTP_TIMEOUT_SECONDS) as client:
        response = await client.post(
            url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "x-simli-api-key": settings.simli_api_key,
            },
        )
    if response.status_code >= 400:
        detail = (response.text or response.reason_phrase or "Simli session failed").strip()
        raise RuntimeError(detail[:400])
    data = response.json()
    token = data.get("session_token") if isinstance(data, dict) else None
    if not token:
        raise RuntimeError("Simli did not return a session token")
    return {"session_token": str(token)}
