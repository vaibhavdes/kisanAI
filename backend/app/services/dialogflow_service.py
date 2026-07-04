from typing import Any

from app.models.schemas import (
    ConversationLogRequest,
    ConversationRole,
    CropRecommendationRequest,
    DrySpellAdvisoryRequest,
    FarmerIdentifyRequest,
    FarmerResponse,
    WaterAvailability,
)
from app.repositories.store import store
from app.services.channel_intent import detect_farmer_intent
from app.services.conversation_store import ConversationStore
from app.services.recommendation_engine import RecommendationEngine
from app.services.weather_context_service import WeatherProviderUnavailable
from app.services.weather_service import WeatherService
from app.utils.language import phrase


class DialogflowService:
    def handle_webhook(self, payload: dict[str, Any]) -> dict[str, Any]:
        params = self._parameters(payload)
        language = self._language(payload, params)
        text = self._text(payload, params)
        intent = self._intent(payload, text)
        farmer = self._identify_farmer(params, language)

        reply, metadata = self._reply(intent, farmer, params, text, language)
        if farmer:
            self._log_turn(farmer.id, text or intent, reply, language, intent, metadata)

        response_parameters = dict(params)
        response_parameters.update(
            {
                "intent": intent,
                "reply": reply,
                "farmer_id": farmer.id if farmer else None,
                "missing_fields": ",".join(metadata.get("missing_fields", [])),
                "should_escalate": metadata.get("should_escalate", False),
            }
        )
        return {
            "fulfillmentResponse": {
                "messages": [
                    {
                        "text": {
                            "text": [reply],
                        }
                    }
                ],
                "mergeBehavior": "REPLACE",
            },
            "sessionInfo": {
                "parameters": response_parameters,
            },
            "payload": {
                "intent": intent,
                "farmer_id": farmer.id if farmer else None,
                "should_escalate": metadata.get("should_escalate", False),
                "source": "kisan_alert_backend",
            },
        }

    def _reply(
        self,
        intent: str,
        farmer: FarmerResponse | None,
        params: dict[str, Any],
        text: str | None,
        language: str,
    ) -> tuple[str, dict[str, Any]]:
        if intent == "irrigation_advisory":
            return self._irrigation_reply(farmer, params, language)
        if intent == "crop_recommendation":
            return self._crop_recommendation_reply(farmer, params, language)
        if intent == "crop_diagnosis":
            return phrase("sms_photo", language), {"should_escalate": True}
        if intent == "location_update":
            return phrase("sms_location_saved", language), {}
        return phrase("sms_unknown", language), {"text": text}

    def _irrigation_reply(
        self,
        farmer: FarmerResponse | None,
        params: dict[str, Any],
        language: str,
    ) -> tuple[str, dict[str, Any]]:
        crop = str(params.get("crop") or "crop")
        if not farmer:
            return phrase("sms_water", language), {"missing_fields": ["phone"]}
        try:
            advisory = WeatherService().build_dry_spell_advisory(
                farmer,
                DrySpellAdvisoryRequest(
                    farmer_id=farmer.id,
                    crop=crop,
                    rainfall_forecast_mm=self._float_list(params.get("rainfall_forecast_mm")),
                    soil_moisture=self._float(params.get("soil_moisture")),
                    temperature_c=self._float(params.get("temperature_c")),
                ),
            )
            return f"{advisory.advisory} {advisory.fertilizer_note}", {
                "risk_level": advisory.risk_level.value,
                "alert_channels": ",".join(advisory.alert_channels),
            }
        except (ValueError, WeatherProviderUnavailable):
            return phrase("sms_water", language), {"missing_fields": ["crop", "farm_location_or_forecast"]}

    def _crop_recommendation_reply(
        self,
        farmer: FarmerResponse | None,
        params: dict[str, Any],
        language: str,
    ) -> tuple[str, dict[str, Any]]:
        if not farmer:
            return phrase("sms_crop", language), {"missing_fields": ["phone"]}
        try:
            response = RecommendationEngine().recommend(
                farmer=farmer,
                payload=CropRecommendationRequest(
                    farmer_id=farmer.id,
                    season=str(params.get("season") or "kharif"),
                    expected_rainfall_mm=self._float(params.get("expected_rainfall_mm")),
                    month=self._int(params.get("month")),
                    ndvi=self._float(params.get("ndvi")),
                    water_availability=self._water_availability(params.get("water_availability")),
                ),
                ndvi=self._float(params.get("ndvi")),
            )
        except ValueError:
            return phrase("sms_crop", language), {"missing_fields": ["rainfall_or_public_context"]}

        crops = ", ".join(f"{item.crop} ({item.score})" for item in response.recommendations)
        return f"Recommended crops: {crops}.", {"recommendations": crops}

    def _identify_farmer(self, params: dict[str, Any], language: str) -> FarmerResponse | None:
        phone = params.get("phone") or params.get("from_phone") or params.get("mobile")
        if not phone:
            return None
        identity = store.identify_farmer(
            FarmerIdentifyRequest(
                phone=str(phone),
                channel="dialogflow",
                language=language,
                name=self._optional_str(params.get("name")),
                village=self._optional_str(params.get("village")),
                district=self._optional_str(params.get("district")),
                state=self._optional_str(params.get("state")),
                pincode=self._optional_str(params.get("pincode")),
                latitude=self._float(params.get("latitude")),
                longitude=self._float(params.get("longitude")),
            )
        )
        return identity.farmer

    def _log_turn(
        self,
        farmer_id: str,
        text: str,
        reply: str,
        language: str,
        intent: str,
        metadata: dict[str, Any],
    ) -> None:
        ConversationStore().log(
            ConversationLogRequest(
                farmer_id=farmer_id,
                role=ConversationRole.farmer,
                text=text,
                language=language,
                channel="dialogflow",
                intent=intent,
            )
        )
        ConversationStore().log(
            ConversationLogRequest(
                farmer_id=farmer_id,
                role=ConversationRole.assistant,
                text=reply,
                language=language,
                channel="dialogflow",
                intent=intent,
                metadata=self._scalar_metadata(metadata),
            )
        )

    def _intent(self, payload: dict[str, Any], text: str | None) -> str:
        tag = self._nested(payload, "fulfillmentInfo", "tag")
        display_name = self._nested(payload, "intentInfo", "displayName")
        raw_intent = str(tag or display_name or "").strip().lower().replace(" ", "_").replace("-", "_")
        aliases = {
            "water": "irrigation_advisory",
            "irrigation": "irrigation_advisory",
            "irrigation_advisory": "irrigation_advisory",
            "crop": "crop_recommendation",
            "crop_recommendation": "crop_recommendation",
            "recommend_crop": "crop_recommendation",
            "photo": "crop_diagnosis",
            "crop_photo": "crop_diagnosis",
            "crop_diagnosis": "crop_diagnosis",
            "disease": "crop_diagnosis",
            "location": "location_update",
            "location_update": "location_update",
        }
        if raw_intent in aliases:
            return aliases[raw_intent]
        return detect_farmer_intent(text)

    def _parameters(self, payload: dict[str, Any]) -> dict[str, Any]:
        params = self._nested(payload, "sessionInfo", "parameters")
        return params if isinstance(params, dict) else {}

    def _language(self, payload: dict[str, Any], params: dict[str, Any]) -> str:
        return str(params.get("language") or payload.get("languageCode") or "hi-IN")

    def _text(self, payload: dict[str, Any], params: dict[str, Any]) -> str | None:
        for key in ["text", "transcript", "query", "utterance"]:
            value = params.get(key) or payload.get(key)
            if value:
                return str(value)
        return None

    def _water_availability(self, value: Any) -> WaterAvailability:
        normalized = str(value or WaterAvailability.medium.value).lower()
        if normalized in {item.value for item in WaterAvailability}:
            return WaterAvailability(normalized)
        return WaterAvailability.medium

    def _float_list(self, value: Any) -> list[float]:
        if value is None:
            return []
        if isinstance(value, list):
            return [float(item) for item in value if item not in {"", None}]
        return [float(item.strip()) for item in str(value).split(",") if item.strip()]

    def _float(self, value: Any) -> float | None:
        if value in {"", None}:
            return None
        return float(value)

    def _int(self, value: Any) -> int | None:
        if value in {"", None}:
            return None
        return int(value)

    def _optional_str(self, value: Any) -> str | None:
        return str(value) if value not in {"", None} else None

    def _scalar_metadata(self, metadata: dict[str, Any]) -> dict[str, str | float | int | bool | None]:
        scalar: dict[str, str | float | int | bool | None] = {}
        for key, value in metadata.items():
            if isinstance(value, str | float | int | bool) or value is None:
                scalar[key] = value
            elif isinstance(value, list):
                scalar[key] = ",".join(str(item) for item in value)
            else:
                scalar[key] = str(value)
        return scalar

    def _nested(self, payload: dict[str, Any], *keys: str) -> Any:
        current: Any = payload
        for key in keys:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current
