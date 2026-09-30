# MeghVaani backend

FastAPI prototype for the National Weather Intelligence Platform. It uses Supabase
when both Supabase variables are configured and otherwise uses a seeded in-memory
store, so the demo remains zero-config. Reports are classified with keyword rules,
scored using source reliability and duplicate corroboration, and grouped into alerts.

## Run locally

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Copy `.env.example` to `.env` before configuring providers. API documentation is
available at http://localhost:8000/docs. `.env` is ignored by git.

## Persistence and providers

Run `schema.sql` in Supabase, then set `SUPABASE_URL` and
`SUPABASE_SERVICE_ROLE_KEY`. The service-role key is server-only and bypasses RLS;
keep it out of frontend bundles. Without both values, reports stay in memory.

`POST /api/ingestion/weather` requires `OPENWEATHER_API_KEY` and sends the
coordinates in the request to OpenWeather, storing a cross-check report.
`POST /api/ingestion/reddit` uses Reddit OAuth client credentials and the configured
user agent to read subreddit posts. No provider is contacted without credentials.

TweetHarvest is deliberately a configurable connector because deployments expose
different TweetHarvest versions. Set `TWEETHARVEST_API_URL` and optionally an API
key or bearer token. The endpoint sends `{"query": "...", "limit": N}` via POST
and expects either a JSON list or `{ "tweets": [...] }` / `{ "data": [...] }`.
Each item must contain `text` or `full_text`, and may contain `id`. Confirm the
exact API contract, authentication header, and response shape with your
TweetHarvest deployment before enabling it.

Authentication:

* `POST /api/citizens/register` and `POST /api/citizens/login` accept
  `{ "email": "...", "password": "..." }` and return a JWT. Passwords are
  salted PBKDF2-SHA256 hashes and registrations are held in memory in demo mode.
* `POST /api/reports` requires `Authorization: Bearer <citizen-token>`.
  `GET /api/reports`, `/api/alerts`, and `/api/notifications` remain public.
* `POST /api/admin/login` remains available for the configured admin. Set
  `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`, and a random, environment-only
  `JWT_SECRET`; no credentials or fallback secret are hardcoded.

OpenWeather ingestion can be triggered with the existing
`POST /api/ingestion/weather` or a polling-friendly
`GET /api/ingestion/weather/poll?city=...&state=...&latitude=...&longitude=...`.
Both use `OPENWEATHER_API_KEY`, `OPENWEATHER_BASE_URL`, and
`OPENWEATHER_POLL_INTERVAL_SECONDS`. Without the API key, demo read endpoints
continue to work and ingestion returns `503`.
