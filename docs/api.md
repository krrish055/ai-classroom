# API

FastAPI serves OpenAPI at [http://127.0.0.1:8787/docs](http://127.0.0.1:8787/docs). There is **no user authentication**. CORS is limited to `CORS_ORIGIN`. Mutating routes are rate-limited (`RATE_LIMIT_PER_MINUTE`). `/health`, `GET /api/config/public`, and CORS `OPTIONS` are excluded.

Errors: `{ "error": "<message>" }` (validation errors may include `details`).

## `GET /health`

Liveness + resolved providers. No secrets.

```json
{ "ok": true, "app": "tutor", "providers": { "llm": "groq", "tts": "edge", "stt": "browser" }, "avatarEnabled": true, "avatarModule": "simli" }
```

## `GET /api/config/public`

Frontend bootstrap. Includes `demoScript`, provider names, `avatarEnabled`, limits. **Never includes API keys or face secrets beyond what is required to run the UI** (face id stays server-side; the browser only gets a session token later).

## `POST /api/lesson`

Plan a lesson from a script.

Request:

```json
{ "script": "An MCB is a miniature circuit breaker.\nIt protects wiring from overload." }
```

`query` is accepted as a legacy alias for `script`.

| Status | When |
|---|---|
| 200 | `{ lesson, provider, avatarEnabled }` |
| 400 | Empty script, too many chars/lines |
| 422 | Invalid body |
| 429 | Rate limit |
| 500 | Planner failed (Groq should already have fallen back to local) |

Invariant: `lesson.segments[i].speech` equals script line `i`.

## `POST /api/tts`

Synthesize one line.

```json
{ "text": "An MCB is a miniature circuit breaker." }
```

Success: `audio/mpeg` body, header `X-TTS-Provider: edge`. Fallback JSON: `{ "provider": "browser", "fallback": true, "text": "...", "speechRate": 1 }`.

400 if text empty or longer than `MAX_SPEECH_CHARS`.

## `POST /api/avatar/session`

Mints a Simli session token using the **server** API key. Browser uses `simli-client` with that token only.

200: `{ "session_token": "..." }`  
400: avatar not configured  
502: Simli rejected the request

## `POST /api/stt`

`multipart/form-data` field `audio`. Returns `{ "provider", "text" }`. Browser-only STT returns `client_side: true` and empty text (the browser handles recognition).
