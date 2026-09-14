import { useCallback, useEffect, useRef, useState, type RefObject } from "react";
import { createLesson, getPublicConfig, streamLesson, synthesizeSpeech, transcribeAudio } from "../services/api";
import { audioBlobToPcm16k } from "../services/pcm";
import { drawBoard, frameClassroom, type ExcalidrawAPI } from "../services/boardRenderer";
import { StageRecorder, type SessionVideo } from "../services/stageRecorder";
import type { Lesson, LessonSegment, PublicConfig } from "../types/lesson";
import type { SpeechPlayback } from "./useSimliAvatar";

type PreparedSpeech = {
  blob?: Blob;
  audioUrl?: string;
  speechRate?: number;
  pcm?: Uint8Array;
  durationMs?: number;
};

function previewLines(script: string) {
  return String(script || "")
    .split(/\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function playAudio(url: string) {
  const audio = new Audio(url);
  let released = false;
  const release = () => {
    if (released) return;
    released = true;
    audio.pause();
    audio.currentTime = 0;
    URL.revokeObjectURL(url);
  };
  const done = new Promise<void>((resolve, reject) => {
    audio.onended = () => resolve();
    audio.onerror = () => reject(new Error("Audio playback failed"));
  }).finally(release);
  void audio.play();
  return {
    stop: release,
    done,
    getProgress: () => (audio.duration ? audio.currentTime / audio.duration : 0),
  };
}

function speakWithBrowser(text: string, rate: number) {
  return new Promise<{ stop: () => void; done: Promise<void>; getProgress: () => number }>((resolve, reject) => {
    const synth = window.speechSynthesis;
    if (!synth) {
      reject(new Error("Browser TTS is not available"));
      return;
    }
    synth.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = rate || 1;
    let charIndex = 0;
    utter.onboundary = (event) => {
      if (typeof event.charIndex === "number") charIndex = event.charIndex;
    };
    const done = new Promise<void>((doneResolve, doneReject) => {
      utter.onend = () => doneResolve();
      utter.onerror = () => doneReject(new Error("Speech failed"));
    });
    synth.speak(utter);
    resolve({
      stop: () => synth.cancel(),
      done,
      getProgress: () => (text.length ? charIndex / text.length : 1),
    });
  });
}

type AvatarDriver = {
  ensureStarted: () => Promise<boolean>;
  speakBlob: (blob: Blob) => Promise<SpeechPlayback>;
  speakPcm?: (pcm: Uint8Array, durationMs: number) => Promise<SpeechPlayback>;
  stopSpeech: () => void;
  videoRef?: RefObject<HTMLVideoElement | null>;
  audioRef?: RefObject<HTMLAudioElement | null>;
};

function waitForPaint() {
  return new Promise<void>((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
  });
}

function waitMs(ms: number): SpeechPlayback {
  let timer = 0;
  let settled = false;
  let resolveDone: () => void = () => undefined;
  const done = new Promise<void>((resolve) => {
    resolveDone = resolve;
  });
  const finish = () => {
    if (settled) return;
    settled = true;
    window.clearTimeout(timer);
    resolveDone();
  };
  timer = window.setTimeout(finish, Math.max(ms, 400));
  return {
    stop: finish,
    done,
    getProgress: () => 1,
  };
}

export function useTeacherSession(
  excalidrawApiRef: React.RefObject<ExcalidrawAPI | null>,
  avatar?: AvatarDriver,
  stageRef?: RefObject<HTMLElement | null>,
) {
  const [publicConfig, setPublicConfig] = useState<PublicConfig | null>(null);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("Paste the script. Every word is spoken. Notes come from the meaning.");
  const [isPlanning, setIsPlanning] = useState(false);
  const [isTeaching, setIsTeaching] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [activeSegment, setActiveSegment] = useState(0);
  const [spokenText, setSpokenText] = useState("");
  const [provider, setProvider] = useState("");
  const [showThanks, setShowThanks] = useState(false);
  const [sessionVideo, setSessionVideo] = useState<SessionVideo | null>(null);
  const abortRef = useRef(false);
  const streamAbortRef = useRef<AbortController | null>(null);
  const lessonRef = useRef<Lesson | null>(null);
  const stopSpeechRef = useRef<(() => void) | null>(null);
  const recorderRef = useRef<StageRecorder | null>(null);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const ensureStarted = avatar?.ensureStarted;
  const speakBlob = avatar?.speakBlob;
  const speakPcm = avatar?.speakPcm;
  const stopSpeech = avatar?.stopSpeech;

  useEffect(() => {
    let cancelled = false;
    getPublicConfig()
      .then((cfg) => {
        if (cancelled) return;
        setPublicConfig(cfg);
        if (cfg?.demoScript) setQuery((prev) => prev || cfg.demoScript);
        if (cfg?.avatarEnabled) void ensureStarted?.();
      })
      .catch((err: Error) => {
        if (!cancelled) setStatus(err.message || "Failed to load teacher config");
      });
    return () => {
      cancelled = true;
    };
  }, [ensureStarted]);

  useEffect(() => {
    return () => {
      mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
      const recorder = mediaRef.current;
      if (recorder && recorder.state !== "inactive") {
        recorder.stop();
      }
      stopSpeechRef.current?.();
    };
  }, []);

  const stop = useCallback(() => {
    abortRef.current = true;
    streamAbortRef.current?.abort();
    stopSpeechRef.current?.();
    stopSpeech?.();
    setIsTeaching(false);
    setStatus("Lesson paused.");
  }, [stopSpeech]);

  const teach = useCallback(async (rawQuery?: string) => {
    const topic = String(rawQuery ?? query).trim();
    if (!topic) {
      setStatus("Paste a script first.");
      return;
    }
    const api = excalidrawApiRef.current;

    abortRef.current = false;
    stopSpeechRef.current?.();
    setIsPlanning(true);
    setIsTeaching(true);
    setShowThanks(false);
    setSessionVideo(null);
    setStatus("Preparing the talk...");
    setSpokenText("");
    setActiveSegment(0);

    const recorder = new StageRecorder();
    recorderRef.current = recorder;
    recorder.prepare();

    const prepared = new Map<string, Promise<PreparedSpeech>>();
    const queueSpeech = (text: string) => {
      if (!prepared.has(text)) {
        prepared.set(
          text,
          (async () => {
            const tts = await synthesizeSpeech(text);
            let pcm: Uint8Array | undefined;
            let durationMs: number | undefined;
            if (tts.blob) {
              try {
                const decoded = await audioBlobToPcm16k(tts.blob);
                pcm = decoded.pcm;
                durationMs = decoded.durationMs;
              } catch {
                // play the mp3 directly if PCM decode fails
              }
            }
            return {
              blob: tts.blob,
              audioUrl: tts.audioUrl,
              speechRate: typeof tts.speechRate === "number" ? tts.speechRate : undefined,
              pcm,
              durationMs,
            };
          })(),
        );
      }
      return prepared.get(text)!;
    };

    for (const line of previewLines(topic)) queueSpeech(line);
    void ensureStarted?.();

    const streamAbort = new AbortController();
    streamAbortRef.current = streamAbort;
    lessonRef.current = null;

    let settleDeck: (lesson: Lesson) => void = () => undefined;
    let failDeck: (error: Error) => void = () => undefined;
    const deckReady = new Promise<Lesson>((resolve, reject) => {
      settleDeck = resolve;
      failDeck = reject;
    });
    let deckSettled = false;
    const finishDeck = () => {
      const current = lessonRef.current;
      if (deckSettled) return;
      deckSettled = true;
      if (!current) {
        failDeck(new Error("Could not build slides"));
        return;
      }
      setLesson(current);
      settleDeck(current);
    };
    const acceptLesson = (next: Lesson) => {
      lessonRef.current = next;
    };

    const streamWork = (async () => {
      try {
        await streamLesson(
          topic,
          (event) => {
            if (event.event === "error") {
              throw new Error(event.error || "Could not prepare this lesson");
            }
            if ((event.event === "meta" || event.event === "lesson") && event.lesson) {
              if (event.provider) setProvider(event.provider);
              acceptLesson(event.lesson as Lesson);
            }
            if (event.event === "segment" && typeof event.index === "number" && event.segment) {
              const current = lessonRef.current;
              if (!current) return;
              const segments = current.segments.slice();
              segments[event.index] = event.segment as LessonSegment;
              acceptLesson({ ...current, segments });
            }
            if (event.event === "done") finishDeck();
          },
          streamAbort.signal,
        );
        finishDeck();
      } catch {
        if (streamAbort.signal.aborted || abortRef.current) {
          failDeck(new Error("Stopped"));
          return;
        }
        try {
          const result = await createLesson(topic);
          setProvider(result.provider);
          acceptLesson(result.lesson);
          finishDeck();
        } catch (fallbackError) {
          failDeck(fallbackError instanceof Error ? fallbackError : new Error("Could not build slides"));
        }
      }
    })();

    try {
      setStatus("Building slides for each spoken line...");
      const nextLesson = await deckReady;
      setIsPlanning(false);
      setStatus(`Speaking your script · ${nextLesson.title}`);
      await waitForPaint();
      const stage = stageRef?.current;
      if (stage) {
        await recorder.start({
          stage,
          video: avatar?.videoRef?.current,
          title: nextLesson.title,
        });
      }
      for (const segment of nextLesson.segments) queueSpeech(segment.speech);

      for (let i = 0; i < nextLesson.segments.length; i += 1) {
        if (abortRef.current) break;
        const segment = (lessonRef.current ?? nextLesson).segments[i];
        setActiveSegment(i);
        setSpokenText(segment.speech);
        const elements = segment.board.elements || [];
        if (api) {
          drawBoard(api, elements, i === 0 || segment.board.mode === "replace");
          frameClassroom(api);
        }

        const ready = await queueSpeech(segment.speech);
        if (recorder.active) {
          const hear = !publicConfig?.avatarEnabled;
          if (ready.pcm) recorder.playPcm(ready.pcm, 16000, { hear });
          else if (ready.audioUrl) void recorder.playUrl(ready.audioUrl, { hear });
        }
        let playback: SpeechPlayback;
        try {
          if (publicConfig?.avatarEnabled && ready.pcm && ready.durationMs != null && speakPcm) {
            playback = await speakPcm(ready.pcm, ready.durationMs);
          } else if (publicConfig?.avatarEnabled && ready.blob && speakBlob) {
            playback = await speakBlob(ready.blob);
          } else if (recorder.active && ready.durationMs) {
            playback = waitMs(ready.durationMs);
          } else if (ready.audioUrl) {
            playback = playAudio(ready.audioUrl);
          } else {
            playback = await speakWithBrowser(segment.speech, ready.speechRate || publicConfig?.speechRate || 1);
          }
        } catch {
          playback = recorder.active && ready.durationMs
            ? waitMs(ready.durationMs)
            : ready.audioUrl
              ? playAudio(ready.audioUrl)
              : await speakWithBrowser(segment.speech, ready.speechRate || publicConfig?.speechRate || 1);
        }
        stopSpeechRef.current = playback.stop;
        await playback.done.catch(() => undefined);
      }

      await streamWork.catch(() => undefined);

      if (!abortRef.current) {
        setStatus("Done. Download the session video or the deck.");
      }
    } catch (error) {
      if (!abortRef.current) {
        setStatus(error instanceof Error ? error.message : "Failed to present this script.");
      }
    } finally {
      const recorded = await recorder.stop().catch(() => null);
      recorderRef.current = null;
      if (recorded) setSessionVideo(recorded);
      streamAbortRef.current = null;
      setIsPlanning(false);
      setIsTeaching(false);
      stopSpeechRef.current = null;
      if (lessonRef.current && (!abortRef.current || recorded)) {
        setShowThanks(true);
        if (recorded && abortRef.current) {
          setStatus("Stopped. You can still download the recorded session.");
        }
      }
    }
  }, [avatar, excalidrawApiRef, ensureStarted, publicConfig, query, speakBlob, speakPcm, stageRef]);

  const toggleMic = useCallback(async () => {
    if (isRecording) {
      mediaRef.current?.stop();
      setIsRecording(false);
      return;
    }

    try {
      if ((publicConfig?.sttProvider || "browser") === "browser") {
        const SpeechRecognition =
          (window as unknown as { SpeechRecognition?: new () => any; webkitSpeechRecognition?: new () => any })
            .SpeechRecognition ||
          (window as unknown as { webkitSpeechRecognition?: new () => any }).webkitSpeechRecognition;
        if (!SpeechRecognition) throw new Error("Browser speech recognition is not available");
        setIsRecording(true);
        setStatus("Listening...");
        const text = await new Promise<string>((resolve, reject) => {
          const recognition = new SpeechRecognition();
          recognition.lang = publicConfig?.sttLanguage || "en-US";
          recognition.interimResults = false;
          recognition.onresult = (event: any) => resolve(event.results?.[0]?.[0]?.transcript || "");
          recognition.onerror = (event: any) => reject(new Error(event.error || "STT failed"));
          recognition.start();
        });
        setQuery(text);
        setIsRecording(false);
        setStatus("Topic captured from voice.");
        return;
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size) chunksRef.current.push(event.data);
      };
      recorder.onstop = async () => {
        mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
        mediaStreamRef.current = null;
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        try {
          const result = await transcribeAudio(blob);
          if (result.text) setQuery(result.text);
          setStatus("Topic captured from voice.");
        } catch (error) {
          setStatus(error instanceof Error ? error.message : "Could not transcribe audio.");
        }
        setIsRecording(false);
      };
      mediaRef.current = recorder;
      recorder.start();
      setIsRecording(true);
      setStatus("Recording... click mic again to send.");
    } catch (error) {
      setIsRecording(false);
      setStatus(error instanceof Error ? error.message : "Microphone is unavailable.");
    }
  }, [isRecording, publicConfig]);

  return {
    publicConfig,
    query,
    setQuery,
    status,
    isPlanning,
    isTeaching,
    isRecording,
    lesson,
    activeSegment,
    spokenText,
    provider,
    showThanks,
    sessionVideo,
    dismissThanks: () => setShowThanks(false),
    teach,
    stop,
    toggleMic,
  };
}
