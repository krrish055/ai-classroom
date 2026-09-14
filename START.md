# Start

Script in → slides + talking avatar out. Spoken lines stay **verbatim**.

## Need

- Python **3.11+**
- Node **20+**
- A Groq key (slides)
- A Simli key + face id (avatar)

## One-time setup

From the repo root:

```bash
python -m pip install -r backend/requirements.txt
npm install
npm --prefix frontend install
copy .env.example .env
```

Then open `.env` and fill the keys below. **Never commit `.env`.**

## `.env` — what to fill

Copy `.env.example`. Change only these:

| Key | What |
|---|---|
| `GROQ_API_KEY` | Groq API key. Without it, slides stay generic. |
| `SIMLI_API_KEY` | Simli API key. |
| `SIMLI_FACE_ID` | Simli face id for the avatar. |
| `APP_DISPLAY_NAME` | Brand on screen, e.g. `Krrish`. Leave blank for no name. |

Leave the rest as-is unless you know you need to change it:

| Key | Default | Why |
|---|---|---|
| `VITE_API_BASE_URL` | `http://127.0.0.1:8787` | Frontend → API |
| `AVATAR_ENABLED` | `true` | Face on/off |
| `AVATAR_MODULE` | `simli` | Must stay `simli` for the face |
| `TTS_PROVIDER` | `edge` | Voice (no extra key) |
| `LLM_PROVIDER` | `groq` | Slide generation |

Avatar works only when **all three** are set: `AVATAR_ENABLED=true`, `SIMLI_API_KEY`, `SIMLI_FACE_ID`.

## Run

```bash
npm run dev
```

| App | URL |
|---|---|
| Classroom | http://127.0.0.1:5173 |
| API | http://127.0.0.1:8787 |
| Health | http://127.0.0.1:8787/health |

If the UI still shows the old brand or a missing route, stop the terminal and run `npm run dev` again (the API reload can stick).

## Use

1. Open the classroom.
2. Paste the spoken script (one idea per line).
3. **Present** — wait until slides are built, then the avatar speaks them.
4. At the end: download **session video**, **PPT**, **PDF**, or **Word**.

## Checks

```bash
python -m pytest
npm run verify
```

`verify` needs `npm run dev` already running.
