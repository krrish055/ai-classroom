import { useState } from "react";
import { FileText, Presentation, FileType, Video } from "lucide-react";
import { exportLesson } from "../services/api";
import type { SessionVideo } from "../services/stageRecorder";
import type { Lesson } from "../types/lesson";

type ThankYouStageProps = {
  lesson: Lesson;
  brand: string;
  sessionVideo?: SessionVideo | null;
  onClose: () => void;
};

const FORMATS = [
  { id: "pptx" as const, label: "PowerPoint", hint: "Editable slides", icon: Presentation },
  { id: "pdf" as const, label: "PDF", hint: "Share-ready file", icon: FileText },
  { id: "docx" as const, label: "Word", hint: "Notes document", icon: FileType },
];

function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1500);
}

export function ThankYouStage({ lesson, brand, sessionVideo, onClose }: ThankYouStageProps) {
  const [busy, setBusy] = useState<string>("");
  const [error, setError] = useState("");

  async function download(format: "pptx" | "pdf" | "docx") {
    setBusy(format);
    setError("");
    try {
      const { blob, filename } = await exportLesson(lesson, format);
      saveBlob(blob, filename);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not download this file.");
    } finally {
      setBusy("");
    }
  }

  function downloadVideo() {
    if (!sessionVideo) return;
    setError("");
    saveBlob(sessionVideo.blob, sessionVideo.filename);
  }

  return (
    <div className="thanks-stage">
      <p className="thanks-kicker">{brand || "Training complete"}</p>
      <h2>Thank you</h2>
      <p className="thanks-copy">
        This presentation is over. Download the recorded session, or the same slides as PPT, PDF, or Word.
      </p>
      <ul className="thanks-downloads">
        <li className="thanks-video-item">
          <button
            type="button"
            className="thanks-download featured session-video"
            onClick={downloadVideo}
            disabled={!sessionVideo || Boolean(busy)}
          >
            <Video size={28} strokeWidth={1.7} />
            <span>
              <strong>{sessionVideo ? "Session video" : "Video unavailable"}</strong>
              <span>{sessionVideo ? "Slides + avatar + voice" : "This run was not captured"}</span>
            </span>
          </button>
        </li>
        {FORMATS.map((item) => {
          const Icon = item.icon;
          return (
            <li key={item.id}>
              <button
                type="button"
                className="thanks-download"
                onClick={() => void download(item.id)}
                disabled={Boolean(busy)}
              >
                <Icon size={28} strokeWidth={1.7} />
                <strong>{busy === item.id ? "Preparing..." : item.label}</strong>
                <span>{item.hint}</span>
              </button>
            </li>
          );
        })}
      </ul>
      {error ? <p className="thanks-error">{error}</p> : null}
      <button type="button" className="ghost-btn" onClick={onClose}>
        Back to classroom
      </button>
    </div>
  );
}
