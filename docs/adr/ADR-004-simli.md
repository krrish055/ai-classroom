# ADR-004: Simli for avatar lip-sync

- Status: Accepted
- Date: 2026-09-14

## Context

The classroom should show a talking face in sync with the script. Lip-sync must use the **same** audio Edge TTS already produced, not a second generated script.

## Decision

- Keep `SIMLI_API_KEY` on the backend
- `POST /api/avatar/session` returns a short-lived Simli token
- Frontend `simli-client` (Livekit transport) receives PCM16 16 kHz chunks
- Avatar is optional: `AVATAR_ENABLED` + face id; teaching continues without it

## Consequences

- Browser never holds the Simli API key
- Needs Simli minutes and a valid face id
- Double audio is avoided by not playing the local MP3 when Simli speak succeeds
