"""Voice I/O: OpenAI Whisper speech-to-text and a locally-loaded MMS-TTS
Bengali model for text-to-speech.

Stays pure like tools/crop_health.py and tools/weather.py — no trace_log or
State knowledge here, that's built by the calling node (see
nodes/voice_input.py and nodes/voice_output.py). The TTS model load mirrors
agents/checkpointer.py's module-level-singleton-plus-init-function pattern:
VitsModel's weights are too large to reload on every request, so
init_tts_model() is called once from app.main's lifespan instead.

Voice is currently stalled (the mic button is disabled client-side — see
ChatInput.jsx), so torch/transformers/scipy/numpy are NOT in requirements.txt
right now. Their imports are deliberately kept local to init_tts_model() and
synthesize_speech() rather than at module level, so this module — and
anything that imports from it (nodes/voice_input.py, nodes/voice_output.py,
which the conversation graph always loads) — stays importable without those
packages installed. Re-add them to requirements.txt before calling either
function again.
"""
from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from openai import OpenAI

from app.core.config import settings

if TYPE_CHECKING:
    from transformers import AutoTokenizer, VitsModel

logger = logging.getLogger(__name__)

STT_MODEL = "whisper-1"
STT_LANGUAGE = "bn"  # Bengali
TTS_MODEL_NAME = "facebook/mms-tts-ben"
AUDIO_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "generated_audio"
# Peak amplitude synthesized audio is normalized to before quantizing to
# 16-bit PCM — leaves a small margin under full scale (1.0) so normalizing a
# quiet MMS-TTS render doesn't clip.
_TTS_PEAK_TARGET = 0.95

_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MARKDOWN_EMPHASIS_RE = re.compile(r"\*\*(.+?)\*\*|\*(.+?)\*")
_MARKDOWN_BULLET_RE = re.compile(r"^\s*[-*•]\s+", re.MULTILINE)
_WHITESPACE_RE = re.compile(r"[ \t]+")

_tts_model: VitsModel | None = None
_tts_tokenizer: AutoTokenizer | None = None


def init_tts_model() -> None:
    """Loads the MMS-TTS Bengali model once, at server startup (see
    app.main's lifespan). Idempotent — safe to call more than once. Must not
    be called per-request; synthesize_speech only ever reads the singletons
    this sets, exactly like agents/checkpointer.init_checkpointer opens its
    connection pool once rather than per-call.

    Not currently called from anywhere (voice is stalled) — requires
    transformers/torch to be reinstalled before this can run again."""
    from transformers import AutoTokenizer, VitsModel

    global _tts_model, _tts_tokenizer
    if _tts_model is not None:
        return
    logger.info("Loading MMS-TTS Bengali model (%s)...", TTS_MODEL_NAME)
    _tts_model = VitsModel.from_pretrained(TTS_MODEL_NAME)
    _tts_tokenizer = AutoTokenizer.from_pretrained(TTS_MODEL_NAME)
    logger.info("MMS-TTS Bengali model loaded.")


def transcribe_audio(audio_file) -> str | None:
    """Sends audio_file (a file-like object — e.g. io.BytesIO with a `.name`
    set so the SDK can infer the format) to OpenAI's Whisper API. Returns the
    transcribed text, or None on any failure (missing key, network error,
    empty result). Callers must never treat a None return as an empty
    message — see nodes/voice_input.py, which keeps a failed transcription
    from silently continuing into intent classification."""
    if not settings.openai_api_key:
        logger.error("transcribe_audio: OPENAI_API_KEY is not configured")
        return None

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        transcript = client.audio.transcriptions.create(
            model=STT_MODEL, file=audio_file, language=STT_LANGUAGE
        )
    except Exception:  # noqa: BLE001 — any SDK/HTTP failure is a hard failure here
        logger.exception("transcribe_audio: Whisper API call failed")
        return None

    text = (transcript.text or "").strip()
    return text or None


def _clean_text_for_tts(text: str) -> str:
    """Strips the markdown FormattedText.jsx renders (**bold**, [links](url),
    bullet markers) before handing text to the TTS tokenizer. MMS-TTS-ben was
    never trained on markdown syntax — literal asterisks/brackets reaching it
    get mangled into audible noise mid-sentence, not just left silent, so
    this is a real source of unclear speech, not a cosmetic nicety."""
    cleaned = _MARKDOWN_LINK_RE.sub(r"\1", text)
    cleaned = _MARKDOWN_EMPHASIS_RE.sub(lambda m: m.group(1) or m.group(2) or "", cleaned)
    cleaned = _MARKDOWN_BULLET_RE.sub("", cleaned)
    cleaned = cleaned.replace("\n", ". ")
    return _WHITESPACE_RE.sub(" ", cleaned).strip()


def synthesize_speech(bengali_text: str) -> str | None:
    """Runs the pre-loaded MMS-TTS model over bengali_text and writes a .wav
    file, returning its path — or None on any failure (model not loaded,
    inference error, disk write error). Callers must still return the text
    response even when this returns None — see nodes/voice_output.py, which
    never blocks the farmer-facing message on TTS succeeding."""
    if _tts_model is None or _tts_tokenizer is None:
        logger.error("synthesize_speech: TTS model not loaded — init_tts_model() was never called at startup")
        return None

    cleaned_text = _clean_text_for_tts(bengali_text)
    if not cleaned_text:
        return None

    import numpy as np
    import scipy.io.wavfile
    import torch

    try:
        inputs = _tts_tokenizer(cleaned_text, return_tensors="pt")
        with torch.no_grad():
            waveform = _tts_model(**inputs).waveform

        samples = waveform.squeeze().cpu().numpy().astype(np.float32)
        # The model's raw output is float32 (amplitude varies by input —
        # often quiet) and scipy would otherwise write it as an IEEE-float
        # WAV, a format most browsers/players decode inconsistently at best.
        # Peak-normalizing then quantizing to standard 16-bit PCM fixes both
        # the "quiet"/"muffled" complaint and the format-compatibility one.
        peak = float(np.max(np.abs(samples))) if samples.size else 0.0
        if peak > 0:
            samples = samples / peak * _TTS_PEAK_TARGET
        pcm16 = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)

        AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        audio_path = AUDIO_OUTPUT_DIR / f"{uuid.uuid4()}.wav"
        scipy.io.wavfile.write(str(audio_path), rate=_tts_model.config.sampling_rate, data=pcm16)
        return str(audio_path)
    except Exception:  # noqa: BLE001 — any inference/write failure is a hard failure here
        logger.exception("synthesize_speech: MMS-TTS inference/write failed")
        return None
