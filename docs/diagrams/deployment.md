# Deployment view

Current (development):

```mermaid
flowchart TB
  internet[Loopback / LAN]
  vite[Vite :5173]
  api[Uvicorn :8787]
  groq[Groq cloud]
  edge[Edge TTS cloud]
  simli[Simli cloud]

  internet --> vite
  vite --> api
  api --> groq
  api --> edge
  api --> simli
  vite --> simli
```

No load balancer, database, or object store. Secrets: process environment / `.env` on the API host. Health check: `GET /health`. Rollback: previous git revision + restart processes. See [../deployment.md](../deployment.md).
