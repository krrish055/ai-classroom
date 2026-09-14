from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LlmProvider(Protocol):
    name: str

    def is_ready(self) -> bool: ...

    async def complete_json(self, system: str, user: str) -> dict[str, Any]: ...


@runtime_checkable
class TtsProvider(Protocol):
    name: str

    def is_ready(self) -> bool: ...

    async def synthesize(self, text: str) -> dict[str, Any]: ...


@runtime_checkable
class SttProvider(Protocol):
    name: str

    def is_ready(self) -> bool: ...

    async def transcribe(
        self, data: bytes, filename: str, mime_type: str
    ) -> dict[str, Any]: ...
