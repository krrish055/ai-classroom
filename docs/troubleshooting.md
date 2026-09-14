# Troubleshooting

## Classroom loads, notes look like the script in boxes

`LLM · local` means Groq is not ready. Check `GROQ_API_KEY` and `GROQ_BASE_URL=https://api.groq.com` (not `.../openai/v1`). Restart the API after changing `.env`.

## `/api/lesson` 500 with Groq `unknown_url` / doubled `/openai/v1`

The Groq SDK already appends `/openai/v1`. Base URL must be `https://api.groq.com`. Tutor also strips a trailing `/openai/v1` if present.

## Avatar blank or “Avatar is not configured”

Need `AVATAR_ENABLED=true`, `AVATAR_MODULE=simli`, `SIMLI_API_KEY`, `SIMLI_FACE_ID`. Confirm `GET /health` → `avatarEnabled: true`. Simli `startup_error` usually means a bad face id or depleted minutes.

## TTS silent, teaching continues

Edge TTS may have fallen back to browser speech. Allow autoplay. If Simli is connected, audio comes from the Simli `<audio>` element — unmute the tab.

## Board is a thin strip / empty

The blackboard needs height. Use a desktop-width window; the avatar overlays on smaller screens instead of hiding.

## 429 Too many requests

In-memory limiter (`RATE_LIMIT_PER_MINUTE`). Wait a minute or raise the env value locally.

## CORS errors

`CORS_ORIGIN` must match the Vite origin exactly, e.g. `http://127.0.0.1:5173`.

## Do not log

API keys, Simli tokens, raw audio blobs, or full user scripts in shared channels.
