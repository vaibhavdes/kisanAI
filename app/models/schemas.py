from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
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
    area_acres: float = Field(default=1, gt=0)
    soil_type: str = "unknown"
    soil_ph: float | None = Field(default=None, ge=0, le=14)
    groundwater_depth_m: float | None = Field(default=None, ge=0)
    soil_ec: float | None = Field(default=None, ge=0)
    organic_carbon: float | None = Field(default=None, ge=0)
    soil_nitrogen: str | float | None = None
    soil_phosphorus: str | float | None = None
    soil_potassium: str | float | None = None
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


class FarmerIdentifyRequest(BaseModel):
    phone: str
    channel: str = "whatsapp"
    language: str | None = None
    name: str | None = None
    village: str | None = None
    district: str | None = None
    state: str | None = None
    pincode: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class FarmerIdentifyResponse(BaseModel):
    farmer: FarmerResponse
    is_new: bool
    missing_fields: list[str]


class CropRecommendationRequest(BaseModel):
    farmer_id: str
    season: str = "kharif"
    expected_rainfall_mm: float | None = Field(default=None, ge=0)
    month: int | None = Field(default=None, ge=1, le=12)
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
    data_sources: dict[str, str | float | int | bool | None]


class FarmCoordinate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class SatelliteSignalRequest(BaseModel):
    farmer_id: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    polygon: list[FarmCoordinate] | None = None
    buffer_m: int = Field(default=250, ge=20, le=2000)
    days: int = Field(default=90, ge=15, le=365)
    history_periods: int = Field(default=3, ge=1, le=12)


class SatelliteHistoryPoint(BaseModel):
    start_date: str
    end_date: str
    ndvi: float | None = None
    ndwi: float | None = None
    ndmi: float | None = None
    evi: float | None = None
    ndre: float | None = None
    water_stress: str | None = None


class SatelliteSignalResponse(BaseModel):
    farmer_id: str | None = None
    latitude: float
    longitude: float
    geometry_type: str
    buffer_m: int | None = None
    start_date: str
    end_date: str
    source: str
    ndvi: float | None = None
    ndwi: float | None = None
    ndmi: float | None = None
    evi: float | None = None
    ndre: float | None = None
    water_stress: str
    vegetation_status: str
    moisture_status: str
    chlorophyll_status: str
    history: list[SatelliteHistoryPoint] = Field(default_factory=list)
    note: str


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
    weather_source: str | None = None
    weather_fallback_used: bool = False
    satellite_source: str | None = None
    satellite_water_stress: str | None = None
    satellite_ndwi: float | None = None
    satellite_ndmi: float | None = None
    ai_source: str | None = None
    ai_model: str | None = None


class WeatherDailyForecast(BaseModel):
    date: str
    rainfall_mm: float | None = None
    rainfall_probability_percent: float | None = None
    temperature_max_c: float | None = None
    temperature_min_c: float | None = None
    wind_speed_max_kmph: float | None = None
    evapotranspiration_mm: float | None = None


class WeatherProviderStatus(BaseModel):
    provider: ProviderName
    attempted: bool
    success: bool
    error: str | None = None


class WeatherContextRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    days: int = Field(default=7, ge=1, le=16)
    include_hourly_soil: bool = True


class WeatherContextResponse(BaseModel):
    latitude: float
    longitude: float
    source: ProviderName
    fallback_used: bool
    provider_statuses: list[WeatherProviderStatus]
    current_temperature_c: float | None = None
    current_humidity_percent: float | None = None
    current_wind_speed_kmph: float | None = None
    current_precipitation_mm: float | None = None
    current_weather_code: int | None = None
    soil_moisture: float | None = None
    soil_temperature_c: float | None = None
    daily: list[WeatherDailyForecast]
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


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


class AlertDeliveryRequest(BaseModel):
    farmer_id: str
    message: str = Field(min_length=1, max_length=1000)
    alert_plan: AlertPlan
    language: str | None = None
    media_url: str | None = None
    media_file_name: str | None = None


