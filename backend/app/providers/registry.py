from __future__ import annotations

from app.core.settings import settings
from app.providers.llm.groq_llm import GroqLlmProvider
from app.providers.llm.local_llm import LocalLlmProvider
from app.providers.stt.groq_stt import BrowserSttProvider, GroqSttProvider
from app.providers.tts.edge_tts_provider import BrowserTtsProvider, EdgeTtsProvider

LLM_REGISTRY = {
    "groq": GroqLlmProvider,
    "local": LocalLlmProvider,
}
TTS_REGISTRY = {
    "edge": EdgeTtsProvider,
    "browser": BrowserTtsProvider,
}
STT_REGISTRY = {
    "groq": GroqSttProvider,
    "browser": BrowserSttProvider,
}


def _resolve(registry: dict, primary: str, fallback: str, kind: str):
    primary_name = (primary or "").strip().lower()
    fallback_name = (fallback or "").strip().lower()
    if primary_name not in registry:
        raise RuntimeError(f"Unknown {kind} provider '{primary_name}'")
    provider = registry[primary_name]()
    if provider.is_ready():
        return provider
    if fallback_name and fallback_name in registry:
        fallback_provider = registry[fallback_name]()
        if fallback_provider.is_ready():
            return fallback_provider
    raise RuntimeError(f"No ready {kind} provider. Set keys or change {kind.upper()}_PROVIDER.")


def resolve_llm():
    return _resolve(LLM_REGISTRY, settings.llm_provider, settings.llm_fallback_provider, "llm")


def resolve_tts():
    return _resolve(TTS_REGISTRY, settings.tts_provider, settings.tts_fallback_provider, "tts")


def resolve_stt():
    return _resolve(STT_REGISTRY, settings.stt_provider, settings.stt_fallback_provider, "stt")
