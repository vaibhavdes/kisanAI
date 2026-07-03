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


class CropStage(StrEnum):
    sowing = "sowing"
    germination = "germination"
    vegetative = "vegetative"
    flowering = "flowering"
    harvesting = "harvesting"
    post_harvest = "post_harvest"


class AlertPriority(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class ProviderFeature(StrEnum):
    weather = "weather"
    stt = "stt"
    tts = "tts"
    translation = "translation"
    llm_advisory = "llm_advisory"
    vision_ocr = "vision_ocr"
    satellite = "satellite"
    geocoding_maps = "geocoding_maps"
    whatsapp = "whatsapp"
    sms_voice = "sms_voice"


class ProviderName(StrEnum):
    imd = "imd"
    open_meteo = "open_meteo"
    google_stt = "google_stt"
    sarvam_stt = "sarvam_stt"
    google_tts = "google_tts"
    sarvam_tts = "sarvam_tts"
    google_translate = "google_translate"
    sarvam_translate = "sarvam_translate"
    gemini = "gemini"
    vertex_ai = "vertex_ai"
    gemini_vision = "gemini_vision"
    vertex_ai_vision = "vertex_ai_vision"
    earth_engine = "earth_engine"
    google_maps = "google_maps"
    osm_nominatim = "osm_nominatim"
    authkey = "authkey"
    twilio = "twilio"


class ProviderRoute(BaseModel):
    feature: ProviderFeature
    primary: ProviderName
    secondary: ProviderName | None = None
    allow_fallback: bool = True
    enabled: bool = True
    note: str | None = None


class ProviderConfigResponse(BaseModel):
    routes: list[ProviderRoute]
    updated_at: datetime


class ProviderRouteUpdate(BaseModel):
    primary: ProviderName | None = None
    secondary: ProviderName | None = None
    allow_fallback: bool | None = None
    enabled: bool | None = None
    note: str | None = None


class ProviderConfigUpdate(BaseModel):
    routes: dict[ProviderFeature, ProviderRouteUpdate]


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


class AdvisoryTestRequest(BaseModel):
    farmer_name: str = "Demo farmer"
    language: str = "mr-IN"
    crop: str = "cotton"
    crop_stage: str = "vegetative"
    location: str = "demo village"
    weather_summary: str = "Heavy rain likely in the next 24 hours."
    rainfall_forecast_mm: float = Field(default=45, ge=0)
    soil_moisture: float | None = Field(default=None, ge=0, le=1)


class AdvisoryTestResponse(BaseModel):
    source: str
    model: str
    advisory_text: str
    risk_level: RiskLevel
    recommended_actions: list[str]


class AlertPlan(BaseModel):
    priority: AlertPriority
    channels: list[str]
    reason: str
    call_required: bool = False


class CropStageAdvisoryRequest(BaseModel):
    farmer_id: str
    crop: str
    stage: CropStage
    rainfall_forecast_mm: list[float] = Field(default_factory=list, max_length=10)
    wind_speed_kmph: float | None = Field(default=None, ge=0)
    humidity_percent: float | None = Field(default=None, ge=0, le=100)
    soil_moisture: float | None = Field(default=None, ge=0, le=1)
    disease_risk: RiskLevel | None = None


class CropStageAdvisoryResponse(BaseModel):
    farmer_id: str
    crop: str
    stage: CropStage
    risk_level: RiskLevel
    advice: str
    actions: list[str]
    alert_plan: AlertPlan
    data_used: dict[str, float | str | None]


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


class SoilCardExtractionRequest(BaseModel):
    farmer_id: str | None = None
    image_uri: str | None = None
    extracted_text: str | None = None
    language: str = "en-IN"


class SoilCardExtractionResponse(BaseModel):
    source: str
    ph: float | None = None
    ec: float | None = None
    organic_carbon: float | None = None
    nitrogen: str | float | None = None
    phosphorus: str | float | None = None
    potassium: str | float | None = None
    micronutrients: dict[str, str | float] = Field(default_factory=dict)
    confidence: float = Field(ge=0, le=1)
    needs_manual_review: bool
    raw_text: str | None = None


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


class DatasetReference(BaseModel):
    name: str
    provider: str
    url: str
    use_case: str
    integration_status: str = "planned"


class GovernmentDataContextRequest(BaseModel):
    state: str
    district: str
    crop: str | None = None
    season: str | None = None


class GovernmentDataContextResponse(BaseModel):
    state: str
    district: str
    crop: str | None = None
    rainfall_signal: str
    groundwater_signal: str
    crop_history_signal: str
    recommended_datasets: list[DatasetReference]


class ConversationRole(StrEnum):
    farmer = "farmer"
    assistant = "assistant"
    expert = "expert"
    system = "system"


class ConversationMessage(BaseModel):
    farmer_id: str
    role: ConversationRole
    text: str
    language: str = "hi-IN"
    channel: str = "api"
    intent: str | None = None
    metadata: dict[str, str | float | int | bool | None] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ConversationLogRequest(BaseModel):
    farmer_id: str
    role: ConversationRole = ConversationRole.farmer
    text: str
    language: str = "hi-IN"
    channel: str = "api"
    intent: str | None = None
    metadata: dict[str, str | float | int | bool | None] = Field(default_factory=dict)


class ConversationLogResponse(BaseModel):
    saved: bool
    message: ConversationMessage
