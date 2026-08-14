"""voice_output — the conversation graph's single shared exit funnel. Every
terminal node routes here instead of directly to END (see
graph_conversation.py), so a voice turn's spoken reply gets generated in
exactly one place regardless of which node produced the farmer-facing text
— ask_followup, crop_recommendation, disease_explanation, qa_agent, and so
on all reach it the same way, rather than duplicating a synthesize_speech
call at every one of them.

No-ops immediately (and cheaply) for any turn that didn't come in as voice
— state.voice_input.used is only true when voice_input actually ran this
turn (see nodes/voice_input.py) — so a normal typed turn pays no TTS cost.

Never blocks the text response: if synthesize_speech fails,
voice_output.audio_path stays null and the farmer-facing message already in
`messages` is returned exactly as-is.
"""
from langchain_core.messages import AIMessage

from app.agents.state import AgentState
from app.tools.voice import synthesize_speech

_SUMMARY_MAX_CHARS = 60


def voice_output(state: AgentState) -> dict:
    voice_input_state = state.get("voice_input") or {}
    if not voice_input_state.get("used"):
        return {}

    messages = state.get("messages") or []
    last_ai = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)
    text = (last_ai.content if last_ai else "") or ""
    if not text:
        return {}

    display_text = text if len(text) <= _SUMMARY_MAX_CHARS else f"{text[:_SUMMARY_MAX_CHARS]}..."
    audio_path = synthesize_speech(text)

    trace = [
        {
            "type": "voice_output",
            "tool": "synthesize_speech",
            "paramsDisplay": f'text="{display_text}"',
            "params": {"text": text},
            "response": {"audio_path": audio_path} if audio_path else {"error": "MMS-TTS synthesis failed"},
            "summary": (
                f"synthesized Bengali audio -> {audio_path}"
                if audio_path
                else "MMS-TTS synthesis failed — returning text-only response"
            ),
        }
    ]

    return {
        "trace_log": trace,
        "voice_output": {
            "requested": True,
            "audio_path": audio_path,
            "tts_error": None if audio_path else "Bengali speech synthesis failed",
        },
    }
