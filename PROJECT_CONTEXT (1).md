# National Weather Intelligence Platform — Agent Context

## Problem Statement (Summary)
Build a scalable weather data aggregation and verification platform for India (Problem Statement 26069). It ingests weather-related information from multiple sources (social media, weather APIs, news, citizen reports), stores it centrally, uses AI to classify events and detect fake/duplicate reports, and presents it via a public dashboard + admin panel. We are building a 2-day hackathon prototype, not a production system — prioritize a working end-to-end vertical flow over feature breadth.

## Core Demo Story (this is what must work end-to-end)
1. A report comes in (citizen form / Reddit / seeded sample data)
2. AI classifies the event type and extracts location
3. Duplicate detection checks it against existing reports
4. Weather API cross-verifies the claim (e.g. is rain actually detected in that area)
5. A confidence score is calculated and a verification status assigned
6. Report appears on the India map with correct marker/color
7. If enough verified reports cluster on the same event/location, a severity level triggers and the Disaster Response Module surfaces safe zones + precautions

If this loop works cleanly, the project succeeds. Everything else is secondary.

## Tech Stack
- **Frontend:** React + Tailwind CSS. Map via Leaflet (free, no API key needed) unless a team member prefers Mapbox.
- **Backend:** Python + FastAPI
- **Database:** MongoDB (Atlas free tier). Use `motor` (async driver) with FastAPI, or `pymongo` if the team prefers sync code for speed of development. Chosen over Postgres/Firebase because report documents from different sources have varying fields, geospatial queries (`$near`, `$geoWithin`) are built-in for duplicate/proximity/safe-zone logic, and Atlas free tier spins up in minutes.
- **AI/NLP:** scikit-learn, Pandas, NumPy. Use TF-IDF + cosine similarity for duplicate detection. Event classification can be a lightweight keyword/rule hybrid — do NOT attempt to train a deep learning model from scratch.
- **Data ingestion:** Reddit via PRAW (free, official API). Weather via any free-tier weather API. News via NewsAPI free tier (100 req/day). X/Twitter API is NOT free-tier anymore — do not build a dependency on it; treat it as a "future connector" mentioned in architecture only.
- **Real-time updates:** No Firebase real-time listeners available with MongoDB — implement dashboard refresh via polling every 5–10 seconds (simple `fetch` interval) or a lightweight WebSocket if time allows. Polling is sufficient for a 2-day prototype.
- **Auth (admin panel):** FastAPI + JWT (e.g. `fastapi-users` or a hand-rolled JWT login) since MongoDB has no bundled auth like Firebase does. Keep it simple — one admin role is enough for the demo.

## Common Data Schema — MongoDB Collection: `reports`
Each report is a document in the `reports` collection:
```json
{
  "_id": "ObjectId (Mongo default)",
  "report_id": "string (uuid, app-level id)",
  "source": "citizen | reddit | weather_api | news | simulated",
  "source_id": "string, original post/report id if applicable",
  "text": "string, raw description",
  "timestamp": "ISO 8601 datetime",
  "city": "string",
  "state": "string",
  "location": {
    "type": "Point",
    "coordinates": [77.5946, 12.9716]
  },
  "event_type": "rainfall | thunderstorm | flood | heatwave | fog | dust_storm | strong_wind | unknown",
  "photo_url": "string, optional",
  "video_url": "string, optional",
  "confidence_score": "float 0-1",
  "verification_status": "verified | review | suspicious | pending",
  "duplicate_of": "report_id or null",
  "source_reliability": "float 0-1"
}
```
Notes:
- `location` uses GeoJSON Point format (`[longitude, latitude]`, in that order — Mongo convention) so a **2dsphere index** can be created on it: `db.reports.createIndex({ location: "2dsphere" })`. This powers duplicate-by-proximity checks and nearest-safe-zone lookups directly in queries instead of hand-written distance math.
- A second collection `safe_zones` holds the hardcoded relief-point data (name, city, `location` as GeoJSON Point) — also indexed as `2dsphere` so nearest-safe-zone queries are a single `$near` call.
- A third collection `admin_users` holds admin login credentials (hashed passwords) for the JWT auth flow.

## AI Logic Rules

**Event classification:** keyword/phrase matching against event categories (e.g. "flood", "waterlogging", "submerged" → flood; "44°C", "heat", "sunstroke" → heatwave). Extend with simple NLP similarity if time allows. Always output a confidence percentage, never a bare label.

**Duplicate detection:** compute TF-IDF vectors of report text, compare cosine similarity between reports within the same city + a time window (e.g. 6 hours). Above a similarity threshold → mark as duplicate/cluster together rather than discard; duplicates count toward event severity, they are evidence not noise.

**Confidence scoring:** combine (a) source reliability weight, (b) location consistency, (c) duplicate/cluster corroboration, (d) weather API agreement. Output a 0–100% score. Map score ranges to status: e.g. ≥85% verified, 50–84% review, <50% suspicious.

