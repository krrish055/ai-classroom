# Requirements

## Objective

Tutor presents a teacher-written script in a virtual classroom: **verbatim speech**, **related blackboard notes/diagrams**, and an optional **lip-synced avatar**. The LLM must not invent spoken text.

## Scope

### In Scope

- 1–20 line scripts, spoken exactly by TTS
- Blackboard notes and diagrams generated per line, animated during speech
- Plug-and-play LLM / TTS / STT / avatar from environment config
- Simli face lip-sync to the same TTS audio
- Optional microphone capture into the script box
- Local fallback notes when Groq is unavailable

### Out of Scope

- Free-form conversational tutoring (the LLM does not write the lecture)
- User accounts, billing, or multi-tenant isolation
- Persistent lesson history
- Production Kubernetes / CDN (documented as future)
- Hardcoded subject lessons (e.g. “Explain MCB” is demo config only)

## Functional Requirements

| ID | Requirement | Acceptance |
|---|---|---|
| FR-001 | User can paste 1–20 non-empty script lines | Present is enabled; extra lines are rejected |
| FR-002 | System speaks those lines verbatim | Every `/api/lesson` segment `speech` equals the original line |
| FR-003 | LLM (or local fallback) produces board notes/diagrams for each line | Each segment has board elements; labels are short, not the full sentence when Groq is on |
| FR-004 | Board updates in sync with the spoken line | Elements for line *n* appear while line *n* plays |
| FR-005 | Edge TTS synthesizes each line | `POST /api/tts` returns audio or a browser-TTS fallback payload |
| FR-006 | Simli lip-syncs when avatar is configured | Backend mints a session token; browser streams PCM 16 kHz to Simli |
| FR-007 | Missing Groq key does not block teaching | LLM falls back to local diagrams; speech still plays |
| FR-008 | Optional STT fills the script box | Mic uses Groq Whisper or browser speech recognition |
| FR-009 | Providers are selected from `.env` | Changing `LLM_PROVIDER` / `TTS_PROVIDER` / `STT_PROVIDER` / `AVATAR_MODULE` does not require code edits |
| FR-010 | Secrets stay on the backend | Browser never receives `GROQ_API_KEY` or `SIMLI_API_KEY` |

## Non-Functional Requirements

| ID | Area | Requirement |
|---|---|---|
| NFR-001 | Performance | Lesson plan for a 3-line script typically returns in a few seconds when Groq is healthy |
| NFR-002 | Reliability | Groq failure falls back to local notes; TTS failure can fall back to browser speech |
| NFR-003 | Security | `.env` gitignored; rate limit on API; CORS allowlist; no secrets in public config |
| NFR-004 | Scalability | Single-process modular monolith is enough for classroom demos; no independent service scaling yet |
| NFR-005 | Operability | `GET /health` reports providers and avatar readiness |
| NFR-006 | Maintainability | LLM / TTS / STT behind protocols; ADRs record why |

## Acceptance Criteria

- `npm run verify` passes: segment count matches lines, speech is unchanged, each beat has board elements, TTS returns 200.
- Classroom Present plays the pasted lines, board diagrams appear, Simli face is visible when avatar env is set.
- Public `/api/config/public` contains no API keys.