class ChannelDeliveryResult(BaseModel):
    channel: str
    provider: str | None = None
    operation: str | None = None
    status: str
    sent: bool = False
    dry_run: bool = False
    provider_message_id: str | None = None
    attempt_count: int = 1
    retryable: bool = False
    raw_status: str | None = None
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    error: str | None = None


class AlertDeliveryResponse(BaseModel):
    farmer_id: str
    priority: AlertPriority
    message: str
    results: list[ChannelDeliveryResult]
    overall_status: str


class ChannelReceiptRequest(BaseModel):
    provider: str = "authkey"
    channel: str
    provider_message_id: str | None = None
    message_id: str | None = None
    phone: str | None = None
    status: str
    event_type: str = "delivery_receipt"
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class ChannelDeliveryReceipt(BaseModel):
    id: str = Field(default_factory=lambda: f"receipt_{uuid4().hex[:10]}")
    provider: str
    channel: str
    provider_message_id: str | None = None
    message_id: str | None = None
    phone: str | None = None
    status: str
    normalized_status: str
    event_type: str
    retryable: bool = False
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    received_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ChannelReceiptResponse(BaseModel):
    saved: bool
    receipt: ChannelDeliveryReceipt


class ProactiveAlertRunRequest(BaseModel):
    farmer_ids: list[str] | None = None
    crop: str = "crop"
    min_priority: AlertPriority = AlertPriority.medium
    rainfall_forecast_mm: list[float] = Field(default_factory=list, max_length=10)
    soil_moisture: float | None = Field(default=None, ge=0, le=1)
    temperature_c: float | None = None
    max_farmers: int = Field(default=100, ge=1, le=500)
    run_date: str | None = None
    idempotency_key: str | None = None
    dedupe: bool = True


class ProactiveAlertFarmerResult(BaseModel):
    farmer_id: str
    generated: bool
    skipped_reason: str | None = None
    risk_level: RiskLevel | None = None
    priority: AlertPriority | None = None
    advisory: str | None = None
    delivery: AlertDeliveryResponse | None = None


class ProactiveAlertRunResponse(BaseModel):
    processed: int
    generated: int
    skipped: int
    delivered: int
    run_date: str
    idempotency_key: str
    results: list[ProactiveAlertFarmerResult]


class AlertRunRecord(BaseModel):
    key: str
    farmer_id: str
    crop: str
    run_date: str
    risk_level: RiskLevel
    priority: AlertPriority
    message: str
    delivery_status: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PubSubMessage(BaseModel):
    data: str | None = None
    messageId: str | None = None
    publishTime: str | None = None
    attributes: dict[str, str] = Field(default_factory=dict)


class PubSubPushRequest(BaseModel):
    message: PubSubMessage
    subscription: str | None = None


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
    ai_source: str | None = None
    ai_model: str | None = None


class DiagnosisRequest(BaseModel):
    farmer_id: str
    crop: str
    symptoms_text: str | None = None
    voice_transcript: str | None = None
    photo_uri: str | None = None
    image_base64: str | None = None
    mime_type: str = "image/jpeg"
    language: str | None = None


class DiagnosisResult(BaseModel):
    crop: str
    likely_issue: str
    confidence: float = Field(ge=0, le=1)
    severity: RiskLevel
    immediate_action: str
    needs_expert_followup: bool
    source: str | None = None
    model: str | None = None


class ExpertTicket(BaseModel):
    id: str = Field(default_factory=lambda: f"RSK-{uuid4().hex[:8].upper()}")
    farmer_id: str
    farmer_name: str
    farmer_phone: str | None = None
    district: str | None = None
    crop: str
    issue: str
    severity: RiskLevel
    assigned_center: str
    assigned_expert: str | None = None
    expert_notes: list[str] = Field(default_factory=list)
    farmer_notification: str | None = None
    status: str = "open"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ExpertTicketUpdateRequest(BaseModel):
    status: str | None = None
    assigned_expert: str | None = None
    expert_note: str | None = None
    notify_farmer: bool = True
    farmer_message: str | None = None


