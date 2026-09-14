from __future__ import annotations

import re
from typing import Any

from app.core.settings import settings

STOP = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "it",
    "its",
    "and",
    "or",
    "of",
    "to",
    "from",
    "for",
    "with",
    "that",
    "this",
    "when",
    "then",
    "than",
    "too",
    "very",
    "also",
    "into",
    "onto",
    "over",
    "under",
    "by",
    "as",
    "be",
    "been",
    "being",
    "does",
    "do",
    "did",
    "has",
    "have",
    "had",
    "will",
    "can",
    "may",
    "if",
    "in",
    "on",
    "at",
    "we",
    "you",
    "they",
    "them",
    "their",
    "which",
    "who",
    "whom",
    "what",
    "how",
    "why",
    "not",
    "but",
    "so",
    "just",
    "more",
    "most",
    "some",
    "any",
    "all",
    "our",
    "my",
    "me",
    "him",
    "her",
    "his",
    "currently",
}


def short_label(text: str, max_words: int = 4, max_chars: int = 28) -> str:
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9+\-/%]*", text or "")
    keep = [w for w in words if w.lower() not in STOP and len(w) >= 3]
    if not keep:
        keep = [w for w in words if len(w) >= 3][:max_words]
    label = " ".join(keep[:max_words]).strip() or (text or "Note")
    if len(label) > max_chars:
        label = label[: max_chars - 1].rstrip() + "…"
    return label[0].upper() + label[1:] if label else "Note"


def is_weak_label(text: str) -> bool:
    compact = re.sub(r"[^A-Za-z0-9]", "", text or "")
    return len(compact) < 3 or compact.lower() in STOP


def _ideas(text: str, limit: int = 8) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9+\-]{2,}", text or "")
    seen: set[str] = set()
    ideas: list[str] = []
    for word in words:
        key = word.lower()
        if key in STOP or key in seen or len(word) < 3:
            continue
        seen.add(key)
        ideas.append(word[0].upper() + word[1:])
        if len(ideas) == limit:
            break
    return ideas or ["Key idea"]


def topic_from_lines(lines: list[str]) -> str:
    ideas = _ideas(" ".join(lines[:4]), limit=4)
    return " ".join(ideas[:2]) if ideas else "Notes"


def _split_list(text: str) -> list[str]:
    chunk = re.split(r"\bfrom\b|\binto\b|\bagainst\b", text, maxsplit=1, flags=re.I)
    tail = chunk[1] if len(chunk) > 1 else text
    parts = re.split(r"\s*(?:,|/|&|\band\b|\bor\b)\s*", tail, flags=re.I)
    labels = [short_label(part, 3, 22) for part in parts if part.strip()]
    return [label for label in labels if not is_weak_label(label)][:4] or [short_label(text, 3, 22)]


