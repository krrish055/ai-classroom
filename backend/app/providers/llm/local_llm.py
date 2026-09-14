from __future__ import annotations

from typing import Any

from app.services.board_notes import build_local_notes


class LocalLlmProvider:
    """Dev fallback: diagram notes only. Speech is never invented here."""

    name = "local"

    def is_ready(self) -> bool:
        return True

    async def complete_json(self, system: str, user: str) -> dict[str, Any]:
        del system
        lines: list[str] = []
        for raw in user.splitlines():
            stripped = raw.strip()
            if not stripped:
                continue
            if stripped[0].isdigit() and "." in stripped[:4]:
                lines.append(stripped.split(".", 1)[1].strip())
        if not lines:
            lines = [user.strip()]
        return build_local_notes(lines)
