"""Shared model types kept separate so the repository does not import the app."""

from typing import Literal
from datetime import datetime
from pydantic import BaseModel, Field

Source = Literal["citizen", "reddit", "weather_api", "news", "simulated"]
EventType = Literal["rainfall", "thunderstorm", "flood", "heatwave", "fog", "dust_storm", "strong_wind", "unknown"]
VerificationStatus = Literal["verified", "review", "suspicious", "pending"]


class Location(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float] = Field(..., description="[longitude, latitude]")


class Report(BaseModel):
    report_id: str
    source: Source
    source_id: str | None = None
    text: str
    timestamp: datetime
    city: str
    state: str
    location: Location
    event_type: EventType
    classification_confidence: float = Field(ge=0, le=1)
    confidence_score: float = Field(ge=0, le=1)
    verification_status: VerificationStatus
    duplicate_of: str | None = None
    source_reliability: float = Field(ge=0, le=1)
    photo_url: str | None = None
    video_url: str | None = None
