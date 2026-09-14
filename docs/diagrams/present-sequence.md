# Present sequence

Happy path for one Present click:

```mermaid
sequenceDiagram
  actor User
  participant UI as Classroom UI
  participant API as FastAPI
  participant Groq as Groq LLM
  participant Edge as Edge TTS
  participant Simli as Simli

  User->>UI: Paste 1–20 lines, Present
  UI->>API: POST /api/avatar/session
  API->>Simli: compose/token (API key server-side)
  Simli-->>UI: session_token
  UI->>Simli: WebRTC start
  UI->>API: POST /api/lesson { script }
  API->>Groq: notes JSON only
  Groq-->>API: board beats
  API-->>UI: lesson (speech = original lines)
  loop each line
    UI->>API: POST /api/tts { text: line }
    API->>Edge: synthesize
    Edge-->>UI: mp3
    UI->>UI: decode PCM16 16 kHz
    UI->>Simli: sendAudioData
    UI->>UI: animate Excalidraw elements
    Simli-->>User: lip-synced face + audio
  end
```

If Groq is down, `plan_lesson` uses local diagrams; speech is still the script. If Simli is off, the UI plays Edge audio directly.

Rendered diagram: [workflow.svg](workflow.svg).
