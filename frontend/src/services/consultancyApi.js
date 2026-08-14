const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function parseErrorMessage(response) {
  try {
    const body = await response.json();
    return body.detail || "Something went wrong. Please try again.";
  } catch {
    return "Something went wrong. Please try again.";
  }
}

function authHeaders(token) {
  return { Authorization: `Bearer ${token}` };
}

export async function getConsultancyAccess(token) {
  const response = await fetch(`${API_URL}/api/consultancy/access`, { headers: authHeaders(token) });
  if (!response.ok) throw new Error(await parseErrorMessage(response));
  return response.json();
}

export async function getExperts(token) {
  const response = await fetch(`${API_URL}/api/consultancy/experts`, { headers: authHeaders(token) });
  if (!response.ok) throw new Error(await parseErrorMessage(response));
  return response.json();
}

export async function createConsultation(token, { expertId, topic }) {
  const response = await fetch(`${API_URL}/api/consultancy/requests`, {
    method: "POST",
    headers: { ...authHeaders(token), "Content-Type": "application/json" },
    body: JSON.stringify({ expert_id: expertId, topic }),
  });
  if (!response.ok) throw new Error(await parseErrorMessage(response));
  return response.json();
}

export async function getConsultations(token) {
  const response = await fetch(`${API_URL}/api/consultancy/requests`, { headers: authHeaders(token) });
  if (!response.ok) throw new Error(await parseErrorMessage(response));
  return response.json();
}
