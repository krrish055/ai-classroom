# System context

Who sits outside Tutor?

```mermaid
flowchart TB
  user[Teacher / learner]
  tutor[Tutor classroom]
  groq[Groq — LLM notes + optional Whisper]
  edge[Microsoft Edge TTS]
  simli[Simli — lip-sync avatar]

  user -->|script, Present, optional mic| tutor
  tutor -->|JSON notes prompt| groq
  tutor -->|script lines| edge
  tutor -->|session token + PCM audio| simli
  tutor -->|spoken lines, board, face| user
```

Tutor owns the classroom UI and the FastAPI backend. Groq, Edge TTS, and Simli are external providers. The LLM never owns the spoken lecture.

Rendered diagram: [architecture.svg](architecture.svg).
