// MediaRecorder only produces webm/ogg containers in every mainstream
// browser (there's no "audio/wav" recording mimeType to ask for), but the
// backend's voice_input node hard-codes a .wav filename hint for the
// Whisper API (see backend/app/agents/nodes/voice_input.py) — sending it
// raw webm/opus bytes under a .wav name would make transcription fail.
// Re-encoding to real WAV here, entirely client-side via the Web Audio API,
// avoids needing any backend change to match formats.
export async function blobToWavBlob(blob) {
  const arrayBuffer = await blob.arrayBuffer();
  const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
  const audioCtx = new AudioContextCtor();
  try {
    const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
    return new Blob([encodeWav(audioBuffer)], { type: "audio/wav" });
  } finally {
    audioCtx.close();
  }
}

function encodeWav(audioBuffer) {
  const numChannels = audioBuffer.numberOfChannels;
  const sampleRate = audioBuffer.sampleRate;
  const bitDepth = 16;

  const interleaved =
    numChannels === 2
      ? interleaveStereo(audioBuffer.getChannelData(0), audioBuffer.getChannelData(1))
      : audioBuffer.getChannelData(0);

  const bytesPerSample = bitDepth / 8;
  const dataLength = interleaved.length * bytesPerSample;
  const buffer = new ArrayBuffer(44 + dataLength);
  const view = new DataView(buffer);

  writeAscii(view, 0, "RIFF");
  view.setUint32(4, 36 + dataLength, true);
  writeAscii(view, 8, "WAVE");
  writeAscii(view, 12, "fmt ");
  view.setUint32(16, 16, true); // fmt chunk size
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * numChannels * bytesPerSample, true); // byte rate
  view.setUint16(32, numChannels * bytesPerSample, true); // block align
  view.setUint16(34, bitDepth, true);
  writeAscii(view, 36, "data");
  view.setUint32(40, dataLength, true);

  floatTo16BitPCM(view, 44, interleaved);

  return buffer;
}

function interleaveStereo(left, right) {
  const result = new Float32Array(left.length + right.length);
  let index = 0;
  for (let i = 0; i < left.length; i++) {
    result[index++] = left[i];
    result[index++] = right[i];
  }
  return result;
}

function writeAscii(view, offset, text) {
  for (let i = 0; i < text.length; i++) {
    view.setUint8(offset + i, text.charCodeAt(i));
  }
}

function floatTo16BitPCM(view, offset, input) {
  for (let i = 0; i < input.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, input[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
}
