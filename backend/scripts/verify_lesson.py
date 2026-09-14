from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

HOST = os.environ.get("HOST", "127.0.0.1")
PORT = os.environ.get("PORT", "8787")
SCRIPT = os.environ.get("VERIFY_SCRIPT") or os.environ.get("DEMO_SCRIPT") or (
    "An MCB is a miniature circuit breaker.\n"
    "It protects wiring from overload and short circuit.\n"
    "When current is too high, it trips and cuts the power."
)
BASE = f"http://{HOST}:{PORT}"


def get_json(url: str, data: dict | None = None) -> dict:
    body = None if data is None else json.dumps(data).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"} if data is not None else {},
        method="GET" if data is None else "POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_health() -> dict:
    for _ in range(20):
        try:
            return get_json(f"{BASE}/health")
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.5)
    raise SystemExit(f"Server did not become healthy at {BASE}/health")


def main() -> None:
    health = wait_health()
    print("[verify] health", health)
    payload = get_json(f"{BASE}/api/lesson", {"script": SCRIPT})
    lesson = payload["lesson"]
    expected = [line.strip() for line in SCRIPT.splitlines() if line.strip()]
    if len(lesson.get("segments") or []) != len(expected):
        raise SystemExit("Segment count does not match script lines")
    for index, segment in enumerate(lesson["segments"]):
        if segment.get("speech") != expected[index]:
            raise SystemExit(f"Speech was rewritten on line {index + 1}")
        if not segment.get("board", {}).get("elements"):
            raise SystemExit(f"Segment {segment.get('id')} missing board notes")

    tts_request = urllib.request.Request(
        f"{BASE}/api/tts",
        data=json.dumps({"text": lesson["segments"][0]["speech"]}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(tts_request, timeout=60) as response:
        tts_status = response.status

    avatar_ok = False
    if health.get("avatarEnabled"):
        session = get_json(f"{BASE}/api/avatar/session", {})
        avatar_ok = bool(session.get("session_token"))
        if not avatar_ok:
            raise SystemExit("Avatar session token missing")

    print(
        "[verify] ok",
        {
            "lines": len(expected),
            "provider": payload.get("provider"),
            "title": lesson.get("title"),
            "firstSpeech": lesson["segments"][0]["speech"],
            "ttsStatus": tts_status,
            "avatar": avatar_ok,
        },
    )


if __name__ == "__main__":
    main()
