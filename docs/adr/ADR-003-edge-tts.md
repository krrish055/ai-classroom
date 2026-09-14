# ADR-003: Microsoft Edge TTS

- Status: Accepted
- Date: 2026-09-14

## Context

Tutor needs reliable TTS with no paid key for the default path. ElevenLabs-class voices are out of scope for this MVP.

## Decision

Use `edge-tts` (`TTS_PROVIDER=edge`) with a neural voice (`TTS_VOICE`, default `en-IN-NeerjaNeural`). Fallback: browser `speechSynthesis`.

## Consequences

- Zero TTS API key in `.env` for the happy path
- MP3 from Edge is decoded to PCM16 16 kHz for Simli
- Voice quality/latency is bound to Microsoft’s public Edge voices
