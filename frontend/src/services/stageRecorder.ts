export type SessionVideo = {
  blob: Blob;
  filename: string;
  mime: string;
};

type StartOptions = {
  stage: HTMLElement;
  video?: HTMLVideoElement | null;
  title?: string;
};

type PlayOpts = {
  hear?: boolean;
};

function pickMime(): string {
  const types = [
    "video/webm;codecs=vp9,opus",
    "video/webm;codecs=vp8,opus",
    "video/webm",
    "video/mp4",
  ];
  return types.find((type) => typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(type)) || "";
}

function extensionFor(mime: string): string {
  return mime.includes("mp4") ? "mp4" : "webm";
}

function slugify(text: string): string {
  const slug = text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  return slug.slice(0, 48) || "session";
}

function readText(root: ParentNode, selector: string): string {
  return (root.querySelector(selector)?.textContent || "").replace(/\s+/g, " ").trim();
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  const radius = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.arcTo(x + w, y, x + w, y + h, radius);
  ctx.arcTo(x + w, y + h, x, y + h, radius);
  ctx.arcTo(x, y + h, x, y, radius);
  ctx.arcTo(x, y, x + w, y, radius);
  ctx.closePath();
}

function wrapText(
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  maxWidth: number,
  lineHeight: number,
  maxLines = 4,
) {
  const words = text.split(" ").filter(Boolean);
  let line = "";
  let row = 0;
  for (const word of words) {
    const next = line ? `${line} ${word}` : word;
    if (ctx.measureText(next).width > maxWidth && line) {
      ctx.fillText(line, x, y + row * lineHeight);
      line = word;
      row += 1;
      if (row >= maxLines) return;
    } else {
      line = next;
    }
  }
  if (line && row < maxLines) ctx.fillText(line, x, y + row * lineHeight);
}

function drawVideoCover(
  ctx: CanvasRenderingContext2D,
  video: HTMLVideoElement,
  dx: number,
  dy: number,
  dw: number,
  dh: number,
) {
  const vw = video.videoWidth || dw;
  const vh = video.videoHeight || dh;
  const scale = Math.max(dw / vw, dh / vh);
  const sw = dw / scale;
  const sh = dh / scale;
  const sx = (vw - sw) / 2;
  const sy = (vh - sh) / 2;
  ctx.drawImage(video, sx, sy, sw, sh, dx, dy, dw, dh);
}

export class StageRecorder {
  private ctx: AudioContext | null = null;
  private dest: MediaStreamAudioDestinationNode | null = null;
  private silent: OscillatorNode | null = null;
  private canvas: HTMLCanvasElement | null = null;
  private canvasStream: MediaStream | null = null;
  private draw: CanvasRenderingContext2D | null = null;
  private recorder: MediaRecorder | null = null;
  private chunks: Blob[] = [];
  private raf = 0;
  private running = false;
  private stage: HTMLElement | null = null;
  private video: HTMLVideoElement | null = null;
  private mime = "";
  private title = "session";
  private voices: AudioBufferSourceNode[] = [];

  prepare() {
    if (this.ctx) {
      void this.ctx.resume();
      return;
    }
    const ctx = new AudioContext();
    this.ctx = ctx;
    this.dest = ctx.createMediaStreamDestination();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    gain.gain.value = 0.0001;
    osc.connect(gain);
    gain.connect(this.dest);
    osc.start();
    this.silent = osc;
    void ctx.resume();
  }

  get active() {
    return this.running;
  }

