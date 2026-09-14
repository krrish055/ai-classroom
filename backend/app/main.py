from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from time import time

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse

from app.core.settings import settings
from app.providers.registry import resolve_llm, resolve_stt, resolve_tts
from app.schemas.lesson import Lesson, LessonExportRequest, LessonRequest, LessonResponse, SpeechRequest
from app.services.export_deck import build_export
from app.services.lesson import iter_lesson_events, plan_lesson, split_script
from app.services.simli import create_simli_session

logger = logging.getLogger("tutor")

app = FastAPI(title=settings.app_name, version="0.1.2")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

_hits: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_SKIP_PATHS = frozenset({"/health", "/api/config/public"})


def should_skip_rate_limit(method: str, path: str) -> bool:
    if method.upper() == "OPTIONS":
        return True
    return path in RATE_LIMIT_SKIP_PATHS


def client_host(request: Request) -> str:
    return request.client.host if request.client else "local"


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if should_skip_rate_limit(request.method, request.url.path):
        return await call_next(request)
    now = time()
    host = client_host(request)
    bucket = [ts for ts in _hits[host] if now - ts < 60]
    if len(bucket) >= settings.rate_limit_per_minute:
        return JSONResponse({"error": "Too many requests. Please wait a moment."}, status_code=429)
    bucket.append(now)
    _hits[host] = bucket
    return await call_next(request)


