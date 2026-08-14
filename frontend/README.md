# Green Leaf AI — Frontend

React + Vite frontend for Green Leaf AI, styled to match the "Agriva" design reference in `../Main files/` (colors, fonts, button/input conventions extracted into `src/index.css`).

## Pages

- **Home** (`/`, `src/pages/HomePage.jsx`) — public landing page matching the Agriva `index.html` ("Maize Farming") layout: header/nav, hero, features, about (animated stat counters), why-choose-us, services, FAQ accordion, testimonials carousel, blog/news, brand strip, footer. Styles in `src/styles/home.css`.
- **Login** (`/login`, `src/pages/LoginPage.jsx`) — combined login/register form (toggle between modes). Redirects to `/chat` if already authenticated.
- **Dashboard** (`/chat`, `src/pages/ChatPage.jsx`, requires auth) — split-screen: guided chat on the left drives a live-updating dashboard on the right (Farm Profile, Live Agent Trace, Weather, Crop Comparison, Season Plan, Financial Breakdown, Alerts, Knowledge Sources). Styles in `src/styles/dashboard.css`. All agent behavior (tool calls, recommendations, weather) is simulated client-side in `src/data/*Script.js` — no real AI backend yet.

Routing (`App.jsx`) wraps everything in `AuthProvider`; `/chat` is wrapped in `RequireAuth`, which redirects to `/login` when logged out.

## Auth & per-user sessions

- `src/context/AuthContext.jsx` — holds the logged-in user/token, persists them to `localStorage` (`agrisense_token` / `agrisense_username`), and validates the stored token against the backend's `GET /api/auth/me` on app load.
- `src/services/authApi.js` — fetch wrappers for the backend (`VITE_API_URL`, see `.env`).
- `src/data/dashboardStorage.js` — each user's dashboard session (messages, farm profile, trace log, selected crop, alerts, etc.) is saved to `localStorage` under a key derived from their username, and restored on login/reload — so different users in the same browser never see each other's session, and reloading doesn't lose progress.
- Requires the backend (`../backend/`) running for register/login to work — see its README.

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Opens at http://localhost:5173. Set `VITE_API_URL` in `.env` if the backend isn't at the default `http://localhost:8000`.

## Run with Docker

See the [root README](../README.md#run-everything-with-docker) — `docker compose up -d --build` from the repo root runs this alongside the backend and Postgres.

## Notes

- Font Awesome (icons) and Google Fonts (Instrument Sans / Inter) are loaded via `index.html`; Font Awesome assets were copied from the Agriva template into `public/assets/`.
- Most photographic assets in the Agriva template (`Main files/agriva/assets/img/`) are dummy placeholder images (literally "1920X1000" gray boxes), not real photography. Home page image slots use gradient/icon placeholder blocks instead.
