import json
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage

from app.agents.graph_conversation import conversation_graph
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.chat import (
    ChatRequest,
    serialize_crop_candidates,
    serialize_knowledge_sources,
    serialize_messages,
    serialize_season_plan,
    serialize_weather,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Nodes whose LLM call produces the farmer-facing text directly (safe to
# token-stream). Every other node either has no LLM call or uses structured
# output, whose raw token stream is partial JSON, not something to show.
TOKEN_STREAM_NODES = {"casual_response"}


def _sse(event_type: str, data: dict) -> str:
    return f"data: {json.dumps({'type': event_type, **data})}\n\n"


@router.post("")
def send_message(payload: ChatRequest, current_user: User = Depends(get_current_user)):
    thread_id = str(current_user.id)
    config = {"configurable": {"thread_id": thread_id}}

    def event_stream():
        has_location = payload.lat is not None and payload.lon is not None
        input_state = {
            "messages": [HumanMessage(content=payload.message)],
            "farmer_id": thread_id,
            "turn_complete": False,
            "is_scenario": False,
            # Set fresh every turn (never carried over) — the farmer may
            # have shared their location once but this specific message
            # isn't a "near me" query, or vice versa.
            "current_location": {"lat": payload.lat, "lon": payload.lon} if has_location else None,
            "uploaded_image": payload.image_base64,
            "uploaded_audio": payload.audio_base64,
        }
        # Running cache: season_plan and financials arrive from two different
        # nodes (season_planner, then calculate_financials) but the frontend
        # needs both together to render milestone costs, so the season_plan
        # event is emitted once financials lands, not the moment the plan does.
        cache = {"farm_profile": {}, "selected_crop": None, "season_plan": None, "financials": None}
        try:
            for stream_mode, chunk in conversation_graph.stream(
                input_state, config, stream_mode=["updates", "messages"]
            ):
                if stream_mode == "messages":
                    message_chunk, metadata = chunk
                    node = metadata.get("langgraph_node")
                    # LangGraph's "messages" mode emits both the live per-token
                    # AIMessageChunk deltas AND, once the node returns, the full
                    # committed AIMessage it added to state — skip the latter or
                    # the streamed text gets duplicated in full at the end.
                    if (
                        node in TOKEN_STREAM_NODES
                        and isinstance(message_chunk, AIMessageChunk)
                        and message_chunk.content
                    ):
                        yield _sse("token", {"node": node, "content": message_chunk.content})
                    continue

                # stream_mode == "updates": {node_name: partial_state_update}
                for node_name, node_output in chunk.items():
                    if not node_output:
                        continue

                    # Membership checks ("key" in node_output), not truthiness —
                    # a node can legitimately clear one of these to None/[]
                    # (core_change_handler does, when a confirmed profile
                    # change invalidates the existing crop/plan) and that
                    # clearing has to reach the dashboard live too, not just
                    # get silently dropped because None/[] is falsy.
                    if "farm_profile" in node_output:
                        cache["farm_profile"] = node_output["farm_profile"] or {}
                    if "selected_crop" in node_output:
                        cache["selected_crop"] = node_output["selected_crop"]
                    if "season_plan" in node_output:
                        cache["season_plan"] = node_output["season_plan"]
                    if "financials" in node_output:
                        cache["financials"] = node_output["financials"]

                    for entry in node_output.get("trace_log") or []:
                        yield _sse("trace", {"entry": {**entry, "id": f"trace-{uuid4()}"}})

                    for message in node_output.get("messages") or []:
                        if isinstance(message, AIMessage) and node_name not in TOKEN_STREAM_NODES:
                            message_payload = {"node": node_name, "text": message.content}
                            badge = message.additional_kwargs.get("badge")
                            if badge:
                                message_payload["badge"] = badge
                            yield _sse("message", message_payload)

                    if "farm_profile" in node_output:
                        yield _sse("profile", {"farm_profile": cache["farm_profile"]})

                    if "crop_candidates" in node_output:
                        yield _sse(
                            "crops",
                            {"crops": serialize_crop_candidates(node_output["crop_candidates"] or [])},
                        )

                    if "weather_data" in node_output:
                        weather_data = node_output["weather_data"]
                        location = cache["farm_profile"].get("location", "")
                        yield _sse(
                            "weather",
                            {"weather": serialize_weather(weather_data, location) if weather_data else None},
                        )

                    if "financials" in node_output:
                        yield _sse("financials", {"financials": cache["financials"]})
                        yield _sse(
                            "season_plan",
                            {
                                "crop": cache["selected_crop"],
                                "milestones": (
                                    serialize_season_plan(cache["season_plan"], cache["financials"])
                                    if cache["season_plan"]
                                    else None
                                ),
                            },
                        )

                    if "voice_output" in node_output:
                        voice_out = node_output["voice_output"]
                        audio_path = voice_out.get("audio_path")
                        # audio_path is a server filesystem path (see
                        # tools/voice.synthesize_speech) — turn it into the
                        # URL main.py's /generated_audio static mount serves.
                        audio_url = f"/generated_audio/{Path(audio_path).name}" if audio_path else None
                        yield _sse(
                            "audio",
                            {"audio_url": audio_url, "tts_error": voice_out.get("tts_error")},
                        )

                    if "retrieved_docs" in node_output:
                        yield _sse(
                            "sources",
                            {"sources": serialize_knowledge_sources(node_output["retrieved_docs"] or [])},
                        )

            yield _sse("done", {})
        except Exception as exc:  # noqa: BLE001 — surface any failure to the client instead of a silent hang
            logger.exception("Conversation graph turn failed for thread_id=%s", thread_id)
            yield _sse("error", {"message": str(exc)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/state")
def get_chat_state(current_user: User = Depends(get_current_user)):
    thread_id = str(current_user.id)
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = conversation_graph.get_state(config)
    values = snapshot.values or {}

    financials = values.get("financials")
    season_plan = values.get("season_plan")
    weather_data = values.get("weather_data")
    farm_profile = values.get("farm_profile") or {}

    return {
        "messages": serialize_messages(values.get("messages") or []),
        "farm_profile": farm_profile,
        "crop_candidates": serialize_crop_candidates(values.get("crop_candidates") or []),
        "selected_crop": values.get("selected_crop"),
        "season_plan": serialize_season_plan(season_plan, financials) if season_plan else None,
        "financials": financials,
        "weather": serialize_weather(weather_data, farm_profile.get("location", "")) if weather_data else None,
        "sources": serialize_knowledge_sources(values.get("retrieved_docs") or []),
        "trace_log": [{**e, "id": f"trace-{i}"} for i, e in enumerate(values.get("trace_log") or [])],
    }
