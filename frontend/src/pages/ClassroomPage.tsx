import { useEffect, useRef, useState } from "react";
import { Excalidraw } from "@excalidraw/excalidraw";
import "@excalidraw/excalidraw/index.css";
import { Mic, Square, Sun, Moon } from "lucide-react";
import { AvatarStage } from "../components/AvatarStage";
import { LessonSlide } from "../components/LessonSlide";
import { ThankYouStage } from "../components/ThankYouStage";
import { useSimliAvatar } from "../hooks/useSimliAvatar";
import { useTeacherSession } from "../hooks/useTeacherSession";
import { displayName, studioTitle } from "../lib/brand";
import type { ExcalidrawAPI } from "../services/boardRenderer";

export default function ClassroomPage() {
  const excalidrawApiRef = useRef<ExcalidrawAPI | null>(null);
  const stageRef = useRef<HTMLDivElement | null>(null);
  const [ready, setReady] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [dark, setDark] = useState(false);

  const avatar = useSimliAvatar();
  const session = useTeacherSession(excalidrawApiRef, avatar, stageRef);
  const brand = displayName(session.publicConfig);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    document.title = studioTitle(brand);
  }, [brand]);

  useEffect(() => {
    if (session.isTeaching) setSidebarOpen(false);
  }, [session.isTeaching]);

  const current = session.lesson?.segments[session.activeSegment];

  return (
    <div className={`classroom ${session.isTeaching ? "presenting" : ""}`}>
      <header className="classroom-top">
        <div className="classroom-brand">
          <button className="icon-btn" onClick={() => setSidebarOpen((v) => !v)} aria-label="Toggle panel">
            ☰
          </button>
          {brand ? <span className="brand-mark">{brand}</span> : null}
          <span className="brand-chip">training</span>
        </div>
        <p className="classroom-kicker">Talking avatar + demo slides. You write the lines. They are spoken verbatim.</p>
        <button className="icon-btn" onClick={() => setDark((v) => !v)} aria-label="Toggle theme">
          {dark ? <Sun size={16} /> : <Moon size={16} />}
        </button>
      </header>

      <div className="classroom-body training">
        <aside className={`ask-panel ${sidebarOpen ? "open" : "closed"}`}>
          <h1>Your script</h1>
          <p className="ask-copy">
            Paste the spoken lines. Present waits until a proper slide exists for each line, then plays the talk on those slides.
          </p>
          <textarea
            value={session.query}
            onChange={(e) => session.setQuery(e.target.value)}
            placeholder={"An MCB is a miniature circuit breaker.\nIt protects wiring from overload.\nWhen current is too high, it trips."}
            disabled={session.isTeaching}
            rows={10}
          />
          {session.publicConfig?.demoScript && (
            <button
              className="ghost-btn"
              disabled={session.isTeaching}
              onClick={() => {
                session.setQuery(session.publicConfig!.demoScript);
                void session.teach(session.publicConfig!.demoScript);
              }}
            >
              Load demo script
            </button>
          )}
          <div className="ask-actions">
            <button
              className="primary-btn"
              onClick={() => void session.teach()}
              disabled={session.isTeaching || !session.query.trim()}
            >
              {session.isPlanning ? "Building slides..." : session.isTeaching ? "Presenting..." : "Present"}
            </button>
            <button className={`mic-btn ${session.isRecording ? "live" : ""}`} onClick={() => void session.toggleMic()}>
              <Mic size={16} />
              {session.isRecording ? "Stop" : "Speak"}
            </button>
            {session.isTeaching && (
              <button className="stop-btn" onClick={session.stop}>
                <Square size={12} /> Stop
              </button>
            )}
          </div>
          <p className="status-line">{session.status}</p>
          {session.provider && (
            <p className="meta-line">
              LLM · {session.provider}
              {session.provider === "local" ? " — add GROQ_API_KEY in .env for richer slides" : " — slides from each line"}
            </p>
          )}
          {session.lesson && (
            <ol className="beats">
              {session.lesson.segments.map((segment, index) => (
                <li key={segment.id} className={index === session.activeSegment ? "active" : ""}>
                  {segment.title}
                </li>
              ))}
            </ol>
          )}
        </aside>

        <main className="stage">
          <div className="stage-frame" ref={stageRef}>
            {session.isTeaching && !session.isPlanning ? (
              <span className="session-rec" aria-hidden="true">
                REC
              </span>
            ) : null}
            {session.showThanks && session.lesson ? (
              <ThankYouStage
                lesson={session.lesson}
                brand={brand}
                sessionVideo={session.sessionVideo}
                onClose={session.dismissThanks}
              />
            ) : (
              <LessonSlide
                segment={session.isPlanning ? undefined : current}
                lessonTitle={session.lesson?.title || brand || "Training"}
                index={session.activeSegment}
                total={session.lesson?.segments.length || 0}
                caption={session.spokenText}
                presenting={session.isTeaching && !session.isPlanning}
                speaking={avatar.speaking}
              />
            )}
            <AvatarStage
              enabled={Boolean(session.publicConfig?.avatarEnabled)}
              connected={avatar.connected}
              speaking={avatar.speaking}
              status={avatar.status}
              videoRef={avatar.videoRef}
              audioRef={avatar.audioRef}
            />
            {brand ? <span className="stage-brand">{brand}</span> : null}
            {(session.isPlanning || !ready) && (
              <div className={`board-status ${session.isPlanning ? "building" : ""}`}>
                {session.isPlanning ? "Building slides..." : "Loading studio..."}
              </div>
            )}
          </div>
        </main>

        <div className="board-hidden" aria-hidden="true" inert>
          <Excalidraw
            theme="light"
            excalidrawAPI={(api) => {
              excalidrawApiRef.current = api as ExcalidrawAPI;
              setReady(true);
            }}
          />
        </div>
      </div>
    </div>
  );
}
