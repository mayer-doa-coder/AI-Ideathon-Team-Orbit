import { translate } from "../i18n/translations";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function parseErrorMessage(response) {
  try {
    const body = await response.json();
    return body.detail || translate("errors.genericFallback");
  } catch {
    return translate("errors.genericFallback");
  }
}

// Full persisted conversation for this user — backed by the LangGraph
// Postgres checkpointer, keyed off the JWT-derived user id. Called on mount
// so a reload (or a login from a different device) resumes the real
// conversation instead of starting a fresh wizard.
export async function fetchChatState(token) {
  const response = await fetch(`${API_URL}/api/chat/state`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return response.json();
}

// Reads a File or Blob as base64 (no "data:...;base64," prefix — the
// backend adds its own data URI when it forwards the image to GPT-5.6 Sol's
// vision call, and reads raw bytes directly for voice audio).
function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(",", 2)[1] ?? "");
    reader.onerror = () => reject(new Error(translate("errors.photoReadError")));
    reader.readAsDataURL(file);
  });
}

// Sends one chat turn and streams the agent's Server-Sent Events as they
// arrive, invoking onEvent for each parsed { type, ... } payload. Uses
// fetch()+ReadableStream rather than the native EventSource, since
// EventSource can't send a POST body or an Authorization header.
//
// `location`, if given ({ lat, lon }), is the farmer's current browser
// position for this message only (see ChatInput's "share my location"
// button) — distinct from their farm's registered location, and not
// persisted beyond this one request.
//
// `imageFile`, if given, is sent as base64 — a photo attached via
// ChatInput's camera button, routed by the backend straight to
// disease_detection instead of the normal intake path.
//
// `audioBlob`, if given, is sent as base64 — a voice message recorded via
// ChatInput's mic button (already re-encoded to real WAV, see
// utils/audioToWav.js), routed by the backend straight to voice_input
// instead of the normal intake path.
export async function streamChatMessage(
  token,
  message,
  onEvent,
  location = null,
  imageFile = null,
  audioBlob = null
) {
  const image_base64 = imageFile ? await fileToBase64(imageFile) : null;
  const audio_base64 = audioBlob ? await fileToBase64(audioBlob) : null;

  const response = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      message,
      ...(location ? { lat: location.lat, lon: location.lon } : {}),
      ...(image_base64 ? { image_base64 } : {}),
      ...(audio_base64 ? { audio_base64 } : {}),
    }),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }
  if (!response.body) {
    throw new Error(translate("errors.streamingUnsupported"));
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";

    for (const frame of frames) {
      const line = frame.trim();
      if (!line.startsWith("data:")) continue;
      const jsonStr = line.slice("data:".length).trim();
      if (!jsonStr) continue;
      try {
        const event = JSON.parse(jsonStr);
        // The backend's "audio" event carries a path relative to its own
        // origin (see api/routes/chat.py's /generated_audio static mount) —
        // the frontend is served from a different origin, so it needs the
        // full URL to actually fetch/play it.
        if (event.type === "audio" && event.audio_url) {
          event.audio_url = `${API_URL}${event.audio_url}`;
        }
        onEvent(event);
      } catch {
        // Malformed frame — skip rather than break the whole stream.
      }
    }
  }
}