  async start(options: StartOptions) {
    this.prepare();
    if (!this.ctx || !this.dest) return false;
    const stage = options.stage;
    const rect = stage.getBoundingClientRect();
    const cssW = Math.max(640, Math.round(rect.width) || 1280);
    const cssH = Math.max(360, Math.round(rect.height) || 720);
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(cssW * dpr);
    canvas.height = Math.round(cssH * dpr);
    const draw = canvas.getContext("2d");
    if (!draw) return false;

    this.canvas = canvas;
    this.draw = draw;
    this.stage = stage;
    this.video = options.video || null;
    this.title = options.title || "session";
    this.chunks = [];
    this.running = true;
    if (this.video) this.video.muted = true;

    const stream = canvas.captureStream(30);
    this.canvasStream = stream;
    const mixed = new MediaStream([...stream.getVideoTracks(), ...this.dest.stream.getAudioTracks()]);
    this.mime = pickMime();
    const recorder = this.mime
      ? new MediaRecorder(mixed, { mimeType: this.mime, videoBitsPerSecond: 3_200_000 })
      : new MediaRecorder(mixed);
    this.mime = recorder.mimeType || this.mime || "video/webm";
    recorder.ondataavailable = (event) => {
      if (event.data.size) this.chunks.push(event.data);
    };
    this.recorder = recorder;
    recorder.start(400);
    const tick = () => {
      if (!this.running) return;
      this.paint();
      this.raf = requestAnimationFrame(tick);
    };
    this.raf = requestAnimationFrame(tick);
    return true;
  }

  playPcm(pcm: Uint8Array, sampleRate = 16000, opts: PlayOpts = {}) {
    if (!this.ctx || !this.dest || !pcm.byteLength) return;
    const samples = new Int16Array(pcm.buffer, pcm.byteOffset, Math.floor(pcm.byteLength / 2));
    const floats = new Float32Array(samples.length);
    for (let i = 0; i < samples.length; i += 1) {
      floats[i] = samples[i] < 0 ? samples[i] / 0x8000 : samples[i] / 0x7fff;
    }
    const buffer = this.ctx.createBuffer(1, floats.length, sampleRate);
    buffer.copyToChannel(floats, 0);
    this.startBuffer(buffer, opts.hear === true);
  }

  async playUrl(url: string, opts: PlayOpts = {}) {
    if (!this.ctx || !this.dest || !url) return;
    const raw = await fetch(url).then((res) => res.arrayBuffer());
    const buffer = await this.ctx.decodeAudioData(raw.slice(0));
    this.startBuffer(buffer, opts.hear === true);
  }

  async stop(): Promise<SessionVideo | null> {
    this.running = false;
    if (this.raf) cancelAnimationFrame(this.raf);
    this.raf = 0;
    this.voices.forEach((node) => {
      try {
        node.stop();
      } catch {
        // already ended
      }
    });
    this.voices = [];
    const recorder = this.recorder;
    const mime = this.mime;
    const title = this.title;
    const blob = await new Promise<Blob | null>((resolve) => {
      if (!recorder || recorder.state === "inactive") {
        resolve(this.chunks.length ? new Blob(this.chunks, { type: mime }) : null);
        return;
      }
      recorder.onstop = () => {
        resolve(this.chunks.length ? new Blob(this.chunks, { type: mime }) : null);
      };
      try {
        recorder.requestData();
      } catch {
        // some browsers throw if no data yet
      }
      recorder.stop();
    });
    this.cleanup();
    if (!blob || blob.size < 16_000) return null;
    return {
      blob,
      mime,
      filename: `${slugify(title)}-session.${extensionFor(mime)}`,
    };
  }

  private startBuffer(buffer: AudioBuffer, hear: boolean) {
    if (!this.ctx || !this.dest) return;
    const src = this.ctx.createBufferSource();
    src.buffer = buffer;
    src.connect(this.dest);
    if (hear) src.connect(this.ctx.destination);
    src.start();
    this.voices.push(src);
    src.onended = () => {
      this.voices = this.voices.filter((node) => node !== src);
    };
  }

  private paint() {
    const ctx = this.draw;
    const canvas = this.canvas;
    const stage = this.stage;
    if (!ctx || !canvas || !stage) return;
    if (this.video) this.video.muted = true;
    this.paintSlide(ctx, canvas, stage);
    this.paintAvatar(ctx, canvas, stage);
  }

