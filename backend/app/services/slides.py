from __future__ import annotations

import re
from typing import Any

from app.schemas.lesson import SlideContent
from app.services.board_notes import is_weak_label, labels_from_line, short_label

LAYOUTS = {"title", "cards", "steps", "bullets"}
CHIP = re.compile(r"^(line\s+\d+|note\s+\d+|makes|useful|key idea|how it works|why it matters)$", re.I)
TOPIC_PACKS: list[tuple[re.Pattern[str], str, list[str]]] = [
    (
        re.compile(r"langgraph", re.I),
        "LangGraph",
        [
            "Model the app as a graph of nodes and edges.",
            "Nodes run LLM calls, tools, or checks.",
            "Shared state moves through the graph as it runs.",
        ],
    ),
    (
        re.compile(r"\bmcb\b|circuit breaker", re.I),
        "Miniature circuit breaker",
        [
            "An MCB sits on the wiring and watches current.",
            "It trips when the load is higher than the circuit can take.",
            "That cut protects the wiring from overload and short faults.",
        ],
    ),
]


def _clip(text: str, max_len: int) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= max_len:
        return value
    return value[: max_len - 1].rstrip() + "…"


def clean_bullet(text: Any) -> str | None:
    value = " ".join(str(text or "").split())
    if not value or CHIP.match(value) or is_weak_label(value):
        return None
    words = re.findall(r"[A-Za-z0-9']+", value)
    if len(words) < 4:
        return None
    if len(value) > 110:
        value = value[:109].rsplit(" ", 1)[0].rstrip(".,;:") + "."
    if value[0].islower():
        value = value[0].upper() + value[1:]
    if value[-1] not in ".!?":
        value += "."
    return value


def clean_bullets(raw: Any) -> list[str]:
    items = raw if isinstance(raw, list) else []
    unique: list[str] = []
    seen: set[str] = set()
    for item in items:
        bullet = clean_bullet(item)
        if not bullet:
            continue
        key = bullet.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(bullet)
        if len(unique) == 3:
            break
    return unique


def _topic_pack(line: str, topic: str) -> tuple[str, list[str]] | None:
    haystack = f"{topic} {line}"
    for pattern, headline, bullets in TOPIC_PACKS:
        if pattern.search(haystack):
            return headline, bullets
    return None


def _clause_bullets(line: str) -> list[str]:
    parts = re.split(r"[.;:]|(?:\s+(?:and|which|that)\s+)", line or "")
    bullets: list[str] = []
    seen: set[str] = set()
    spoken = " ".join((line or "").split()).lower()
    for part in parts:
        bullet = clean_bullet(part)
        if not bullet:
            continue
        if bullet.lower().rstrip(".") == spoken.rstrip("."):
            continue
        key = bullet.lower()
        if key in seen:
            continue
        seen.add(key)
        bullets.append(bullet)
        if len(bullets) == 3:
            break
    return bullets


def fallback_slide(line: str, topic: str, index: int, total: int = 0) -> SlideContent:
    pack = _topic_pack(line, topic)
    title, _labels = labels_from_line(line, topic)
    headline = title
    if CHIP.match(headline or "") or is_weak_label(headline) or len((headline or "").split()) < 2:
        headline = (pack[0] if pack else "") or topic or "Key idea"

    bullets = _clause_bullets(line)
    if pack:
        extra = [item for item in pack[1] if item.lower() not in {b.lower() for b in bullets}]
        bullets = (bullets + extra)[:3]
    pads = [
        f"{short_label(topic or headline, 4, 28)} is the idea this beat is teaching.",
        "This step sits inside the larger workflow.",
        "Keep this point in mind as the demo continues.",
    ]
    for pad in pads:
        if len(bullets) >= 3:
            break
        bullets.append(pad)

    layout: str = "title" if index == 0 else "cards"
    if re.search(r"\b(then|next|step|first|finally)\b", line or "", re.I):
        layout = "steps"

    kicker = topic if topic and topic.lower() != headline.lower() else "Live training demo"
    if total:
        kicker = f"{kicker} · {index + 1} of {total}"

    return SlideContent(
        headline=_clip(headline, 56),
        kicker=_clip(kicker, 48),
        bullets=bullets[:3],
        layout=layout if layout in LAYOUTS else "cards",
    )


def slide_from_item(
    item: dict[str, Any],
    line: str,
    index: int,
    topic: str,
    total: int = 0,
) -> SlideContent:
    raw = item.get("slide") if isinstance(item.get("slide"), dict) else {}
    bullets = clean_bullets(raw.get("bullets") or item.get("bullets"))
    headline = _clip(str(raw.get("headline") or item.get("beatTitle") or item.get("title") or ""), 56)
    kicker = _clip(str(raw.get("kicker") or item.get("kicker") or topic or ""), 48)
    layout = str(raw.get("layout") or item.get("layout") or "").lower()
    if layout not in LAYOUTS:
        layout = "cards"
    if CHIP.match(headline) or len(headline.split()) < 2:
        headline = ""

    fallback = fallback_slide(line, topic, index, total)
    if not headline:
        headline = fallback.headline
    if not kicker:
        kicker = fallback.kicker
    if len(bullets) < 3:
        extras = [b for b in fallback.bullets if b.lower() not in {x.lower() for x in bullets}]
        bullets = (bullets + extras)[:3]
    if layout == "cards" and index == 0 and not (raw.get("layout") or item.get("layout")):
        layout = fallback.layout

    return SlideContent(
        headline=headline,
        kicker=kicker,
        bullets=bullets[:3],
        layout=layout,  # type: ignore[arg-type]
    )
