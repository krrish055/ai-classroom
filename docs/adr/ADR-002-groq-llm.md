# ADR-002: Groq for blackboard LLM (not speech)

- Status: Accepted
- Date: 2026-09-14

## Context

The product forbids the model from writing the lecture. We still need diagrams and short notes. Groq is the chosen hosted LLM (fast, JSON mode). Speech must remain the teacher’s script.

## Decision

- `LLM_PROVIDER=groq` with `LLM_FALLBACK_PROVIDER=local`
- System prompt asks only for board JSON
- `normalize_lesson` overwrites `speech` with the original lines
- Local heuristic diagrams run when the Groq key is missing or the call fails

## Consequences

- Teaching works offline-of-Groq
- Note quality depends on Groq when the key is set
- STT can reuse the same Groq account (Whisper) without coupling it to speech generation