  private paintSlide(ctx: CanvasRenderingContext2D, canvas: HTMLCanvasElement, stage: HTMLElement) {
    const w = canvas.width;
    const h = canvas.height;
    const pad = Math.round(w * 0.045);
    ctx.fillStyle = "#fffcf8";
    ctx.fillRect(0, 0, w, h);
    const wash = ctx.createRadialGradient(w * 0.12, 0, 0, w * 0.12, 0, w * 0.55);
    wash.addColorStop(0, "rgba(232, 163, 106, 0.16)");
    wash.addColorStop(1, "rgba(232, 163, 106, 0)");
    ctx.fillStyle = wash;
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = "#e8a36a";
    ctx.fillRect(0, 0, w, Math.max(3, Math.round(h * 0.007)));

    const kicker = readText(stage, ".demo-kicker");
    const progress = readText(stage, ".demo-progress");
    const headline = readText(stage, ".demo-heading h2, .sop-heading h2, .thanks-stage h2");
    ctx.fillStyle = "#c48a12";
    ctx.font = `700 ${Math.round(h * 0.022)}px Inter, Segoe UI, sans-serif`;
    if (kicker) ctx.fillText(kicker.toUpperCase(), pad, pad + h * 0.035);
    if (progress) {
      ctx.fillStyle = "#9aa3ad";
      ctx.textAlign = "right";
      ctx.fillText(progress, w - pad - Math.round(w * 0.16), pad + h * 0.035);
      ctx.textAlign = "left";
    }

    ctx.fillStyle = "#2a3238";
    ctx.font = `600 ${Math.round(h * 0.052)}px Georgia, "Times New Roman", serif`;
    if (headline) wrapText(ctx, headline, pad, pad + h * 0.1, w * 0.62, h * 0.06, 3);

    const cards = Array.from(stage.querySelectorAll(".demo-cards li"));
    const steps = Array.from(stage.querySelectorAll(".demo-steps li"));
    const bullets = Array.from(stage.querySelectorAll(".demo-bullets li"));
    const tones = ["#fff7e8", "#eef8f1", "#eef6f5"];

    if (cards.length) {
      const top = h * 0.3;
      const cardH = h * 0.4;
      const gap = w * 0.015;
      const usable = w - pad * 2;
      const cw = (usable - gap * (cards.length - 1)) / cards.length;
      cards.forEach((card, index) => {
        const x = pad + index * (cw + gap);
        roundRect(ctx, x, top, cw, cardH, Math.min(28, cw * 0.08));
        ctx.fillStyle = tones[index % tones.length];
        ctx.fill();
        const label = readText(card, ".demo-card-index") || String(index + 1).padStart(2, "0");
        const body = readText(card, "p");
        ctx.fillStyle = "#9aa3ad";
        ctx.font = `700 ${Math.round(h * 0.018)}px Inter, Segoe UI, sans-serif`;
        ctx.fillText(label, x + cw * 0.08, top + h * 0.045);
        ctx.fillStyle = "#2a3238";
        ctx.font = `600 ${Math.round(h * 0.026)}px Inter, Segoe UI, sans-serif`;
        wrapText(ctx, body, x + cw * 0.08, top + h * 0.09, cw * 0.84, h * 0.038, 6);
      });
    } else if (steps.length) {
      steps.forEach((step, index) => {
        const y = h * 0.32 + index * (h * 0.14);
        roundRect(ctx, pad, y, w * 0.7, h * 0.12, 18);
        ctx.fillStyle = "rgba(255,255,255,0.9)";
        ctx.fill();
        ctx.fillStyle = "#e8a36a";
        ctx.font = `700 ${Math.round(h * 0.032)}px Georgia, serif`;
        ctx.fillText(readText(step, "span") || String(index + 1).padStart(2, "0"), pad + w * 0.02, y + h * 0.07);
        ctx.fillStyle = "#2a3238";
        ctx.font = `600 ${Math.round(h * 0.024)}px Inter, Segoe UI, sans-serif`;
        wrapText(ctx, readText(step, "p"), pad + w * 0.09, y + h * 0.05, w * 0.56, h * 0.032, 2);
      });
    } else if (bullets.length) {
      bullets.forEach((item, index) => {
        const y = h * 0.32 + index * (h * 0.12);
        roundRect(ctx, pad, y, w * 0.62, h * 0.1, 16);
        ctx.fillStyle = "rgba(255,255,255,0.9)";
        ctx.fill();
        ctx.fillStyle = "#e8a36a";
        ctx.beginPath();
        ctx.arc(pad + w * 0.025, y + h * 0.05, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#2a3238";
        ctx.font = `600 ${Math.round(h * 0.024)}px Inter, Segoe UI, sans-serif`;
        wrapText(ctx, (item.textContent || "").replace(/\s+/g, " ").trim(), pad + w * 0.05, y + h * 0.04, w * 0.54, h * 0.032, 2);
      });
    }

    const caption = readText(stage, ".sop-caption span");
    if (caption) {
      const capW = w - pad * 2 - w * 0.08;
      const capH = h * 0.1;
      const capY = h - pad - capH;
      roundRect(ctx, pad, capY, capW, capH, 8);
      ctx.fillStyle = "rgba(18, 18, 18, 0.9)";
      ctx.fill();
      ctx.fillStyle = "#ffffff";
      ctx.font = `500 ${Math.round(h * 0.024)}px Inter, Segoe UI, sans-serif`;
      wrapText(ctx, caption, pad + w * 0.02, capY + h * 0.04, capW - w * 0.04, h * 0.03, 2);
    }

    const brand = readText(stage, ".stage-brand");
    if (brand) {
      ctx.fillStyle = "#d0b39a";
      ctx.font = `700 ${Math.round(h * 0.018)}px Inter, Segoe UI, sans-serif`;
      ctx.textAlign = "right";
      ctx.fillText(brand.toUpperCase(), w - pad, h - pad * 0.45);
      ctx.textAlign = "left";
    }
  }

  private paintAvatar(ctx: CanvasRenderingContext2D, canvas: HTMLCanvasElement, stage: HTMLElement) {
    const video = this.video;
    const pip = stage.querySelector(".avatar-pip") as HTMLElement | null;
    const stageBox = stage.getBoundingClientRect();
    const scaleX = canvas.width / Math.max(stageBox.width, 1);
    const scaleY = canvas.height / Math.max(stageBox.height, 1);
    let x: number;
    let y: number;
    let size: number;
    if (pip) {
      const box = pip.getBoundingClientRect();
      x = (box.left - stageBox.left) * scaleX;
      y = (box.top - stageBox.top) * scaleY;
      size = Math.min(box.width * scaleX, box.height * scaleY);
    } else {
      size = 168 * scaleX;
      x = canvas.width - 18 * scaleX - size;
      y = 18 * scaleY;
    }
    if (size < 8) return;
    const cx = x + size / 2;
    const cy = y + size / 2;
    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, size / 2, 0, Math.PI * 2);
    ctx.closePath();
    ctx.clip();
    if (video && video.readyState >= 2 && video.videoWidth) {
      drawVideoCover(ctx, video, x, y, size, size);
    } else {
      const fill = ctx.createRadialGradient(cx - size * 0.1, cy - size * 0.15, size * 0.1, cx, cy, size * 0.7);
      fill.addColorStop(0, "#f7f1e8");
      fill.addColorStop(1, "#d3c4b4");
      ctx.fillStyle = fill;
      ctx.fill();
    }
    ctx.restore();
    ctx.beginPath();
    ctx.arc(cx, cy, size / 2, 0, Math.PI * 2);
    ctx.lineWidth = Math.max(4, size * 0.04);
    ctx.strokeStyle = "#ffffff";
    ctx.stroke();
  }

  private cleanup() {
    this.canvasStream?.getTracks().forEach((track) => track.stop());
    this.canvasStream = null;
    this.recorder = null;
    this.canvas = null;
    this.draw = null;
    this.stage = null;
    this.video = null;
    this.chunks = [];
    try {
      this.silent?.stop();
    } catch {
      // ignore
    }
    this.silent = null;
  }
}