class DiagnosisResponse(DiagnosisResult):
    expert_ticket: ExpertTicket


class SoilCardExtractionRequest(BaseModel):
    farmer_id: str | None = None
    image_uri: str | None = None
    image_base64: str | None = None
    mime_type: str = "image/jpeg"
    extracted_text: str | None = None
    language: str = "en-IN"


class SoilCardExtractionResponse(BaseModel):
    source: str
    model: str | None = None
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
    persisted: bool = False
    farmer: FarmerResponse | None = None


class VoiceIntakeRequest(BaseModel):
    farmer_id: str
    audio_uri: str | None = None
    audio_base64: str | None = None
    transcript: str | None = None
    language: str | None = None


class VoiceIntakeResponse(BaseModel):
    transcript: str
    detected_intent: str
    response_text: str
    response_language: str
    audio_url: str | None = None
    stt_provider: str | None = None
    tts_provider: str | None = None
    response_audio_base64: str | None = None
    response_audio_content_type: str | None = None


class VoiceTranscribeRequest(BaseModel):
    farmer_id: str | None = None
    audio_base64: str | None = None
    audio_uri: str | None = None
    language: str | None = None
    audio_encoding: str = "LINEAR16"
    content_type: str = "audio/wav"
    sample_rate_hertz: int = Field(default=16000, ge=8000, le=48000)


class VoiceTranscribeResponse(BaseModel):
    transcript: str
    language: str | None = None
    provider: str
    confidence: float | None = Field(default=None, ge=0, le=1)


class VoiceSpeakRequest(BaseModel):
    farmer_id: str | None = None
    text: str
    language: str = "hi-IN"
    audio_encoding: str = "MP3"


class VoiceSpeakResponse(BaseModel):
    audio_base64: str
    provider: str
    audio_encoding: str
    content_type: str


class TranslateTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    target_language: str
    source_language: str | None = None
    mime_type: str = "text/plain"


class TranslateTextResponse(BaseModel):
    translated_text: str
    source_language: str | None = None
    target_language: str
    provider: str


class DetectLanguageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class DetectLanguageResponse(BaseModel):
    language: str | None = None
    script: str | None = None
    provider: str
    confidence: float | None = Field(default=None, ge=0, le=1)


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
    message_id: str | None = None
    text: str | None = None
    media_uri: str | None = None
    media_base64: str | None = None
    media_mime_type: str | None = None
    media_type: str | None = None
    audio_uri: str | None = None
    audio_base64: str | None = None
    audio_mime_type: str = "audio/ogg"
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    location_label: str | None = None
    language: str | None = None


class WhatsAppWebhookResponse(BaseModel):
    reply: str
    intent: str
    template_name: str | None = None
    should_escalate: bool = False
    farmer_id: str | None = None
    detected_language: str | None = None
    transcript: str | None = None
    response_audio_base64: str | None = None
    response_audio_content_type: str | None = None
    outbound_provider: str | None = None
    delivery_status: str = "not_sent"
    missing_fields: list[str] = Field(default_factory=list)


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
    month: int | None = Field(default=None, ge=1, le=12)


class DataSignal(BaseModel):
    available: bool
    source: str
    value: str | float | int | None = None
    unit: str | None = None
    note: str | None = None
    metadata: dict[str, str | float | int | None] = Field(default_factory=dict)


class GovernmentDataContextResponse(BaseModel):
    state: str
    district: str
    crop: str | None = None
    rainfall_normal: DataSignal
    groundwater: DataSignal
    soil_health: DataSignal
    crop_history: DataSignal
    agromet_advisory: DataSignal
    recommended_datasets: list[DatasetReference]
    missing_sources: list[str] = Field(default_factory=list)


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