def _unique(labels: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in labels:
        label = short_label(str(raw or ""), 5, 28)
        key = label.lower()
        if not label or is_weak_label(label) or key in seen:
            continue
        seen.add(key)
        out.append(label)
    return out


def _box(
    eid: str,
    kind: str,
    x: float,
    y: float,
    w: float,
    h: float,
    label: str,
    bg: str,
    stroke: str,
) -> dict[str, Any]:
    return {
        "id": eid,
        "type": kind,
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "backgroundColor": bg,
        "strokeColor": stroke,
        "fillStyle": "solid",
        "label": {"text": label},
    }


def _arrow(eid: str, start: str, end: str, label: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": eid,
        "type": "arrow",
        "x": 0,
        "y": 0,
        "startId": start,
        "endId": end,
        "strokeColor": settings.board_accent,
    }
    if label:
        payload["label"] = {"text": label}
    return payload


def dense_sheet(
    topic: str,
    labels: list[str],
    index: int = 0,
    beat_title: str = "",
) -> list[dict[str, Any]]:
    """Full 1180x720 aligned lesson sheet so the board never looks empty."""
    p = f"b{index + 1}"
    heading = short_label(beat_title or topic or "Notes", 6, 40)
    topic_label = short_label(topic or heading, 4, 22)
    ideas = _unique([heading, topic, *labels])
    pads = [
        f"What is {topic_label}",
        f"{topic_label} core",
        "How it works",
        "Why it matters",
        "Flow / steps",
        "Watch outs",
        f"Remember {topic_label}",
    ]
    for pad in pads:
        if len(ideas) >= 9:
            break
        ideas = _unique([*ideas, pad])

    while len(ideas) < 9:
        ideas.append(f"Note {len(ideas) + 1}")

    primary = settings.board_box_bg
    secondary = settings.board_second_bg
    tertiary = settings.board_third_bg
    stroke = settings.board_box_stroke
    accent = settings.board_accent

    hero, meaning, key = ideas[0], ideas[1], ideas[2]
    cards = ideas[3:9]
    footer = f"Takeaway · {topic_label}"

    elements: list[dict[str, Any]] = [
        {
            "id": f"{p}_title",
            "type": "text",
            "x": 56,
            "y": 24,
            "text": heading,
            "fontSize": 36,
            "strokeColor": settings.board_title_color,
        },
        _box(f"{p}_hero", "ellipse", 56, 88, 300, 112, hero[:28], primary, stroke),
        _arrow(f"{p}_a1", f"{p}_hero", f"{p}_mean", "is"),
        _box(f"{p}_mean", "rectangle", 420, 88, 360, 112, meaning[:28], secondary, accent),
        _arrow(f"{p}_a2", f"{p}_mean", f"{p}_key", "so"),
        _box(f"{p}_key", "diamond", 844, 84, 260, 120, key[:22], tertiary, stroke),
    ]

    positions = [(56, 248), (420, 248), (784, 248), (56, 400), (420, 400), (784, 400)]
    kinds = ["rectangle", "ellipse", "rectangle", "rectangle", "diamond", "rectangle"]
    colors = [primary, tertiary, secondary, secondary, tertiary, primary]
    parents = [f"{p}_hero", f"{p}_mean", f"{p}_key"]
    verbs = ["note", "also", "then"]

    for i, (card, (x, y)) in enumerate(zip(cards, positions)):
        eid = f"{p}_c{i}"
        elements.append(_box(eid, kinds[i], x, y, 320, 100, card[:28], colors[i], stroke))
        if i < 3:
            elements.append(_arrow(f"{p}_l{i}", parents[i], eid, verbs[i]))

    elements.append(
        _box(
            f"{p}_foot",
            "rectangle",
            56,
            548,
            1048,
            88,
            short_label(footer, 8, 48),
            tertiary,
            stroke,
        )
    )
    return elements[: settings.max_board_elements_per_segment]


def labels_from_line(line: str, topic: str = "") -> tuple[str, list[str]]:
    labels = _ideas(line)
    definition = re.search(r"^(.*?)\s+\bis\s+(?:a|an|the)\s+(.+)$", line, re.I)
    when = re.search(r"\bwhen\b(.+?)(?:,|\bit\b)(.+)$", line, re.I)
    protects = re.search(
        r"\b(protects?|prevents?|stops?|saves?)\s+(.+?)\s+from\s+(.+)$",
        line,
        re.I,
    )

    title = labels[0] if labels else (topic or "Notes")
    extra: list[str] = []

    if definition:
        left = short_label(definition.group(1) or topic, 3, 18)
        if not is_weak_label(left):
            right = short_label(definition.group(2), 5, 32)
            extra = [left, right, "Definition", "Use case"]
            title = left
    elif when:
        cond = short_label(when.group(1), 4, 24)
        extra = [cond + "?", *_split_list(when.group(2)), "Then", "Result"]
        title = "Trip logic" if re.search(r"\btrip", line, re.I) else "When / then"
    elif protects:
        extra = [
            short_label(protects.group(2), 3, 20),
            *_split_list(protects.group(3)),
            "Protects",
            "Hazard",
        ]
        title = "Protection"

    return title, _unique([title, topic, *extra, *labels])


def diagram_for_line(line: str, index: int, topic: str) -> tuple[str, list[dict[str, Any]]]:
    title, labels = labels_from_line(line, topic)
    return title, dense_sheet(topic, labels, index, title)


def build_local_notes(lines: list[str]) -> dict[str, Any]:
    topic = topic_from_lines(lines)
    segments = []
    for index, line in enumerate(lines):
        title, elements = diagram_for_line(line, index, topic)
        segments.append(
            {
                "id": f"s{index + 1}",
                "title": title,
                "board": {
                    "mode": "replace",
                    "elements": elements,
                },
            }
        )
    return {"title": topic, "topic": topic, "segments": segments}


def board_is_dense(elements: list[Any]) -> bool:
    if len(elements) < 8:
        return False
    xs: list[float] = []
    ys: list[float] = []
    for el in elements:
        if isinstance(el, dict):
            xs.append(float(el.get("x") or 0))
            ys.append(float(el.get("y") or 0))
        else:
            xs.append(float(getattr(el, "x", 0) or 0))
            ys.append(float(getattr(el, "y", 0) or 0))
    if not xs or not ys:
        return False
    return (max(ys) - min(ys) >= 240) and (max(xs) - min(xs) >= 360)
