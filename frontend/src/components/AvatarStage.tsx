import type { RefObject } from "react";
import { User } from "lucide-react";

type AvatarStageProps = {
  enabled: boolean;
  connected: boolean;
  speaking: boolean;
  status: string;
  videoRef: RefObject<HTMLVideoElement | null>;
  audioRef: RefObject<HTMLAudioElement | null>;
};

export function AvatarStage({
  enabled,
  connected,
  speaking,
  status,
  videoRef,
  audioRef,
}: AvatarStageProps) {
  return (
    <aside className="avatar-pip" aria-label={status || "Presenter avatar"}>
      <div className={`avatar-stage ${speaking ? "speaking" : ""} ${connected ? "live" : ""}`}>
        {!connected ? (
          <span className="avatar-fallback" aria-hidden="true">
            <User size={72} strokeWidth={1.25} />
          </span>
        ) : null}
        <video ref={videoRef} autoPlay playsInline muted />
        <audio ref={audioRef} autoPlay />
        {enabled && (speaking || connected) ? (
          <span className="avatar-dot">{speaking ? "Live" : "Ready"}</span>
        ) : null}
      </div>
    </aside>
  );
}
