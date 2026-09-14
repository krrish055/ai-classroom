# Contributing

## Workflow

`main` is the default branch. Work on `feature/…` or `fix/…` branches. Open a PR using the template.

## Commits

```
feat: add Simli avatar adapter
fix: handle Groq doubled /openai/v1 base URL
refactor: isolate TTS provider port
test: assert lesson speech is verbatim
docs: update present sequence
```

## Before you push

- No secrets
- `python -m pytest`
- `python -m compileall backend` if you touched Python
- Do not add hardcoded lessons; keep demos in `.env` `DEMO_SCRIPT`

## Code

Readable over clever. New providers implement the protocols in `backend/app/providers/base.py`. The LLM path must not author speech.
