from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from app.core.settings import settings
from app.prompts.teacher import (
    build_beat_notes_prompt,
    build_beat_user_prompt,
    build_notes_prompt,
    build_notes_user_prompt,
)
from app.providers.llm.local_llm import LocalLlmProvider
from app.providers.registry import resolve_llm
from app.schemas.lesson import BoardBeat, BoardElement, Lesson, LessonSegment
from app.services.board_notes import (
    board_is_dense,
    dense_sheet,
    diagram_for_line,
    is_weak_label,
    labels_from_line,
    topic_from_lines,
)
from app.services.slides import slide_from_item

logger = logging.getLogger("tutor.lesson")

ALLOWED_TYPES = {"rectangle", "ellipse", "diamond", "arrow", "line", "text"}
LLM_BEAT_CONCURRENCY = 4


def _sentences(block: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", block) if part.strip()]
    return parts or [block]


def _wrap_words(text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = word if len(word) <= limit else word[:limit]
    if current:
        chunks.append(current)
    return chunks


def split_script(script: str) -> list[str]:
    raw = str(script or "").strip()
    if len(raw) > settings.max_query_chars:
        raw = raw[: settings.max_query_chars].rsplit(" ", 1)[0] or raw[: settings.max_query_chars]
    units: list[str] = []
    for block in [line.strip() for line in raw.splitlines() if line.strip()]:
        for sentence in _sentences(block):
            units.extend(_wrap_words(sentence, settings.max_speech_chars))
    return [unit for unit in units if unit][: settings.max_script_lines]


def _clip(value: Any, max_len: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def _normalize_element(raw: dict[str, Any], index: int, segment_id: str) -> BoardElement | None:
    element_type = str(raw.get("type") or "").lower()
    if element_type not in ALLOWED_TYPES:
        return None

    payload: dict[str, Any] = {
        "id": str(raw.get("id") or f"{segment_id}_el_{index}"),
        "type": element_type,
        "x": float(raw.get("x") or 80),
        "y": float(raw.get("y") or 80),
    }
    if raw.get("width") is not None:
        payload["width"] = float(raw.get("width") or 200)
    if raw.get("height") is not None:
        payload["height"] = float(raw.get("height") or 80)
    if raw.get("fontSize") is not None:
        payload["fontSize"] = float(raw.get("fontSize") or 20)
    for key in ("strokeColor", "backgroundColor", "fillStyle", "startId", "endId"):
        if raw.get(key):
            payload[key] = str(raw[key])
    if isinstance(raw.get("points"), list):
        payload["points"] = raw["points"]

    if element_type == "text":
        label = raw.get("label")
        label_text = label.get("text") if isinstance(label, dict) else label
        payload["text"] = _clip(raw.get("text") or raw.get("labelText") or label_text or "", 80)
        payload["fontSize"] = payload.get("fontSize") or 32
        payload["strokeColor"] = payload.get("strokeColor") or settings.board_title_color
        if is_weak_label(str(payload["text"])):
            return None
    elif element_type in {"rectangle", "ellipse", "diamond"}:
        label = raw.get("label")
        label_text = (
            label.get("text")
            if isinstance(label, dict)
            else raw.get("labelText") or raw.get("text") or label
        )
        if label_text:
            clipped = _clip(label_text, 40)
            if is_weak_label(clipped):
                return None
            payload["label"] = {"text": clipped}
        payload["width"] = payload.get("width") or 240
        payload["height"] = payload.get("height") or 80
        payload["backgroundColor"] = payload.get("backgroundColor") or settings.board_box_bg
        payload["strokeColor"] = payload.get("strokeColor") or settings.board_box_stroke
    else:
        label = raw.get("label")
        label_text = label.get("text") if isinstance(label, dict) else raw.get("labelText")
        if label_text:
            payload["label"] = {"text": _clip(label_text, 24)}
        payload["strokeColor"] = payload.get("strokeColor") or settings.board_box_stroke

    return BoardElement.model_validate(payload)


def _labels_of(elements: list[BoardElement]) -> list[str]:
    labels: list[str] = []
    for el in elements:
        if el.type == "text" and el.text:
            labels.append(el.text)
        elif isinstance(el.label, dict) and el.label.get("text"):
            labels.append(str(el.label["text"]))
        elif isinstance(el.label, str) and el.label.strip():
            labels.append(el.label)
    return [label for label in labels if not is_weak_label(label)]


def _from_raw_elements(raw_elements: list[Any], segment_id: str) -> list[BoardElement]:
    return [
        el
        for el in (
            _normalize_element(raw, el_index, segment_id)
            for el_index, raw in enumerate(raw_elements[: settings.max_board_elements_per_segment])
            if isinstance(raw, dict)
        )
        if el is not None
    ]


def _fallback_board(line: str, index: int, topic: str, extra: list[str] | None = None) -> list[BoardElement]:
    title, labels = labels_from_line(line, topic)
    raw_elements = dense_sheet(topic or title, [*(extra or []), *labels], index, title)
    elements = _from_raw_elements(raw_elements, f"s{index + 1}")
    if elements:
        return elements
    _, raw_elements = diagram_for_line(line, index, topic or title)
    return _from_raw_elements(raw_elements, f"s{index + 1}")


def _coerce_beat(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    if raw.get("bullets") or raw.get("headline") or raw.get("beatTitle") or isinstance(raw.get("elements"), list):
        return raw
    segments = raw.get("segments")
    if isinstance(segments, list):
        for item in segments:
            if not isinstance(item, dict):
                continue
            slide = item.get("slide") if isinstance(item.get("slide"), dict) else {}
            board = item.get("board") if isinstance(item.get("board"), dict) else item
            elements = board.get("elements") if isinstance(board, dict) else None
            return {
                "title": raw.get("title") or item.get("title"),
                "topic": raw.get("topic"),
                "beatTitle": slide.get("headline") or item.get("title"),
                "headline": slide.get("headline"),
                "kicker": slide.get("kicker") or item.get("kicker"),
                "bullets": slide.get("bullets") or item.get("bullets"),
                "layout": slide.get("layout") or item.get("layout"),
                "elements": elements if isinstance(elements, list) else [],
            }
    return raw


def _beat_item(beat: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "title": beat.get("beatTitle") or beat.get("headline") or beat.get("title") or f"Line {index + 1}",
        "kicker": beat.get("kicker"),
        "bullets": beat.get("bullets"),
        "layout": beat.get("layout"),
        "slide": {
            "headline": beat.get("headline") or beat.get("beatTitle") or beat.get("title"),
            "kicker": beat.get("kicker"),
            "bullets": beat.get("bullets") or [],
            "layout": beat.get("layout") or "cards",
        },
        "board": {"mode": "replace", "elements": beat.get("elements") or []},
    }


async def plan_beats_with_llm(provider: Any, lines: list[str], script: str) -> dict[str, Any]:
    """One LLM call per spoken line so notes match that line and fill the board."""
    sem = asyncio.Semaphore(LLM_BEAT_CONCURRENCY)
    system = build_beat_notes_prompt()

    async def one(index: int) -> dict[str, Any]:
        async with sem:
            return await provider.complete_json(
                system,
                build_beat_user_prompt(lines, script, index),
            )

    results = await asyncio.gather(*[one(index) for index in range(len(lines))], return_exceptions=True)
    failures = [item for item in results if isinstance(item, Exception)]
    if len(failures) == len(results):
        raise failures[0]

    title = topic_from_lines(lines)
    segments: list[dict[str, Any]] = []
    for index, result in enumerate(results):
        if isinstance(result, Exception):
            segments.append({"id": f"s{index + 1}", "title": f"Line {index + 1}", "board": {"elements": []}})
            continue
        beat = _coerce_beat(result)
        if index == 0:
            title = str(beat.get("title") or beat.get("topic") or title)
        item = _beat_item(beat, index)
        item["id"] = f"s{index + 1}"
        segments.append(item)
    return {"title": title, "topic": title, "segments": segments}


def _segment_for_line(
    line: str,
    index: int,
    topic: str,
    item: dict[str, Any] | None = None,
    total: int = 0,
) -> LessonSegment:
    item = item if isinstance(item, dict) else {}
    segment_id = f"s{index + 1}"
    board = item.get("board") if isinstance(item.get("board"), dict) else {}
    raw_elements = board.get("elements") if isinstance(board.get("elements"), list) else []
    elements = _from_raw_elements(raw_elements, segment_id)
    if not board_is_dense(elements):
        elements = _fallback_board(line, index, topic, _labels_of(elements))
    slide = slide_from_item(item, line, index, topic, total or (index + 1))
    title = _clip(item.get("title") or slide.headline or f"Line {index + 1}", 80)
    if re.match(r"^line\s+\d+$", title, re.I):
        title = slide.headline
    return LessonSegment(
        id=segment_id,
        title=title,
        speech=line,
        board=BoardBeat(mode="replace", elements=elements),
        slide=slide,
    )


def normalize_lesson(raw: dict[str, Any], lines: list[str]) -> Lesson:
    raw_segments = raw.get("segments") if isinstance(raw, dict) else None
    if not isinstance(raw_segments, list):
        raw_segments = []

    topic = _clip((raw or {}).get("title") or (raw or {}).get("topic") or topic_from_lines(lines), 80)
    total = len(lines)
    segments = [
        _segment_for_line(
            line,
            index,
            topic,
            raw_segments[index] if index < len(raw_segments) and isinstance(raw_segments[index], dict) else {},
            total,
        )
        for index, line in enumerate(lines)
    ]

    if not segments:
        raise ValueError("Script is empty")

    return Lesson(
        title=topic,
        topic=topic,
        level="script",
        language=_clip((raw or {}).get("language") or "en", 8),
        segments=segments,
    )


def placeholder_lesson(lines: list[str]) -> Lesson:
    return normalize_lesson({"title": topic_from_lines(lines), "topic": topic_from_lines(lines)}, lines)


async def iter_lesson_events(script: str):
    """Yield NDJSON events: meta (instant placeholders), then richer segments as the LLM finishes."""
    lines = split_script(script)
    if not lines:
        raise ValueError("script must contain at least one line")

    provider = resolve_llm()
    draft = placeholder_lesson(lines)
    yield {
        "event": "meta",
        "provider": provider.name,
        "lesson": draft.model_dump(mode="json"),
    }

    try:
        if provider.name == "local":
            raw = await provider.complete_json(
                build_notes_prompt(),
                build_notes_user_prompt(lines, script),
            )
            rich = normalize_lesson(raw, lines)
            yield {"event": "lesson", "lesson": rich.model_dump(mode="json"), "provider": provider.name}
        else:
            sem = asyncio.Semaphore(LLM_BEAT_CONCURRENCY)
            system = build_beat_notes_prompt()
            topic = draft.title

            async def enrich(index: int) -> tuple[int, LessonSegment]:
                async with sem:
                    try:
                        raw = await provider.complete_json(
                            system,
                            build_beat_user_prompt(lines, script, index),
                        )
                        beat = _coerce_beat(raw)
                        if index == 0:
                            topic_title = str(beat.get("title") or beat.get("topic") or topic)
                        else:
                            topic_title = topic
                        item = _beat_item(beat, index)
                        return index, _segment_for_line(lines[index], index, topic_title, item, len(lines))
                    except Exception:
                        logger.exception("Beat %s notes failed; keeping draft", index + 1)
                        return index, draft.segments[index]

            for task in asyncio.as_completed([asyncio.create_task(enrich(index)) for index in range(len(lines))]):
                index, segment = await task
                yield {
                    "event": "segment",
                    "index": index,
                    "segment": segment.model_dump(mode="json"),
                }
    except Exception:
        logger.exception("Streaming notes failed; presenter already has draft slides")

    yield {"event": "done"}


async def plan_lesson(script: str) -> tuple[Lesson, str]:
    lines = split_script(script)
    if not lines:
        raise ValueError("script must contain 1 to {0} non-empty lines".format(settings.max_script_lines))
    provider = resolve_llm()
    try:
        if provider.name == "local":
            raw = await provider.complete_json(
                build_notes_prompt(),
                build_notes_user_prompt(lines, script),
            )
        else:
            raw = await plan_beats_with_llm(provider, lines, script)
        return normalize_lesson(raw, lines), provider.name
    except Exception:
        if provider.name == "local":
            raise
        logger.exception("Primary LLM (%s) failed; using local notes", provider.name)
        fallback = LocalLlmProvider()
        raw = await fallback.complete_json(
            build_notes_prompt(),
            build_notes_user_prompt(lines, script),
        )
        return normalize_lesson(raw, lines), fallback.name
