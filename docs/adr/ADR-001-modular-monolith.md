# ADR-001: Modular FastAPI monolith

- Status: Accepted
- Date: 2026-09-14

## Context

Tutor is an MVP classroom: one browser, one API, four providers (LLM, TTS, STT, avatar). Independent scaling of those providers is not required.

## Decision

Ship a single FastAPI process (`backend/app`) with provider modules behind protocols. React/Vite is a separate frontend process, not a BFF farm.

## Consequences

- Simple local run (`npm run dev`)
- Shared deploy lifecycle — LLM and TTS cannot scale apart
- Provider swap is a registry + env change, not a new microservice
