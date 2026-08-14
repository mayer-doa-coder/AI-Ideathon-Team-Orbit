"""voice_input — transcribes an uploaded voice message via Whisper, run
instead of the normal slot-fill/intent intake path whenever the farmer's
message carries audio instead of (or alongside) typed text (see
`router.intake_router`).

One real external call, traced like `weather_tool` traces Open-Meteo and
`disease_detection` traces crop.health. On success, the transcribed text is
appended to `messages` as a normal HumanMessage and control passes to
`classify_intent` — the exact same intake path a typed message takes, so
none of the downstream agent logic needs to know a message originated as
voice at all (see `router.voice_input_router`).

On failure, never treats the missing transcription as an empty/no-op
message — that would let a farmer's real (but unrecognized) voice message
silently vanish. Instead it ends the turn immediately with a message asking
the farmer to try again or type instead, still routed through
`voice_output` (see graph_conversation.py) since voice_input.used is true.
"""
import base64
import io

from langchain_core.messages import AIMessage, HumanMessage

from app.agents.state import AgentState
from app.tools.voice import STT_LANGUAGE, STT_MODEL, transcribe_audio

TRANSCRIPTION_FAILED_MESSAGE = (
    "Sorry, I couldn't understand that voice message. Could you try again, or type your message instead?"
)


def voice_input(state: AgentState) -> dict:
    audio_base64 = state.get("uploaded_audio")
    if not audio_base64:
        return {}

    trace: list[dict] = []

    try:
        audio_bytes = base64.b64decode(audio_base64)
    except Exception as exc:
        trace.append(
            {
                "type": "voice_input",
                "tool": "transcribe_audio",
                "paramsDisplay": "audio=<uploaded voice message>",
                "params": {"model": STT_MODEL, "language": STT_LANGUAGE},
                "response": {"error": f"invalid base64 audio data: {exc}"},
                "summary": "could not decode uploaded audio",
            }
        )
        return {
            "trace_log": trace,
            "voice_input": {"used": True, "transcribed_text": None, "stt_error": "invalid audio data"},
            "turn_complete": True,
            "messages": [AIMessage(content=TRANSCRIPTION_FAILED_MESSAGE)],
        }

    # .name is a format hint for the Whisper SDK/API, not a guarantee about
    # the actual encoding — the frontend is expected to record/send audio
    # that really is wav-compatible; a mismatched format still fails cleanly
    # via the except branch in transcribe_audio.
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "voice_message.wav"

    text = transcribe_audio(audio_file)

    trace.append(
        {
            "type": "voice_input",
            "tool": "transcribe_audio",
            "paramsDisplay": f"audio=<uploaded voice message>, model={STT_MODEL}, language={STT_LANGUAGE}",
            "params": {"model": STT_MODEL, "language": STT_LANGUAGE},
            "response": {"text": text} if text else {"error": "Whisper transcription failed"},
            "summary": f'transcribed: "{text}"' if text else "Whisper transcription failed — no text recognized",
        }
    )

    if not text:
        return {
            "trace_log": trace,
            "voice_input": {"used": True, "transcribed_text": None, "stt_error": "Whisper transcription failed"},
            "turn_complete": True,
            "messages": [AIMessage(content=TRANSCRIPTION_FAILED_MESSAGE)],
        }

    return {
        "trace_log": trace,
        "voice_input": {"used": True, "transcribed_text": text, "stt_error": None},
        "messages": [HumanMessage(content=text)],
    }
