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

function authHeaders(token) {
  return { Authorization: `Bearer ${token}` };
}

// Returns null (rather than throwing) when the user has no active farm yet —
// that's the expected, common case whenever the conversation agent hasn't
// created one for this account yet, not an error.
export async function getMyFarm(token) {
  const response = await fetch(`${API_URL}/api/farms/me`, {
    headers: authHeaders(token),
  });

  if (response.status === 404) return null;
  if (!response.ok) throw new Error(await parseErrorMessage(response));
  return response.json();
}

// Reads the farm's plan straight from Postgres — the one source that
// reflects a monitor-triggered adjustment immediately, even with no new
// sweep this session (unlike /api/chat/state, which reads the conversation
// graph's checkpoint and never sees monitor writes).
export async function getMyPlan(token) {
  const response = await fetch(`${API_URL}/api/farms/me/plan`, {
    headers: authHeaders(token),
  });

  if (response.status === 404) return null;
  if (!response.ok) throw new Error(await parseErrorMessage(response));
  return response.json();
}

export async function checkWeatherNow(token, farmId) {
  const response = await fetch(`${API_URL}/api/monitor/check-weather-now/${farmId}`, {
    method: "POST",
    headers: authHeaders(token),
  });

  if (!response.ok) throw new Error(await parseErrorMessage(response));
  return response.json();
}

export async function simulateTrigger(token, farmId) {
  const response = await fetch(`${API_URL}/api/monitor/simulate-trigger/${farmId}`, {
    method: "POST",
    headers: authHeaders(token),
  });

  if (!response.ok) throw new Error(await parseErrorMessage(response));
  return response.json();
}

export async function listAlerts(token, farmId) {
  const response = await fetch(`${API_URL}/api/alerts?farm_id=${farmId}`, {
    headers: authHeaders(token),
  });

  if (!response.ok) throw new Error(await parseErrorMessage(response));
  return response.json();
}

export async function getTraceLog(token, farmId) {
  const response = await fetch(`${API_URL}/api/trace/${farmId}`, {
    headers: authHeaders(token),
  });

  if (!response.ok) throw new Error(await parseErrorMessage(response));
  return response.json();
}
