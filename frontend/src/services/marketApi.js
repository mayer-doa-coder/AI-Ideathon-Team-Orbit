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

export async function getSupportedCrops(token) {
  const response = await fetch(`${API_URL}/api/market/crops`, { headers: authHeaders(token) });
  if (!response.ok) throw new Error(await parseErrorMessage(response));
  return response.json();
}

// The main call the Market Price Intelligence card uses — current price,
// historical average/high/low, 7d/30d change, trend, and the deterministic
// SELL NOW/STORE/WAIT verdict with its reasons, in one response.
export async function getMarketDecision(token, params) {
  const query = new URLSearchParams();
  query.set("crop", params.crop);
  if (params.season) query.set("season", params.season);
  if (params.district) query.set("district", params.district);
  if (params.storageAvailable !== undefined && params.storageAvailable !== null) {
    query.set("storage_available", String(params.storageAvailable));
  }
  if (params.storageCostBdtPerUnitPerMonth) {
    query.set("storage_cost_bdt_per_unit_per_month", String(params.storageCostBdtPerUnitPerMonth));
  }
  if (params.quantityKg) query.set("quantity_kg", String(params.quantityKg));
  if (params.urgentCashNeeded !== undefined && params.urgentCashNeeded !== null) {
    query.set("urgent_cash_needed", String(params.urgentCashNeeded));
  }

  const response = await fetch(`${API_URL}/api/market/decision?${query}`, { headers: authHeaders(token) });
  if (!response.ok) throw new Error(await parseErrorMessage(response));
  return response.json();
}

export async function getMarketHistory(token, { crop, season, district, days = 180 }) {
  const query = new URLSearchParams({ crop, days: String(days) });
  if (season) query.set("season", season);
  if (district) query.set("district", district);

  const response = await fetch(`${API_URL}/api/market/history?${query}`, { headers: authHeaders(token) });
  if (!response.ok) throw new Error(await parseErrorMessage(response));
  return response.json();
}
