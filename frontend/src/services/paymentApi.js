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

export async function checkout(token, { msisdn, amount, description }) {
  const response = await fetch(`${API_URL}/api/payment/checkout`, {
    method: "POST",
    headers: { ...authHeaders(token), "Content-Type": "application/json" },
    body: JSON.stringify({ msisdn, amount, description }),
  });
  if (!response.ok) throw new Error(await parseErrorMessage(response));
  return response.json();
}

export async function getPaymentHistory(token, msisdn) {
  const query = new URLSearchParams({ msisdn });
  const response = await fetch(`${API_URL}/api/payment/history?${query}`, { headers: authHeaders(token) });
  if (!response.ok) throw new Error(await parseErrorMessage(response));
  return response.json();
}
