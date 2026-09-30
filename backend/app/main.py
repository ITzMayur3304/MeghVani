from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import math
import re
import secrets
import time
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from .main_types import EventType, Location, Report
from .repository import MemoryReportRepository, ReportRepository, SupabaseReportRepository
from .settings import get_settings

VerificationStatus = Literal["verified", "review", "suspicious", "pending"]
Source = Literal["citizen", "reddit", "weather_api", "news", "simulated"]
Severity = Literal["green", "yellow", "orange", "red"]
settings = get_settings()

SOURCE_RELIABILITY = {"citizen": .68, "reddit": .55, "weather_api": .95, "news": .78, "simulated": .82}
KEYWORDS = {
    "flood": ("flood", "waterlogging", "submerged", "overflow", "inundat"),
    "heatwave": ("heatwave", "heat wave", "sunstroke", "hot", "temperature", "°c"),
    "thunderstorm": ("thunder", "lightning", "storm", "hail"), "rainfall": ("rain", "rainfall", "shower", "downpour", "monsoon"),
    "fog": ("fog", "mist", "visibility"), "dust_storm": ("dust storm", "duststorm", "dust"),
    "strong_wind": ("strong wind", "gale", "windstorm", "gust"),
}
PRECAUTIONS = {"flood": "Move to higher ground, avoid flooded roads, and follow official evacuation instructions.",
 "heatwave": "Stay hydrated, avoid direct sun during peak hours, and check on vulnerable neighbours.",
 "thunderstorm": "Stay indoors, unplug sensitive equipment, and avoid trees and open fields.",
 "rainfall": "Use caution on roads and watch for localised waterlogging.", "fog": "Slow down, use low-beam headlights, and avoid unnecessary travel.",
 "dust_storm": "Remain indoors, close windows, and protect eyes and breathing passages.", "strong_wind": "Secure loose objects and stay away from trees, poles, and construction sites.",
 "unknown": "Monitor official advisories and contact emergency services if at risk."}

class ReportCreate(BaseModel):
    text: str = Field(..., min_length=5, max_length=2000)
    source: Source = "citizen"
    source_id: str | None = Field(default=None, max_length=200)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    location: Location
    timestamp: datetime | None = None
    photo_url: str | None = Field(default=None, max_length=1000)
    video_url: str | None = Field(default=None, max_length=1000)

    @field_validator("location")
    @classmethod
    def valid_coordinates(cls, value: Location) -> Location:
        longitude, latitude = value.coordinates
        if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
            raise ValueError("coordinates must be [longitude, latitude]")
        return value

class StatusUpdate(BaseModel):
    status: VerificationStatus

class SafeZone(BaseModel):
    zone_id: str
    name: str
    city: str
    address: str
    capacity: int = Field(gt=0)
    location: Location

class Alert(BaseModel):
    alert_id: str
    title: str
    event_type: EventType
    city: str
    state: str
    severity: Severity
    active: bool
    report_count: int
    average_confidence: float
    precaution: str
    updated_at: datetime

class IngestionRequest(BaseModel):
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    subreddit: str = Field(default="india", min_length=2, max_length=50)
    query: str | None = Field(default=None, max_length=200)
    limit: int = Field(default=25, ge=1, le=100)

