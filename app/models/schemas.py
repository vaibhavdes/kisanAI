from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class WaterAvailability(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class RiskLevel(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class FarmProfile(BaseModel):
    area_acres: float = Field(gt=0)
    soil_type: str = "unknown"
    soil_ph: float | None = Field(default=None, ge=0, le=14)
    groundwater_depth_m: float | None = Field(default=None, ge=0)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class FarmerCreate(BaseModel):
    name: str
    phone: str
    language: str = "hi-IN"
    village: str
    district: str
    state: str
    farm: FarmProfile


class FarmerResponse(FarmerCreate):
    id: str = Field(default_factory=lambda: f"farmer_{uuid4().hex[:10]}")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CropRecommendationRequest(BaseModel):
    farmer_id: str
    season: str = "kharif"
    expected_rainfall_mm: float = Field(ge=0)
    ndvi: float | None = Field(default=None, ge=-1, le=1)
    water_availability: WaterAvailability = WaterAvailability.medium


class CropScore(BaseModel):
    crop: str
    score: int = Field(ge=0, le=100)
    water_fit: str
    soil_fit: str
    reasons: list[str]
    next_action: str


class CropRecommendationResponse(BaseModel):
    farmer_id: str
    language: str
    recommendations: list[CropScore]
    data_sources: dict[str, str | float | None]


class DrySpellAdvisoryRequest(BaseModel):
    farmer_id: str
    crop: str
    soil_moisture: float | None = Field(default=None, ge=0, le=1)
    rainfall_forecast_mm: list[float] = Field(default_factory=list, max_length=10)
    temperature_c: float | None = None
    sensor_id: str | None = None


class DrySpellAdvisoryResponse(BaseModel):
    farmer_id: str
    crop: str
    risk_level: RiskLevel
    dry_days: int
    irrigation_mm: int
    advisory: str
    fertilizer_note: str
    alert_channels: list[str]


class DiagnosisRequest(BaseModel):
    farmer_id: str
    crop: str
    symptoms_text: str | None = None
    voice_transcript: str | None = None
    photo_uri: str | None = None
    language: str | None = None


class DiagnosisResult(BaseModel):
    crop: str
    likely_issue: str
    confidence: float = Field(ge=0, le=1)
    severity: RiskLevel
    immediate_action: str
    needs_expert_followup: bool


class ExpertTicket(BaseModel):
    id: str = Field(default_factory=lambda: f"RSK-{uuid4().hex[:8].upper()}")
    farmer_id: str
    farmer_name: str
    crop: str
    issue: str
    severity: RiskLevel
    assigned_center: str
    status: str = "open"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DiagnosisResponse(DiagnosisResult):
    expert_ticket: ExpertTicket


class VoiceIntakeRequest(BaseModel):
    farmer_id: str
    audio_uri: str | None = None
    transcript: str | None = None
    language: str | None = None


class VoiceIntakeResponse(BaseModel):
    transcript: str
    detected_intent: str
    response_text: str
    response_language: str
    audio_url: str | None = None


class SmsWebhookRequest(BaseModel):
    from_phone: str
    text: str
    language: str = "hi-IN"


class SmsWebhookResponse(BaseModel):
    reply: str
    intent: str
    should_escalate: bool = False


class WhatsAppWebhookRequest(BaseModel):
    from_phone: str
    text: str | None = None
    media_uri: str | None = None
    language: str = "hi-IN"


class WhatsAppWebhookResponse(BaseModel):
    reply: str
    intent: str
    template_name: str | None = None
    should_escalate: bool = False


class VoiceCallWebhookRequest(BaseModel):
    from_phone: str
    call_id: str
    transcript: str | None = None
    language: str = "hi-IN"
    dtmf_digit: str | None = None


class VoiceCallWebhookResponse(BaseModel):
    spoken_reply: str
    intent: str
    next_action: str
    should_escalate: bool = False
