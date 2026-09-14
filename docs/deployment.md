# Deployment

Tutor is currently a **two-process demo**: Uvicorn (API) and Vite (web). There is no production cluster, load balancer, or managed database.

## Topology

See [diagrams/deployment.md](diagrams/deployment.md).

## Environment

All secrets live in backend `.env`. Frontend public env is only `VITE_API_BASE_URL` (Vite `envDir` is the repo root).

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | LLM notes + optional Whisper |
| `GROQ_BASE_URL` | `https://api.groq.com` (do not append `/openai/v1`; the SDK adds it) |
| `SIMLI_API_KEY` | Server-side session mint |
| `SIMLI_FACE_ID` | Avatar face |
| `CORS_ORIGIN` | Browser origin allowlist |
| `LLM_PROVIDER` / `TTS_PROVIDER` / `STT_PROVIDER` | Adapter names |
| `AVATAR_ENABLED` / `AVATAR_MODULE` | `true` / `simli` to enable the face |

Never put real keys in `.env.example`, docs, or GitHub issues.

## Health

`GET /health` must return `ok: true` before sending traffic to `/api/lesson`.

## Rollback

1. Keep the previous Git revision
2. Restore the previous `.env` if config caused the fault
3. Restart `npm run dev` (or the two processes)
4. Confirm `/health` and `npm run verify`

There is no blue/green or migrate/rollback for data — Tutor has no database yet.

## Scaling notes

In-memory rate limiting is **per process**. Multiple Uvicorn workers would not share the counter. Sticky sessions are not required (no server session store). Simli WebRTC is peer/livekit to Simli’s cloud, not to Tutor’s server.
