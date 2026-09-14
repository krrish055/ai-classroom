# Testing

## Layers

| Layer | How |
|---|---|
| Unit | `python -m pytest` — script split, local diagrams, verbatim normalize, API validation |
| Smoke | `npm run verify` — live API: speech unchanged, board present, TTS, optional Simli token |
| Manual E2E | Classroom Present: listen, watch board, watch Simli |

There is no mocked Groq/Simli suite yet. Unit tests must not need API keys.

## Run

```bash
python -m pip install -r backend/requirements-dev.txt
python -m pytest
npm run verify   # API must already be up
```

## Minimum cases

- Script with 1 line and 3 lines
- Speech field cannot differ from the source line even if the planner JSON contains other text
- Empty script rejected
- Local notes produce shapes (ellipse/rectangle/diamond/arrow), not only a transcript box, for the MCB demo
- Verify smoke: TTS 200; if `avatarEnabled`, session token present

## CI

`.github/workflows/ci.yml` compiles the backend, runs unit tests, and typechecks the frontend. It does **not** call Groq or Simli.
