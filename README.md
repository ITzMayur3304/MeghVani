# MeghVaani prototype

MeghVaani is a government-style weather intelligence prototype for Problem Statement 26069. It demonstrates the core vertical flow: citizen report submission, explainable event classification, verification confidence, map visibility, and disaster-response guidance.

## Stack

- **Frontend:** React 18, Vite, React Router, responsive CSS, Leaflet-ready map surface
- **Backend:** Python, FastAPI, Pydantic, rule-based NLP/classification
- **Persistence:** in-memory demo store now, with a MongoDB/Atlas boundary ready for the next iteration
- **Verification:** source reliability + event classification + duplicate corroboration + weather agreement signals

## Run locally

Frontend:

```bash
npm install
npm run dev
```

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The frontend falls back to seeded demo data when the API is unavailable, so the UI can be reviewed before configuring MongoDB or external weather credentials. API keys and connection strings belong in `backend/.env`; never commit them.

## Prototype routes

- `/` public situational dashboard
- `/report` citizen report submission
- `/map` live report map and filters
- `/alerts` active alerts and safe zones
- `/about` verification principles
- `/admin/dashboard` operational verification queue
