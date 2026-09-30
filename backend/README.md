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

Admin login is a placeholder at `POST /api/admin/login`. Set `ADMIN_USERNAME`,
`JWT_SECRET`, and a PBKDF2 password hash in `.env`; no password is hardcoded.
Generate a hash in a trusted local script rather than committing credentials.
