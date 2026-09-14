from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class BoardElement(BaseModel):
    id: str = ""
    type: str = "text"
    x: float = 80
    y: float = 80
    width: float | None = None
    height: float | None = None
    text: str | None = None
    fontSize: float | None = None
    strokeColor: str | None = None
    backgroundColor: str | None = None
    fillStyle: str | None = None
    startId: str | None = None
    endId: str | None = None
    label: dict[str, Any] | str | None = None
    points: list[Any] | None = None

    model_config = {"extra": "allow"}


class BoardBeat(BaseModel):
    mode: Literal["replace", "append"] = "replace"
    elements: list[BoardElement] = Field(default_factory=list)

    model_config = {"extra": "allow"}


class SlideContent(BaseModel):
    headline: str = ""
    kicker: str = ""
    bullets: list[str] = Field(default_factory=list)
    layout: Literal["title", "cards", "steps", "bullets"] = "cards"

    model_config = {"extra": "allow"}


class LessonSegment(BaseModel):
    id: str
    title: str
    speech: str
    board: BoardBeat
    slide: SlideContent = Field(default_factory=SlideContent)

    model_config = {"extra": "allow"}


class Lesson(BaseModel):
    title: str
    topic: str = ""
    level: str = "beginner"
    language: str = "en"
    segments: list[LessonSegment]

    model_config = {"extra": "allow"}


class LessonRequest(BaseModel):
    """script is the source of truth; query is accepted as a legacy alias."""

    script: str | None = None
    query: str | None = None
    level: str | None = None


class LessonResponse(BaseModel):
    lesson: Lesson
    provider: str
    avatarEnabled: bool


class SpeechRequest(BaseModel):
    text: str = ""


class LessonExportRequest(BaseModel):
    lesson: dict[str, Any]
    format: str = "pptx"
