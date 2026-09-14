from fastapi.testclient import TestClient

from app.main import _hits, app, should_skip_rate_limit


client = TestClient(app)


def setup_function() -> None:
    _hits.clear()


def test_should_skip_health_config_and_preflight() -> None:
    assert should_skip_rate_limit("GET", "/health") is True
    assert should_skip_rate_limit("GET", "/api/config/public") is True
    assert should_skip_rate_limit("OPTIONS", "/api/lesson") is True
    assert should_skip_rate_limit("POST", "/api/lesson") is False
    assert should_skip_rate_limit("POST", "/api/tts") is False


def test_health_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "providers" in body
    assert "GROQ_API_KEY" not in str(body)


def test_public_config_has_no_secrets() -> None:
    response = client.get("/api/config/public")
    assert response.status_code == 200
    body = response.json()
    blob = str(body).lower()
    assert "api_key" not in blob
    assert "session_token" not in blob
    assert "maxScriptLines" in body
    assert "appName" in body


SAMPLE_LESSON = {
    "title": "MCB Basics",
    "topic": "MCB Basics",
    "level": "script",
    "language": "en",
    "segments": [
        {
            "id": "s1",
            "title": "Definition",
            "speech": "An MCB is a miniature circuit breaker.",
            "slide": {
                "headline": "MCB protects a circuit",
                "kicker": "How it works",
                "bullets": [
                    "An MCB watches current on the wiring path.",
                    "It trips when the load is higher than the circuit can take.",
                    "That cut protects the wiring from overload and short faults.",
                ],
                "layout": "cards",
            },
            "board": {
                "mode": "replace",
                "elements": [
                    {"id": "a", "type": "text", "text": "Makes"},
                    {"id": "b", "type": "rectangle", "label": {"text": "Useful"}},
                ],
            },
        }
    ],
}


def test_export_pptx() -> None:
    response = client.post("/api/export", json={"lesson": SAMPLE_LESSON, "format": "pptx"})
    assert response.status_code == 200
    assert "presentationml" in response.headers["content-type"]
    assert response.content[:2] == b"PK"
    assert "mcb-basics.pptx" in response.headers.get("content-disposition", "")


def test_export_pdf() -> None:
    response = client.post("/api/lesson/export", json={"lesson": SAMPLE_LESSON, "format": "pdf"})
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"


def test_export_docx() -> None:
    response = client.post("/api/lesson/export", json={"lesson": SAMPLE_LESSON, "format": "docx"})
    assert response.status_code == 200
    assert "wordprocessingml" in response.headers["content-type"]
    assert response.content[:2] == b"PK"


def test_export_uses_slide_not_board_chips() -> None:
    from io import BytesIO
    from zipfile import ZipFile

    from app.schemas.lesson import Lesson
    from app.services.export_deck import build_export

    lesson = Lesson.model_validate(SAMPLE_LESSON)
    data, _, name = build_export(lesson, "docx")
    assert name == "mcb-basics.docx"
    with ZipFile(BytesIO(data)) as archive:
        xml = archive.read("word/document.xml").decode()
    assert "MCB protects a circuit" in xml
    assert "trips when the load" in xml
    assert "Makes" not in xml
    assert "Useful" not in xml


def test_lesson_requires_script() -> None:
    response = client.post("/api/lesson", json={"script": "  "})
    assert response.status_code == 400
    assert response.json()["error"] == "script is required"


def test_tts_requires_text() -> None:
    response = client.post("/api/tts", json={"text": ""})
    assert response.status_code == 400
    assert response.json()["error"] == "text is required"


def test_stt_rejects_oversized_audio(monkeypatch) -> None:
    from app.core.settings import settings

    monkeypatch.setattr(settings, "max_stt_bytes", 8)
    response = client.post(
        "/api/stt",
        files={"audio": ("speech.webm", b"0123456789", "audio/webm")},
    )
    assert response.status_code == 413


def test_public_config_not_rate_limited() -> None:
    from app.core.settings import settings

    for _ in range(settings.rate_limit_per_minute + 5):
        response = client.get("/api/config/public")
        assert response.status_code == 200
