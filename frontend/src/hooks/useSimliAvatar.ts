import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { LogLevel, SimliClient } from "simli-client";
import { createAvatarSession } from "../services/api";
import { audioBlobToPcm16k } from "../services/pcm";

export type SpeechPlayback = {
  stop: () => void;
  done: Promise<void>;
  getProgress: () => number;
};

const CHUNK = 6000;

export function useSimliAvatar() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const clientRef = useRef<SimliClient | null>(null);
  const startingRef = useRef<Promise<boolean> | null>(null);
  const [connected, setConnected] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [status, setStatus] = useState("Avatar idle");

  const disconnect = useCallback(async () => {
    const client = clientRef.current;
    clientRef.current = null;
    startingRef.current = null;
    setConnected(false);
    setSpeaking(false);
    if (client) {
      try {
        client.ClearBuffer();
        await client.stop();
      } catch {
        // already closed
      }
    }
  }, []);

  const ensureStarted = useCallback(async () => {
    if (clientRef.current) return true;
    if (startingRef.current) return startingRef.current;

    startingRef.current = (async () => {
      const video = videoRef.current;
      const audio = audioRef.current;
      if (!video || !audio) {
        setStatus("Avatar video is still mounting.");
        return false;
      }
      setStatus("Connecting Simli face...");
      const session = await createAvatarSession();
      const client = new SimliClient(
        session.session_token,
        video,
        audio,
        null,
        LogLevel.ERROR,
        "livekit",
      );
      client.on("speaking", () => {
        setSpeaking(true);
        setStatus("Presenter is speaking");
      });
      client.on("silent", () => {
        setSpeaking(false);
        setStatus("Avatar ready");
      });
      client.on("startup_error", (message) => {
        setStatus(message || "Simli could not start");
      });
      client.on("error", (message) => {
        setStatus(message || "Simli connection error");
      });
      await client.start();
      clientRef.current = client;
      setConnected(true);
      setStatus("Avatar ready");
      return true;
    })().catch(async (error) => {
      await disconnect();
      setStatus(error instanceof Error ? error.message : "Could not start Simli avatar");
      return false;
    }).finally(() => {
      startingRef.current = null;
    });

    return startingRef.current;
  }, [disconnect]);

  const speakPcm = useCallback(async (pcm: Uint8Array, durationMs: number): Promise<SpeechPlayback> => {
    const started = await ensureStarted();
    const client = clientRef.current;
    if (!started || !client) {
      throw new Error("Avatar is not connected");
    }

    let finished = false;
    let startedAt = Date.now();
    let resolveDone: () => void = () => undefined;
    const done = new Promise<void>((resolve) => {
      resolveDone = resolve;
    });

    const finish = () => {
      if (finished) return;
      finished = true;
      setSpeaking(false);
      try {
        client.off("speaking", onSpeaking);
        client.off("silent", onSilent);
      } catch {
        // client already tore down
      }
      resolveDone();
    };

    const onSpeaking = () => {
      startedAt = Date.now();
      setSpeaking(true);
    };
    const onSilent = () => {
      if (Date.now() - startedAt < durationMs * 0.98) return;
      finish();
    };

    client.on("speaking", onSpeaking);
    client.on("silent", onSilent);

    for (let offset = 0; offset < pcm.byteLength; offset += CHUNK) {
      client.sendAudioData(pcm.slice(offset, offset + CHUNK));
    }

    const timer = window.setTimeout(finish, Math.max(durationMs + 180, 400));

    return {
      stop: () => {
        try {
          client.ClearBuffer();
        } catch {
          // ignore
        }
        window.clearTimeout(timer);
        finish();
      },
      done: done.finally(() => window.clearTimeout(timer)),
      getProgress: () => Math.max(0, Math.min(1, (Date.now() - startedAt) / Math.max(durationMs, 1))),
    };
  }, [ensureStarted]);

  const speakBlob = useCallback(async (blob: Blob): Promise<SpeechPlayback> => {
    const { pcm, durationMs } = await audioBlobToPcm16k(blob);
    return speakPcm(pcm, durationMs);
  }, [speakPcm]);

  const stopSpeech = useCallback(() => {
    try {
      clientRef.current?.ClearBuffer();
    } catch {
      // ignore
    }
    setSpeaking(false);
  }, []);

  useEffect(() => () => {
    void disconnect();
  }, [disconnect]);

  return useMemo(
    () => ({
      videoRef,
      audioRef,
      connected,
      speaking,
      status,
      ensureStarted,
      speakBlob,
      speakPcm,
      stopSpeech,
      disconnect,
    }),
    [connected, disconnect, ensureStarted, speakBlob, speakPcm, speaking, status, stopSpeech],
  );
}