class AdminLogin(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

class CitizenRegister(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=8, max_length=128)

class CitizenLogin(CitizenRegister):
    pass

app = FastAPI(title="MeghVaani Weather Intelligence API", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True,
                   allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["*"])
repository: ReportRepository = (SupabaseReportRepository(settings.supabase_project_url, settings.supabase_service_role_key)
                                 if settings.supabase_enabled else MemoryReportRepository())
citizens: dict[str, str] = {}
bearer = HTTPBearer(auto_error=False)
safe_zones = [SafeZone(zone_id="sz-nashik-01", name="Nashik Municipal Relief Centre", city="Nashik", address="Panchavati", capacity=500, location=Location(coordinates=(73.7898, 20.0059))),
 SafeZone(zone_id="sz-pune-01", name="Pune Disaster Response Centre", city="Pune", address="Shivajinagar", capacity=750, location=Location(coordinates=(73.8567, 18.5204))),
 SafeZone(zone_id="sz-mumbai-01", name="BMC Emergency Shelter", city="Mumbai", address="Kurla West", capacity=600, location=Location(coordinates=(72.8777, 19.076)))]

def classify(text: str) -> tuple[EventType, float]:
    matches = [(event, sum(word in text.lower() for word in words)) for event, words in KEYWORDS.items()]
    event, count = max(matches, key=lambda item: item[1])
    return (event, min(.55 + count * .12, .95)) if count else ("unknown", .25)

def similarity(left: str, right: str) -> float:
    a, b = set(re.findall(r"[a-z0-9]+", left.lower())), set(re.findall(r"[a-z0-9]+", right.lower()))
    return len(a & b) / max(len(a | b), 1)

def make_report(payload: ReportCreate) -> Report:
    event, confidence = classify(payload.text)
    duplicate = next((item for item in repository.list() if item.city.lower() == payload.city.lower() and item.event_type == event and similarity(item.text, payload.text) >= .55), None)
    score = min(1, SOURCE_RELIABILITY[payload.source] * .55 + confidence * .3 + (.12 if duplicate else 0) + .05)
    status: VerificationStatus = "verified" if score >= .85 else "review" if score >= .5 else "suspicious"
    return Report(report_id=str(uuid4()), source=payload.source, source_id=payload.source_id, text=payload.text.strip(),
        timestamp=payload.timestamp or datetime.now(timezone.utc), city=payload.city.strip(), state=payload.state.strip(),
        location=payload.location, event_type=event, classification_confidence=confidence, confidence_score=score,
        verification_status=status, duplicate_of=duplicate.report_id if duplicate else None,
        source_reliability=SOURCE_RELIABILITY[payload.source], photo_url=payload.photo_url, video_url=payload.video_url)

def add_report(payload: ReportCreate) -> Report:
    return repository.add(make_report(payload))

def severity_for(count: int) -> Severity:
    return "red" if count >= 10 else "orange" if count >= 6 else "yellow" if count >= 3 else "green"

def build_alerts() -> list[Alert]:
    groups: dict[tuple[str, EventType], list[Report]] = {}
    for report in repository.list():
        if report.verification_status == "verified":
            groups.setdefault((report.city, report.event_type), []).append(report)
    return [Alert(alert_id=f"alert-{city.lower()}-{event}", title=f"{event.replace('_', ' ').title()} conditions in {city}",
        event_type=event, city=city, state=items[0].state, severity=severity_for(len(items)), active=True, report_count=len(items),
        average_confidence=sum(x.confidence_score for x in items) / len(items), precaution=PRECAUTIONS[event],
        updated_at=max(x.timestamp for x in items)) for (city, event), items in groups.items() if len(items) >= 2]

def seed() -> None:
    for text, city, state, coords, source in [
        ("Heavy rain causing waterlogging near Panchavati roads.", "Nashik", "Maharashtra", (73.7898, 20.0059), "simulated"),
        ("Flood water has submerged the low-lying road near Panchavati.", "Nashik", "Maharashtra", (73.7905, 20.0062), "citizen"),
        ("Thunderstorm and lightning reported across Shivajinagar.", "Pune", "Maharashtra", (73.8567, 18.5204), "news"),
        ("Extreme heat at 44°C; residents advised to stay indoors.", "Mumbai", "Maharashtra", (72.8777, 19.076), "weather_api")]:
        add_report(ReportCreate(text=text, city=city, state=state, location=Location(coordinates=coords), source=source))
if not settings.supabase_enabled:
    seed()

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    iterations = 310000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"

def auth_secret() -> str:
    if not settings.jwt_secret:
        raise HTTPException(503, "Authentication is not configured")
    return settings.jwt_secret

def decode_jwt(token: str) -> dict:
    try:
        header, encoded_payload, encoded_signature = token.split(".", 2)
        signing_input = f"{header}.{encoded_payload}".encode()
        expected = hmac.new(auth_secret().encode(), signing_input, hashlib.sha256).digest()
        signature = base64.urlsafe_b64decode(encoded_signature + "=" * (-len(encoded_signature) % 4))
        if not hmac.compare_digest(signature, expected):
            raise ValueError
        payload = json.loads(base64.urlsafe_b64decode(encoded_payload + "=" * (-len(encoded_payload) % 4)))
        if int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError
        return payload
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(401, "Invalid or expired token")

def require_citizen(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
    if credentials is None:
        raise HTTPException(401, "Citizen authentication required")
    payload = decode_jwt(credentials.credentials)
    if payload.get("role") != "citizen":
        raise HTTPException(403, "Citizen authentication required")
    return str(payload["sub"])

@app.get("/api/health")
def health() -> dict[str, str | int | bool]:
    return {"status": "ok", "service": "meghvaani-backend", "reports": len(repository.list()), "persistence": settings.supabase_enabled}

@app.get("/api/reports", response_model=list[Report])
def list_reports(city: str | None = None, event_type: EventType | None = None, status: VerificationStatus | None = None,
                 limit: int = Query(100, ge=1, le=500)) -> list[Report]:
    result = repository.list()
    if city: result = [x for x in result if x.city.lower() == city.lower()]
    if event_type: result = [x for x in result if x.event_type == event_type]
    if status: result = [x for x in result if x.verification_status == status]
    return sorted(result, key=lambda x: x.timestamp, reverse=True)[:limit]

@app.post("/api/reports", response_model=Report, status_code=201)
def create_report(payload: ReportCreate, _citizen: str = Depends(require_citizen)) -> Report:
    return add_report(payload)

@app.get("/api/stats")
def stats() -> dict:
    items = repository.list()
    return {"total_reports": len(items), "by_status": {s: sum(x.verification_status == s for x in items) for s in ("verified", "review", "suspicious", "pending")},
            "by_event_type": {e: sum(x.event_type == e for x in items) for e in KEYWORDS}, "active_alerts": len(build_alerts())}

@app.get("/api/alerts", response_model=list[Alert])
def alerts() -> list[Alert]: return build_alerts()

@app.get("/api/safe-zones", response_model=list[SafeZone])
def get_safe_zones(city: str | None = None) -> list[SafeZone]:
    return [z for z in safe_zones if not city or z.city.lower() == city.lower()]

@app.get("/api/sources")
def sources() -> list[dict[str, str | float]]: return [{"source": s, "reliability": r, "description": "Configured provider or demo source"} for s, r in SOURCE_RELIABILITY.items()]

@app.post("/api/reports/{report_id}/status", response_model=Report)
def update_status(report_id: str, update: StatusUpdate) -> Report:
    report = next((x for x in repository.list() if x.report_id == report_id), None)
    if not report: raise HTTPException(404, "Report not found")
    report.verification_status = update.status
    return repository.update(report)

@app.post("/api/ingestion/weather")
async def ingest_weather(payload: IngestionRequest) -> dict:
    if not settings.openweather_api_key: raise HTTPException(503, "OpenWeather is not configured")
    params = {"lat": payload.latitude, "lon": payload.longitude, "appid": settings.openweather_api_key, "units": "metric"}
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(settings.openweather_base_url, params=params)
    if response.is_error: raise HTTPException(502, "OpenWeather request failed")
    data = response.json()
    weather = data.get("weather", [{}])[0].get("description", "weather conditions")
    temp = data.get("main", {}).get("temp")
    report = add_report(ReportCreate(text=f"OpenWeather reports {weather} at {temp}°C.", source="weather_api",
        source_id=str(data.get("id", "")), city=payload.city, state=payload.state,
        location=Location(coordinates=(payload.longitude, payload.latitude))))
    return {"provider": "openweather", "report": report, "raw": {"weather": data.get("weather"), "main": data.get("main")}}

@app.get("/api/ingestion/weather/poll")
async def poll_weather(city: str = Query(..., min_length=2, max_length=100),
                        state: str = Query(..., min_length=2, max_length=100),
                        latitude: float = Query(..., ge=-90, le=90),
                        longitude: float = Query(..., ge=-180, le=180)) -> dict:
    """Poll OpenWeather using configured credentials and persist a cross-check report."""
    return await ingest_weather(IngestionRequest(city=city, state=state, latitude=latitude, longitude=longitude))

@app.post("/api/ingestion/reddit")
async def ingest_reddit(payload: IngestionRequest) -> dict:
    if not (settings.reddit_client_id and settings.reddit_client_secret): raise HTTPException(503, "Reddit is not configured")
    auth = httpx.BasicAuth(settings.reddit_client_id, settings.reddit_client_secret)
    async with httpx.AsyncClient(timeout=10, headers={"User-Agent": settings.reddit_user_agent}) as client:
        token_response = await client.post("https://www.reddit.com/api/v1/access_token", data={"grant_type": "client_credentials"}, auth=auth)
        if token_response.is_error: raise HTTPException(502, "Reddit authentication failed")
        token = token_response.json().get("access_token")
        response = await client.get(f"https://oauth.reddit.com/r/{payload.subreddit}/new.json", params={"limit": payload.limit}, headers={"Authorization": f"bearer {token}"})
    if response.is_error: raise HTTPException(502, "Reddit request failed")
    posts = response.json().get("data", {}).get("children", [])
    created = [add_report(ReportCreate(text=p["data"].get("title", ""), source="reddit", source_id=p["data"].get("id"),
        city=payload.city, state=payload.state, location=Location(coordinates=(payload.longitude, payload.latitude))))
        for p in posts if len(p["data"].get("title", "")) >= 5 and (not payload.query or payload.query.lower() in p["data"].get("title", "").lower())]
    return {"provider": "reddit", "ingested": len(created), "reports": created}

@app.post("/api/ingestion/tweetharvest")
async def ingest_tweetharvest(payload: IngestionRequest) -> dict:
    if not settings.tweetharvest_api_url: raise HTTPException(503, "TweetHarvest is not configured")
    headers = {"Accept": "application/json"}
    if settings.tweetharvest_api_key: headers["X-API-Key"] = settings.tweetharvest_api_key
    if settings.tweetharvest_bearer_token: headers["Authorization"] = f"Bearer {settings.tweetharvest_bearer_token}"
    request_body = {"query": payload.query or payload.city, "limit": payload.limit}
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(settings.tweetharvest_api_url, json=request_body, headers=headers)
    if response.is_error: raise HTTPException(502, "TweetHarvest request failed")
    data = response.json()
    posts = data if isinstance(data, list) else data.get("tweets") or data.get("data")
    if not isinstance(posts, list): raise HTTPException(502, "TweetHarvest response must contain a list in data or tweets")
    created = [add_report(ReportCreate(text=str(p.get("text") or p.get("full_text") or ""), source="news",
        source_id=str(p.get("id", "")), city=payload.city, state=payload.state,
        location=Location(coordinates=(payload.longitude, payload.latitude))))
        for p in posts if isinstance(p, dict) and len(str(p.get("text") or p.get("full_text") or "")) >= 5]
    return {"provider": "tweetharvest", "ingested": len(created), "reports": created}

def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256": return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.urlsafe_b64decode(salt), int(iterations))
        return hmac.compare_digest(base64.urlsafe_b64encode(actual).decode(), expected)
    except (ValueError, TypeError, binascii.Error):
        return False

def jwt_token(subject: str, role: str) -> str:
    secret = auth_secret()
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps({"sub": subject, "role": role, "exp": int(time.time()) + 3600}, separators=(",", ":")).encode()).rstrip(b"=").decode()
    signature = hmac.new(secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    return f"{header}.{payload}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"

@app.post("/api/citizens/register")
def citizen_register(credentials: CitizenRegister) -> dict[str, str]:
    email = credentials.email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(422, "A valid email is required")
    auth_secret()
    if email in citizens:
        raise HTTPException(409, "Citizen already registered")
    citizens[email] = hash_password(credentials.password)
    return {"access_token": jwt_token(email, "citizen"), "token_type": "bearer"}

@app.post("/api/citizens/login")
def citizen_login(credentials: CitizenLogin) -> dict[str, str]:
    email = credentials.email.strip().lower()
    if email not in citizens or not verify_password(credentials.password, citizens[email]):
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": jwt_token(email, "citizen"), "token_type": "bearer"}

@app.post("/api/admin/login")
def admin_login(credentials: AdminLogin) -> dict[str, str]:
    if not settings.admin_username or not settings.admin_password_hash: raise HTTPException(503, "Admin login is not configured")
    if not hmac.compare_digest(credentials.username, settings.admin_username) or not verify_password(credentials.password, settings.admin_password_hash):
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": jwt_token(credentials.username, "admin"), "token_type": "bearer"}

@app.get("/api/notifications", response_model=list[Alert])
def notifications() -> list[Alert]:
    """Public notification feed derived from currently active weather alerts."""
    return build_alerts()
