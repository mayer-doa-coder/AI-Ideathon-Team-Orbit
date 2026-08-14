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

export async function searchKnowledgeBase(query, { crop, topic, k } = {}) {
  const response = await fetch(`${API_URL}/api/rag/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, crop: crop || null, topic: topic || null, k: k || 5 }),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return response.json();
}

export async function askKnowledgeBase(query, { k } = {}) {
  const response = await fetch(`${API_URL}/api/rag/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, k: k || 5 }),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return response.json();
}