@app.exception_handler(HTTPException)
async def http_error(_request: Request, exc: HTTPException):
    return JSONResponse({"error": exc.detail}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_error(_request: Request, exc: RequestValidationError):
    return JSONResponse({"error": "Invalid request", "details": exc.errors()}, status_code=422)


@app.get("/health")
async def health():
    return {
        "ok": True,
        "app": settings.app_name,
        "providers": {
            "llm": resolve_llm().name,
            "tts": resolve_tts().name,
            "stt": resolve_stt().name,
        },
        "avatarEnabled": settings.avatar_ready,
        "avatarModule": settings.avatar_module if settings.avatar_ready else "none",
    }


@app.get("/api/config/public")
async def public_config():
    return {
        "appName": settings.display_name,
        "ttsProvider": resolve_tts().name,
        "ttsFallbackProvider": settings.tts_fallback_provider,
        "sttProvider": resolve_stt().name,
        "sttFallbackProvider": settings.stt_fallback_provider,
        "speechRate": settings.tts_speech_rate,
        "demoScript": settings.demo_script,
        "avatarEnabled": settings.avatar_ready,
        "avatarModule": settings.avatar_module if settings.avatar_ready else "none",
        "maxQueryChars": settings.max_query_chars,
        "maxScriptLines": settings.max_script_lines,
        "sttLanguage": settings.stt_language,
    }


@app.post("/api/lesson", response_model=LessonResponse)
async def create_lesson(body: LessonRequest):
    script = (body.script or body.query or "").strip()
    if not script:
        raise HTTPException(status_code=400, detail="script is required")
    if len(script) > settings.max_query_chars:
        raise HTTPException(status_code=400, detail=f"script exceeds {settings.max_query_chars} characters")
    lines = split_script(script)
    if not lines:
        raise HTTPException(status_code=400, detail="script must contain at least one line")
    if len(lines) > settings.max_script_lines:
        raise HTTPException(status_code=400, detail=f"script exceeds {settings.max_script_lines} lines")
    try:
        lesson, provider = await plan_lesson(script)
    except Exception:
        logger.exception("Lesson planning failed")
        raise HTTPException(status_code=500, detail="Could not prepare this lesson") from None
    return LessonResponse(lesson=lesson, provider=provider, avatarEnabled=settings.avatar_ready)


@app.post("/api/lesson/stream")
async def stream_lesson(body: LessonRequest):
    script = (body.script or body.query or "").strip()
    if not script:
        raise HTTPException(status_code=400, detail="script is required")
    if len(script) > settings.max_query_chars:
        raise HTTPException(status_code=400, detail=f"script exceeds {settings.max_query_chars} characters")
    lines = split_script(script)
    if not lines:
        raise HTTPException(status_code=400, detail="script must contain at least one line")
    if len(lines) > settings.max_script_lines:
        raise HTTPException(status_code=400, detail=f"script exceeds {settings.max_script_lines} lines")

    async def events():
        try:
            async for event in iter_lesson_events(script):
                yield json.dumps(event) + "\n"
        except Exception:
            logger.exception("Lesson stream failed")
            yield json.dumps({"event": "error", "error": "Could not prepare this lesson"}) + "\n"

    return StreamingResponse(events(), media_type="application/x-ndjson")


def _lesson_from_payload(raw: dict) -> Lesson:
    payload = dict(raw or {})
    if not payload.get("topic"):
        payload["topic"] = payload.get("title") or "Training"
    if not payload.get("title"):
        payload["title"] = payload.get("topic") or "Training"
    segments = []
    for index, item in enumerate(payload.get("segments") or []):
        if not isinstance(item, dict):
            continue
        board = item.get("board") if isinstance(item.get("board"), dict) else {}
        elements = []
        for el_index, element in enumerate(board.get("elements") or []):
            if not isinstance(element, dict):
                continue
            row = dict(element)
            row["id"] = str(row.get("id") or f"el_{el_index}")
            row["type"] = str(row.get("type") or "text")
            elements.append(row)
        segments.append(
            {
                "id": str(item.get("id") or f"s{index + 1}"),
                "title": str(item.get("title") or f"Slide {index + 1}"),
                "speech": str(item.get("speech") or ""),
                "board": {"mode": board.get("mode") or "replace", "elements": elements},
                "slide": item.get("slide") if isinstance(item.get("slide"), dict) else {},
            }
        )
    payload["segments"] = segments
    return Lesson.model_validate(payload)


@app.post("/api/export")
@app.post("/api/lesson/export")
async def export_lesson(body: LessonExportRequest):
    fmt = str(body.format or "pptx").lower().strip()
    if fmt in {"ppt", "powerpoint"}:
        fmt = "pptx"
    if fmt in {"doc", "word", "document"}:
        fmt = "docx"
    try:
        lesson = _lesson_from_payload(body.lesson)
        data, mime, filename = await asyncio.to_thread(
            build_export,
            lesson,
            fmt,
            settings.display_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except Exception:
        logger.exception("Lesson export failed")
        raise HTTPException(status_code=500, detail="Could not export this lesson") from None
    return Response(
        content=data,
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/avatar/session")
async def avatar_session():
    if not settings.avatar_ready:
        raise HTTPException(status_code=400, detail="Avatar is not configured")
    try:
        return await create_simli_session()
    except Exception:
        logger.exception("Simli session failed")
        raise HTTPException(status_code=502, detail="Avatar session failed") from None


@app.post("/api/tts")
async def create_speech(body: SpeechRequest):
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    if len(text) > settings.max_speech_chars:
        raise HTTPException(status_code=400, detail=f"text exceeds {settings.max_speech_chars} characters")
    try:
        result = await resolve_tts().synthesize(text)
    except Exception:
        logger.exception("TTS failed; using browser fallback")
        if settings.tts_fallback_provider == "browser":
            return {
                "provider": "browser",
                "fallback": True,
                "text": text,
                "speechRate": settings.tts_speech_rate,
            }
        raise HTTPException(status_code=500, detail="Could not synthesize speech") from None

    audio = result.get("audio")
    if audio:
        return Response(
            content=audio,
            media_type=result.get("mime_type") or "audio/mpeg",
            headers={"X-TTS-Provider": result.get("provider") or "edge"},
        )
    return result


@app.post("/api/stt")
async def transcribe(audio: UploadFile = File(...)):
    data = await audio.read()
    if len(data) > settings.max_stt_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"audio exceeds {settings.max_stt_bytes} bytes",
        )
    try:
        result = await resolve_stt().transcribe(
            data,
            audio.filename or "speech.webm",
            audio.content_type or "audio/webm",
        )
    except Exception:
        logger.exception("STT failed")
        raise HTTPException(status_code=500, detail="Could not transcribe audio") from None
    return result
