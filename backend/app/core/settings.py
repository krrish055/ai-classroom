from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    app_name: str = Field(default="tutor", alias="APP_NAME")
    app_display_name: str = Field(default="", alias="APP_DISPLAY_NAME")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8787, alias="PORT")
    cors_origin: str = Field(default="http://127.0.0.1:5173", alias="CORS_ORIGIN")
    rate_limit_per_minute: int = Field(default=90, alias="RATE_LIMIT_PER_MINUTE")
    max_query_chars: int = Field(default=4000, alias="MAX_QUERY_CHARS")
    max_speech_chars: int = Field(default=2000, alias="MAX_SPEECH_CHARS")
    max_script_lines: int = Field(default=50, alias="MAX_SCRIPT_LINES")
    max_stt_bytes: int = Field(default=8 * 1024 * 1024, alias="MAX_STT_BYTES")
    max_board_elements_per_segment: int = Field(
        default=18, alias="MAX_BOARD_ELEMENTS_PER_SEGMENT"
    )
    demo_script: str = Field(
        default="An MCB is a miniature circuit breaker.\nIt protects wiring from overload and short circuit.\nWhen current is too high, it trips and cuts the power.",
        alias="DEMO_SCRIPT",
    )

    llm_provider: str = Field(default="groq", alias="LLM_PROVIDER")
    llm_fallback_provider: str = Field(default="local", alias="LLM_FALLBACK_PROVIDER")
    llm_model: str = Field(default="openai/gpt-oss-20b", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.5, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=4096, alias="LLM_MAX_TOKENS")

    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_base_url: str = Field(
        default="https://api.groq.com", alias="GROQ_BASE_URL"
    )
    groq_timeout_seconds: int = Field(default=45, alias="GROQ_REQUEST_TIMEOUT_SECONDS")

    @property
    def groq_client_base_url(self) -> str:
        url = (self.groq_base_url or "https://api.groq.com").rstrip("/")
        if url.endswith("/openai/v1"):
            url = url[: -len("/openai/v1")]
        return url or "https://api.groq.com"

    tts_provider: str = Field(default="edge", alias="TTS_PROVIDER")
    tts_fallback_provider: str = Field(default="browser", alias="TTS_FALLBACK_PROVIDER")
    tts_voice: str = Field(default="en-IN-NeerjaNeural", alias="TTS_VOICE")
    tts_rate: str = Field(default="+0%", alias="TTS_RATE")
    tts_speech_rate: float = Field(default=1.0, alias="TTS_SPEECH_RATE")

    stt_provider: str = Field(default="groq", alias="STT_PROVIDER")
    stt_fallback_provider: str = Field(default="browser", alias="STT_FALLBACK_PROVIDER")
    stt_model: str = Field(default="whisper-large-v3-turbo", alias="STT_MODEL")
    stt_language: str = Field(default="en", alias="STT_LANGUAGE")

    board_title_color: str = Field(default="#1e3a5f", alias="BOARD_TITLE_COLOR")
    board_box_bg: str = Field(default="#a5d8ff", alias="BOARD_BOX_BG")
    board_box_stroke: str = Field(default="#1971c2", alias="BOARD_BOX_STROKE")
    board_accent: str = Field(default="#d97757", alias="BOARD_ACCENT")
    board_text_color: str = Field(default="#212529", alias="BOARD_TEXT_COLOR")
    board_second_bg: str = Field(default="#ffd8a8", alias="BOARD_SECOND_BG")
    board_third_bg: str = Field(default="#b2f2bb", alias="BOARD_THIRD_BG")

    avatar_enabled: bool = Field(default=False, alias="AVATAR_ENABLED")
    avatar_module: str = Field(default="none", alias="AVATAR_MODULE")
    simli_api_key: str = Field(default="", alias="SIMLI_API_KEY")
    simli_face_id: str = Field(default="", alias="SIMLI_FACE_ID")
    simli_base_url: str = Field(
        default="https://api.simli.ai", alias="SIMLI_BASE_URL"
    )
    simli_max_session_length: int = Field(default=600, alias="SIMLI_MAX_SESSION_LENGTH")
    simli_max_idle_time: int = Field(default=180, alias="SIMLI_MAX_IDLE_TIME")

    @property
    def display_name(self) -> str:
        return (self.app_display_name or "").strip()

    @property
    def avatar_ready(self) -> bool:
        return bool(
            self.avatar_enabled
            and self.avatar_module == "simli"
            and self.simli_api_key
            and self.simli_face_id
        )


_cached: Settings | None = None
_cached_mtime = -1.0


def load_settings() -> Settings:
    """Re-read .env when it changes so APP_DISPLAY_NAME updates without a stuck reload."""
    global _cached, _cached_mtime
    env_path = ROOT_DIR / ".env"
    mtime = env_path.stat().st_mtime if env_path.exists() else 0.0
    if _cached is None or mtime != _cached_mtime:
        _cached = Settings()
        _cached_mtime = mtime
    return _cached


class _SettingsProxy:
    def __getattr__(self, item: str):
        return getattr(load_settings(), item)


settings = _SettingsProxy()
