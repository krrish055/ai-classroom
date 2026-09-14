const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function readError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return body.error || body.detail || res.statusText;
  } catch {
    return res.statusText;
  }
}

export async function getPublicConfig() {
  const res = await fetch(`${API_BASE}/api/config/public`);
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function createLesson(script: string) {
  const res = await fetch(`${API_BASE}/api/lesson`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ script }),
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export type LessonStreamEvent = {
  event: "meta" | "segment" | "lesson" | "done" | "error";
  provider?: string;
  lesson?: unknown;
  index?: number;
  segment?: unknown;
  error?: string;
};

export async function streamLesson(
  script: string,
  onEvent: (event: LessonStreamEvent) => void,
  signal?: AbortSignal,
) {
  const res = await fetch(`${API_BASE}/api/lesson/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ script }),
    signal,
  });
  if (!res.ok) throw new Error(await readError(res));
  if (!res.body) throw new Error("Lesson stream is empty");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n");
    buffer = parts.pop() || "";
    for (const line of parts) {
      if (!line.trim()) continue;
      onEvent(JSON.parse(line) as LessonStreamEvent);
    }
  }
  if (buffer.trim()) onEvent(JSON.parse(buffer) as LessonStreamEvent);
}

export async function synthesizeSpeech(text: string) {
  const res = await fetch(`${API_BASE}/api/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(await readError(res));

  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return res.json();
  }

  const blob = await res.blob();
  return {
    provider: res.headers.get("X-TTS-Provider") || "edge",
    mimeType: contentType,
    blob,
    audioUrl: URL.createObjectURL(blob),
  };
}

export async function createAvatarSession() {
  const res = await fetch(`${API_BASE}/api/avatar/session`, { method: "POST" });
  if (!res.ok) throw new Error(await readError(res));
  return res.json() as Promise<{ session_token: string }>;
}

export async function exportLesson(lesson: unknown, format: "pptx" | "pdf" | "docx") {
  const body = JSON.stringify({ lesson, format });
  const headers = { "Content-Type": "application/json" };
  const urls = [`${API_BASE}/api/export`, `${API_BASE}/api/lesson/export`];
  let res: Response | null = null;
  let lastError = "Export failed";
  for (const url of urls) {
    res = await fetch(url, { method: "POST", headers, body });
    if (res.ok) break;
    lastError = await readError(res);
    if (res.status !== 404) throw new Error(lastError);
  }
  if (!res?.ok) throw new Error(lastError);
  const blob = await res.blob();
  const header = res.headers.get("Content-Disposition") || "";
  const matched = header.match(/filename="?([^"]+)"?/i);
  return { blob, filename: matched?.[1] || `training-deck.${format}` };
}

export async function transcribeAudio(blob: Blob) {
  const form = new FormData();
  form.append("audio", blob, "speech.webm");
  const res = await fetch(`${API_BASE}/api/stt`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}