**Severity/alert trigger:** when verified report count for one event+location cluster crosses a threshold (e.g. 10+ reports, high average confidence) within a short window, escalate severity using IMD's own scale: Green → Yellow → Orange → Red. On Orange/Red, activate the Disaster Response Module.

## Disaster Response Module (differentiator feature)
- Maintain a lookup table of precaution text per event_type (flood, heatwave, thunderstorm, etc.) — static content is fine, no AI needed here.
- Maintain a small hardcoded dataset of safe zones/relief points for 2–3 demo cities (Nashik, Pune, Mumbai) with lat/lng.
- When severity escalates, show: alert banner on dashboard, precaution card for that event type, nearest safe zone(s) via simple haversine distance calculation (no external routing API needed).
- Be explicit in the UI/pitch that this is a rule-based decision-support layer aligned to IMD/NDMA categories — do not claim predictive AI here.

## Explicit Non-Goals for the 2-Day Build
- Do not attempt real Instagram scraping (API restrictions make this a time sink)
- Do not attempt to deploy Kafka/Spark — mention as "scalable architecture" in the pitch only, use direct FastAPI → DB pipeline for the actual prototype
- Do not build a real-time streaming pipeline — polling every 10–30s or on-demand refresh is sufficient
- Do not over-invest in styling before the core loop (ingest → classify → verify → map) works

## Build Order (see team plan for full detail)
1. Schema + DB setup
2. Citizen report form → DB (simplest source first, validates pipeline)
3. Reddit + weather API connectors → normalize to schema
4. Classification + duplicate detection + confidence scoring
5. Map dashboard + filters + stats
6. Admin panel (verify/reject)
7. Disaster response module (severity trigger, precautions, safe zones)
8. Seed demo data, rehearse demo script

## Security & Secrets Management (Critical — Read Before Writing Any Ingestion/Auth Code)

This project will be pushed to a shared repo and likely deployed publicly for the demo, so secrets hygiene matters even under time pressure.

**Environment variables, not hardcoded keys:**
- All API keys/secrets (Reddit client ID/secret, weather API key, news API key, MongoDB connection string, JWT signing secret) go in a `.env` file at the backend root — never hardcoded in source files, never committed.
- Add `.env` to `.gitignore` from the very first commit, before any key is ever typed into a file.
- Commit a `.env.example` with placeholder values (e.g. `REDDIT_CLIENT_ID=your_id_here`) so teammates and judges can see what's required without seeing real values.
- Load env vars via `python-dotenv` in FastAPI (`os.getenv(...)`), never via a config file that gets committed.

**Third-party API calls must be server-side only:**
- All calls to Reddit/weather/news APIs happen from the FastAPI backend, never from the React frontend. Any key placed in frontend code (even in a `.env` used by React/Vite) ends up visible in the browser's shipped JS bundle — this is a hard rule, not a style preference.
- The frontend only ever calls your own backend endpoints; the backend is the only thing holding real credentials.

**MongoDB Atlas:**
- Use a database user with least-privilege access (read/write only to this project's database, not an admin-level Atlas user).
- Restrict Atlas Network Access to specific IPs where possible; if using "Allow Access from Anywhere" for demo convenience, treat this as a temporary/demo-only setting and note it as a known risk, not a production pattern.
- Never commit the full MongoDB connection string (it contains the username/password) — it goes in `.env` like everything else.

**Admin authentication:**
- Hash admin passwords with bcrypt (or similar) — never store plaintext passwords, even for a hackathon demo login.
- JWT signing secret lives in `.env`, with a reasonable token expiry (a few hours is fine for demo purposes).
- Do not hardcode a default admin password into source code as a "for now" shortcut — set it via a seed script that reads from `.env` instead.

**Public-facing attack surface (the citizen report endpoint is the riskiest one — it's open to anyone):**
- Add basic rate limiting on the report-submission endpoint to prevent spam/flooding (e.g. `slowapi` for FastAPI, or a simple in-memory rate check for the prototype).
- Validate and sanitize all incoming fields (reject oversized text, validate file type/size on photo/video uploads — don't trust the client's declared MIME type alone).
- Do not return verbose stack traces or internal error details in API responses — return generic error messages to the client and log details server-side only.

**CORS:**
- Restrict allowed origins to your actual frontend URL(s) once you know them (localhost during dev, your deployed domain for the demo) — avoid a wildcard `*` origin in anything resembling a production/demo-public build.

**Before pushing to GitHub or sharing the repo:**
- Do a final manual check (or run a tool like `git-secrets` / `truffleHog` if time allows) across the whole diff for anything that looks like a key, password, or connection string before the first push and before any push that touches config files.
- If a key is ever accidentally committed, treat it as compromised — rotate/regenerate it immediately rather than just deleting it from a later commit (it remains in git history otherwise).


- When in doubt about scope, favor the smallest implementation that keeps the end-to-end demo loop functional.
- Keep all source connectors behind a common interface/function signature so adding/removing a source doesn't touch downstream code.
- Prefer clear, inspectable logic (rule-based/statistical) over black-box approaches — this project is judged partly on explainability of its AI claims.
