# Component view

Backend dependency flow:

```mermaid
flowchart TB
  main[main.py routers]
  lesson[LessonService — plan_lesson / normalize_lesson]
  notesPrompt[teacher.py notes prompt]
  llmPort[LlmProvider]
  ttsPort[TtsProvider]
  sttPort[SttProvider]
  groqLlm[GroqLlmAdapter]
  localLlm[Local diagram adapter]
  edgeTts[EdgeTtsAdapter]
  groqStt[GroqSttAdapter]
  simliSvc[Simli session service]
  registry[providers/registry.py]

  main --> lesson
  main --> ttsPort
  main --> sttPort
  main --> simliSvc
  lesson --> notesPrompt
  lesson --> llmPort
  registry --> llmPort
  registry --> ttsPort
  registry --> sttPort
  llmPort --> groqLlm
  llmPort --> localLlm
  ttsPort --> edgeTts
  sttPort --> groqStt
```

Frontend: `useTeacherSession` orchestrates lesson + TTS + board draw; `useSimliAvatar` sends PCM; `boardRenderer` converts elements to Excalidraw.

Routers do not call Groq/Simli SDKs directly except through adapters/services.
