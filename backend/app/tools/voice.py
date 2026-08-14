"""Voice I/O: OpenAI Whisper speech-to-text and a locally-loaded MMS-TTS
Bengali model for text-to-speech.

Stays pure like tools/crop_health.py and tools/weather.py — no trace_log or
State knowledge here, that's built by the calling node (see
nodes/voice_input.py and nodes/voice_output.py). The TTS model load mirrors
agents/checkpointer.py's module-level-singleton-plus-init-function pattern:
VitsModel's weights are too large to reload on every request, so
init_tts_model() is called once from app.main's lifespan instead.

The two halves of this module have different status, and it matters:

  * Speech-to-text (transcribe_audio) is LIVE. It is a plain HTTPS call to
    OpenAI, needs no extra dependencies, and is what the mic button in
    ChatInput.jsx now uses. It handles Bangla and English.

  * Text-to-speech (init_tts_model / synthesize_speech) is still OFF. It needs
    torch/transformers/scipy/numpy, which are NOT in requirements.txt — the
    CPU-only torch wheel alone is a multi-gigabyte install for one feature.
    Their imports are therefore kept local to those two functions rather than
    at module level, so this module — and anything importing it
    (nodes/voice_input.py, nodes/voice_output.py, which the conversation graph
    always loads) — stays importable without them. synthesize_speech() returns
    None when the model was never loaded, so voice_output degrades to a
    text-only reply instead of raising. Re-add those four packages to
    requirements.txt and call init_tts_model() from app.main's lifespan before
    expecting spoken replies.
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

# Speech-to-text model. gpt-4o-transcribe rather than whisper-1 for two
# measured reasons (both verified against real Bangla and English farmer
# speech before switching):
#
#   1. whisper-1 REJECTS Bengali outright. `language="bn"` returns
#      HTTP 400 "Language 'bn' is not supported." — so the previous
#      configuration could never transcribe anything; every voice message
#      failed. This was the actual reason voice was "unreliable".
#   2. On the same audio, transcription accuracy was gpt-4o-transcribe 97% /
#      whisper-1 (auto-detect) 81% for Bangla, and 92% / 91% for English.
#
# whisper-1 is kept as a fallback only — it still handles English well and a
# degraded transcription beats losing the farmer's message entirely.
STT_MODEL = "gpt-4o-transcribe"
STT_FALLBACK_MODEL = "whisper-1"
# Languages we will pass as a hint. Anything else is sent without one, letting
# the model auto-detect, which is better than asserting a wrong language.
STT_SUPPORTED_HINTS = {"bn", "en"}
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


def is_tts_available() -> bool:
    """True only when the text-to-speech stack is actually installed AND the
    model has been loaded. Lets callers tell "switched off" apart from "tried
    and failed" — see nodes/voice_output.py, which would otherwise report a
    red error on every voice turn for a feature that is simply not enabled."""
    return _tts_model is not None and _tts_tokenizer is not None


def transcribe_audio(audio_file, language: str | None = None) -> str | None:
    """Transcribes audio_file (a file-like object — e.g. io.BytesIO with a
    `.name` set so the SDK can infer the format) to text.

    `language` is an ISO-639-1 hint, normally the farmer's current UI language
    ("bn" or "en"), threaded through from the chat request. It is a hint, not a
    constraint: a farmer with the Bangla UI who says an English crop name still
    transcribes correctly. Passing the hint measurably beats auto-detection on
    Bangla (97% vs 92% on the same audio), because these are short utterances
    where the model has little to detect from. Anything outside
    STT_SUPPORTED_HINTS is sent without a hint rather than asserted wrongly.

    No `prompt` is passed. Seeding domain vocabulary (Boro, BRRI, urea, district
    names) was tried and measured *worse* — it pushed the model toward digits
    ("৩০" for "ত্রিশ") and mis-transcribed common soil terms.

    Returns the transcribed text, or None on any failure (missing key, network
    error, empty result). Callers must never treat a None return as an empty
    message — see nodes/voice_input.py, which keeps a failed transcription from
    silently continuing into intent classification.
    """
    if not settings.openai_api_key:
        logger.error("transcribe_audio: OPENAI_API_KEY is not configured")
        return None

    hint = language if language in STT_SUPPORTED_HINTS else None
    client = OpenAI(api_key=settings.openai_api_key)

    def _call(model: str, with_hint: bool) -> str | None:
        # audio_file is a stream and the first attempt consumes it, so rewind
        # before any retry or the fallback uploads zero bytes.
        audio_file.seek(0)
        kwargs = {"model": model, "file": audio_file}
        if with_hint and hint:
            kwargs["language"] = hint
        transcript = client.audio.transcriptions.create(**kwargs)
        return (transcript.text or "").strip() or None

    try:
        return _call(STT_MODEL, with_hint=True)
    except Exception:  # noqa: BLE001 — any SDK/HTTP failure falls through to the fallback
        logger.exception("transcribe_audio: %s failed, retrying with %s", STT_MODEL, STT_FALLBACK_MODEL)

    try:
        # No hint on the fallback: whisper-1 rejects "bn" with a 400, so a hint
        # here would turn a recoverable failure into a guaranteed one.
        return _call(STT_FALLBACK_MODEL, with_hint=False)
    except Exception:  # noqa: BLE001 — both models failed; the caller handles None
        logger.exception("transcribe_audio: fallback %s also failed", STT_FALLBACK_MODEL)
        return None


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
