# Local development

## Setup

1. Python 3.11+, Node 20+
2. `python -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt`
3. `npm install` and `npm --prefix frontend install`
4. Copy `.env.example` to `.env` and fill keys locally
5. `npm run dev`

Windows: `copy .env.example .env`. macOS/Linux: `cp .env.example .env`.

## Code standards

- Python: type hints on new functions; providers implement `LlmProvider` / `TtsProvider` / `SttProvider` in `backend/app/providers/base.py`
- Do not generate spoken text in the LLM path; `normalize_lesson` overwrites `speech`
- Secrets only in `.env` (gitignored)
- Frontend talks only to Tutor’s API, never Groq/Simli with raw API keys
- Prefer small modules over `utils.py` dumping grounds

## Useful commands

```bash
npm run dev
npm run verify
python -m pytest
python -m compileall backend
```

## Project map

```
backend/app/main.py              HTTP
backend/app/services/lesson.py   plan + verbatim normalize
backend/app/prompts/teacher.py   notes/diagram prompt
backend/app/providers/           groq / edge / local adapters
frontend/src/pages/ClassroomPage.tsx
frontend/src/hooks/useTeacherSession.ts
frontend/src/hooks/useSimliAvatar.ts
docs/diagrams/architecture.svg
docs/diagrams/workflow.svg
```
