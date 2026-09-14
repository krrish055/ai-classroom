# ADR-005: HTTP present flow (verbatim script)

- Status: Accepted
- Date: 2026-09-14

## Context

A realtime conversation bus (WebSocket audio chunks, interruptions, barge-in) would fit a “Future Self” chatbot. Tutor is a **scripted presentation**: 1–20 lines, then Present.

## Decision

Use request/response HTTP:

1. `POST /api/lesson` once per Present
2. `POST /api/tts` per line
3. `POST /api/avatar/session` once per classroom session

No WebSocket to Tutor’s backend. Simli’s own WebRTC is an implementation detail of the avatar SDK.

## Consequences

- Easy to test (`verify_lesson.py`)
- No interruption / overlapping speech handling
- Latency is per-line TTS + optional Simli buffer, not token streaming of a lecture
