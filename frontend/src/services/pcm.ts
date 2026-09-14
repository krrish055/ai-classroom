const TARGET_RATE = 16000;

function mixToMono(buffer: AudioBuffer): Float32Array {
  const first = buffer.getChannelData(0);
  if (buffer.numberOfChannels === 1) return new Float32Array(first);
  const mixed = new Float32Array(buffer.length);
  for (let channel = 0; channel < buffer.numberOfChannels; channel += 1) {
    const data = buffer.getChannelData(channel);
    for (let i = 0; i < data.length; i += 1) {
      mixed[i] += data[i] / buffer.numberOfChannels;
    }
  }
  return mixed;
}

function resampleLinear(input: Float32Array, fromRate: number, toRate: number): Float32Array {
  if (fromRate === toRate) return input;
  const ratio = fromRate / toRate;
  const length = Math.max(1, Math.round(input.length / ratio));
  const output = new Float32Array(length);
  for (let i = 0; i < length; i += 1) {
    const src = i * ratio;
    const left = Math.floor(src);
    const right = Math.min(left + 1, input.length - 1);
    const t = src - left;
    output[i] = input[left] * (1 - t) + input[right] * t;
  }
  return output;
}

function floatToPcm16(input: Float32Array): Uint8Array {
  const pcm = new Int16Array(input.length);
  for (let i = 0; i < input.length; i += 1) {
    const sample = Math.max(-1, Math.min(1, input[i]));
    pcm[i] = sample < 0 ? Math.round(sample * 0x8000) : Math.round(sample * 0x7fff);
  }
  return new Uint8Array(pcm.buffer);
}

export async function audioBlobToPcm16k(blob: Blob): Promise<{ pcm: Uint8Array; durationMs: number }> {
  const context = new AudioContext();
  try {
    const decoded = await context.decodeAudioData((await blob.arrayBuffer()).slice(0));
    const mono = mixToMono(decoded);
    const resampled = resampleLinear(mono, decoded.sampleRate, TARGET_RATE);
    return {
      pcm: floatToPcm16(resampled),
      durationMs: Math.round((resampled.length / TARGET_RATE) * 1000),
    };
  } finally {
    await context.close();
  }
}
