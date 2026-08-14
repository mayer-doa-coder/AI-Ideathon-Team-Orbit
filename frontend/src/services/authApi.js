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

export async function registerUser(username, password) {
  const response = await fetch(`${API_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return response.json();
}

export async function loginUser(username, password) {
  const form = new URLSearchParams();
  form.set("username", username);
  form.set("password", password);

  const response = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form,
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return response.json();
}

export async function fetchCurrentUser(token) {
  const response = await fetch(`${API_URL}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    throw new Error(translate("errors.sessionExpired"));
  }

  return response.json();
}
