from datetime import UTC, datetime
from functools import lru_cache
from typing import Protocol

from app.core.config import settings
from app.models.schemas import (
    ConversationMessage,
    ExpertTicket,
    FarmProfile,
    FarmerCreate,
    FarmerIdentifyRequest,
    FarmerIdentifyResponse,
    FarmerResponse,
    ProviderFeature,
    ProviderName,
    ProviderRoute,
)
from app.utils.phone import normalize_phone


class AppStore(Protocol):
    provider_routes_updated_at: datetime

    def create_farmer(self, payload: FarmerCreate) -> FarmerResponse: ...

    def identify_farmer(self, payload: FarmerIdentifyRequest) -> FarmerIdentifyResponse: ...

    def get_farmer(self, farmer_id: str) -> FarmerResponse | None: ...

    def list_farmers(self, limit: int = 100) -> list[FarmerResponse]: ...

    def save_ticket(self, ticket: ExpertTicket) -> ExpertTicket: ...

    def list_tickets(self, farmer_id: str) -> list[ExpertTicket]: ...

    def save_conversation_message(self, message: ConversationMessage) -> ConversationMessage: ...

    def list_conversation_messages(self, farmer_id: str, limit: int = 20) -> list[ConversationMessage]: ...

    def list_provider_routes(self) -> list[ProviderRoute]: ...

    def get_provider_route(self, feature: ProviderFeature) -> ProviderRoute: ...

    def save_provider_route(self, route: ProviderRoute) -> ProviderRoute: ...

    def reset(self) -> None: ...


class LocalStore:
    def __init__(self) -> None:
        self.farmers: dict[str, FarmerResponse] = {}
        self.farmer_ids_by_phone: dict[str, str] = {}
        self.tickets: list[ExpertTicket] = []
        self.conversations: list[ConversationMessage] = []
        self.provider_routes: dict[ProviderFeature, ProviderRoute] = default_provider_routes()
        self.provider_routes_updated_at = datetime.now(UTC)

    def create_farmer(self, payload: FarmerCreate) -> FarmerResponse:
        normalized_phone = normalize_phone(payload.phone)
        data = payload.model_dump()
        data["phone"] = normalized_phone
        farmer = FarmerResponse(**data)
        self.farmers[farmer.id] = farmer
        self.farmer_ids_by_phone[normalized_phone] = farmer.id
        return farmer

    def identify_farmer(self, payload: FarmerIdentifyRequest) -> FarmerIdentifyResponse:
        normalized_phone = normalize_phone(payload.phone)
        farmer_id = self.farmer_ids_by_phone.get(normalized_phone)
        is_new = farmer_id is None
        if is_new:
            farmer = FarmerResponse(
                phone=normalized_phone,
                name=payload.name or "Farmer",
                language=payload.language or settings.default_language,
                village=payload.village or payload.pincode or "unknown",
                district=payload.district or "unknown",
                state=payload.state or "unknown",
                farm=FarmProfile(latitude=payload.latitude, longitude=payload.longitude),
            )
        else:
            farmer = self.farmers[farmer_id]
            farmer = self._merge_farmer(farmer, payload)

        self.farmers[farmer.id] = farmer
        self.farmer_ids_by_phone[normalized_phone] = farmer.id
        return FarmerIdentifyResponse(farmer=farmer, is_new=is_new, missing_fields=missing_farmer_fields(farmer))

    def get_farmer(self, farmer_id: str) -> FarmerResponse | None:
        return self.farmers.get(farmer_id)

    def list_farmers(self, limit: int = 100) -> list[FarmerResponse]:
        return list(self.farmers.values())[:limit]

    def save_ticket(self, ticket: ExpertTicket) -> ExpertTicket:
        self.tickets.append(ticket)
        return ticket

    def list_tickets(self, farmer_id: str) -> list[ExpertTicket]:
        return [ticket for ticket in self.tickets if ticket.farmer_id == farmer_id]

    def save_conversation_message(self, message: ConversationMessage) -> ConversationMessage:
        self.conversations.append(message)
        return message

    def list_conversation_messages(self, farmer_id: str, limit: int = 20) -> list[ConversationMessage]:
        messages = [message for message in self.conversations if message.farmer_id == farmer_id]
        return messages[-limit:]

    def list_provider_routes(self) -> list[ProviderRoute]:
        return list(self.provider_routes.values())

    def get_provider_route(self, feature: ProviderFeature) -> ProviderRoute:
        return self.provider_routes[feature]

    def save_provider_route(self, route: ProviderRoute) -> ProviderRoute:
        self.provider_routes[route.feature] = route
        self.provider_routes_updated_at = datetime.now(UTC)
        return route

    def reset(self) -> None:
        self.farmers.clear()
        self.farmer_ids_by_phone.clear()
        self.tickets.clear()
        self.conversations.clear()
        self.provider_routes = default_provider_routes()
        self.provider_routes_updated_at = datetime.now(UTC)

    def _merge_farmer(self, farmer: FarmerResponse, payload: FarmerIdentifyRequest) -> FarmerResponse:
        data = farmer.model_dump()
        for field in ["name", "language", "village", "district", "state"]:
            value = getattr(payload, field)
            if value:
                data[field] = value
        farm = farmer.farm.model_dump()
        if payload.latitude is not None:
            farm["latitude"] = payload.latitude
        if payload.longitude is not None:
            farm["longitude"] = payload.longitude
        data["farm"] = farm
        return FarmerResponse(**data)


class FirestoreStore:
    def __init__(self) -> None:
        from google.cloud import firestore

        self.client = firestore.Client(
            project=settings.google_cloud_project,
            database=settings.firestore_database,
        )
        self.provider_routes_updated_at = datetime.now(UTC)
        self._ensure_default_provider_routes()

    def create_farmer(self, payload: FarmerCreate) -> FarmerResponse:
        normalized_phone = normalize_phone(payload.phone)
        data = payload.model_dump()
        data["phone"] = normalized_phone
        farmer = FarmerResponse(**data)
        self.client.collection("farmers").document(farmer.id).set(farmer.model_dump(mode="json"))
        self.client.collection("farmer_channel_identities").document(normalized_phone).set(
            {"farmer_id": farmer.id, "phone": normalized_phone, "updated_at": datetime.now(UTC).isoformat()}
        )
        return farmer

    def identify_farmer(self, payload: FarmerIdentifyRequest) -> FarmerIdentifyResponse:
        normalized_phone = normalize_phone(payload.phone)
        identity_ref = self.client.collection("farmer_channel_identities").document(normalized_phone)
        identity_doc = identity_ref.get()
        is_new = not identity_doc.exists
        if is_new:
            farmer = FarmerResponse(
                phone=normalized_phone,
                name=payload.name or "Farmer",
                language=payload.language or settings.default_language,
                village=payload.village or payload.pincode or "unknown",
                district=payload.district or "unknown",
                state=payload.state or "unknown",
                farm=FarmProfile(latitude=payload.latitude, longitude=payload.longitude),
            )
        else:
            farmer = self.get_farmer(identity_doc.to_dict()["farmer_id"])
            if farmer is None:
                is_new = True
                farmer = FarmerResponse(
                    phone=normalized_phone,
                    name=payload.name or "Farmer",
                    language=payload.language or settings.default_language,
                    village=payload.village or payload.pincode or "unknown",
                    district=payload.district or "unknown",
                    state=payload.state or "unknown",
                    farm=FarmProfile(latitude=payload.latitude, longitude=payload.longitude),
                )
            else:
                farmer = LocalStore()._merge_farmer(farmer, payload)

        self.client.collection("farmers").document(farmer.id).set(farmer.model_dump(mode="json"), merge=True)
        identity_ref.set(
            {
                "farmer_id": farmer.id,
                "phone": normalized_phone,
                "channel": payload.channel,
                "updated_at": datetime.now(UTC).isoformat(),
            },
            merge=True,
        )
        return FarmerIdentifyResponse(farmer=farmer, is_new=is_new, missing_fields=missing_farmer_fields(farmer))

    def get_farmer(self, farmer_id: str) -> FarmerResponse | None:
        doc = self.client.collection("farmers").document(farmer_id).get()
        return FarmerResponse(**doc.to_dict()) if doc.exists else None

    def list_farmers(self, limit: int = 100) -> list[FarmerResponse]:
        docs = self.client.collection("farmers").limit(limit).stream()
        return [FarmerResponse(**doc.to_dict()) for doc in docs]

    def save_ticket(self, ticket: ExpertTicket) -> ExpertTicket:
        self.client.collection("expert_tickets").document(ticket.id).set(ticket.model_dump(mode="json"))
        return ticket

    def list_tickets(self, farmer_id: str) -> list[ExpertTicket]:
        docs = (
            self.client.collection("expert_tickets")
            .where("farmer_id", "==", farmer_id)
            .order_by("created_at")
            .stream()
        )
        return [ExpertTicket(**doc.to_dict()) for doc in docs]

    def save_conversation_message(self, message: ConversationMessage) -> ConversationMessage:
        doc_id = f"{message.farmer_id}_{message.created_at.timestamp()}"
        self.client.collection("conversation_messages").document(doc_id).set(message.model_dump(mode="json"))
        return message

    def list_conversation_messages(self, farmer_id: str, limit: int = 20) -> list[ConversationMessage]:
        docs = (
            self.client.collection("conversation_messages")
            .where("farmer_id", "==", farmer_id)
            .order_by("created_at", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        return list(reversed([ConversationMessage(**doc.to_dict()) for doc in docs]))

    def list_provider_routes(self) -> list[ProviderRoute]:
        docs = self.client.collection("provider_routes").stream()
        routes = [ProviderRoute(**doc.to_dict()) for doc in docs]
        return routes or list(default_provider_routes().values())

    def get_provider_route(self, feature: ProviderFeature) -> ProviderRoute:
        doc = self.client.collection("provider_routes").document(feature.value).get()
        if doc.exists:
            return ProviderRoute(**doc.to_dict())
        return default_provider_routes()[feature]

    def save_provider_route(self, route: ProviderRoute) -> ProviderRoute:
        self.client.collection("provider_routes").document(route.feature.value).set(route.model_dump(mode="json"))
        self.provider_routes_updated_at = datetime.now(UTC)
        self.client.collection("system_state").document("provider_routes").set(
            {"updated_at": self.provider_routes_updated_at.isoformat()},
            merge=True,
        )
        return route

    def reset(self) -> None:
        raise RuntimeError("Firestore reset is intentionally disabled")

    def _ensure_default_provider_routes(self) -> None:
        for feature, route in default_provider_routes().items():
            ref = self.client.collection("provider_routes").document(feature.value)
            if not ref.get().exists:
                ref.set(route.model_dump(mode="json"))


def missing_farmer_fields(farmer: FarmerResponse) -> list[str]:
    missing: list[str] = []
    for field in ["village", "district", "state"]:
        if getattr(farmer, field) in {"", "unknown", None}:
            missing.append(field)
    if farmer.farm.latitude is None or farmer.farm.longitude is None:
        missing.append("farm_location")
    if farmer.farm.soil_type == "unknown" and farmer.farm.soil_ph is None:
        missing.append("soil")
    return missing


def default_provider_routes() -> dict[ProviderFeature, ProviderRoute]:
    routes = [
        ProviderRoute(
            feature=ProviderFeature.weather,
            primary=ProviderName.imd,
            secondary=ProviderName.open_meteo,
            note="Use IMD/government weather first; Open-Meteo only as free fallback.",
        ),
        ProviderRoute(feature=ProviderFeature.stt, primary=ProviderName.google_stt, secondary=ProviderName.sarvam_stt),
        ProviderRoute(feature=ProviderFeature.tts, primary=ProviderName.google_tts, secondary=ProviderName.sarvam_tts),
        ProviderRoute(
            feature=ProviderFeature.translation,
            primary=ProviderName.google_translate,
            secondary=ProviderName.sarvam_translate,
            note="Prefer cheaper cached translation; use Gemini only inside advisory generation when needed.",
        ),
        ProviderRoute(
            feature=ProviderFeature.llm_advisory,
            primary=ProviderName.vertex_ai,
            secondary=ProviderName.gemini,
            note="Prefer Vertex AI Gemini for hackathon credits; Gemini API remains fallback.",
        ),
        ProviderRoute(
            feature=ProviderFeature.vision_ocr,
            primary=ProviderName.vertex_ai_vision,
            secondary=ProviderName.gemini_vision,
            note="Prefer Vertex AI Vision for hackathon credits; Gemini Vision remains fallback.",
        ),
        ProviderRoute(
            feature=ProviderFeature.satellite,
            primary=ProviderName.earth_engine,
            secondary=None,
            allow_fallback=False,
            note="No alternate satellite provider fallback; original Earth Engine satellite data is required.",
        ),
        ProviderRoute(
            feature=ProviderFeature.geocoding_maps,
            primary=ProviderName.google_maps,
            secondary=ProviderName.osm_nominatim,
        ),
        ProviderRoute(feature=ProviderFeature.whatsapp, primary=ProviderName.authkey, secondary=ProviderName.twilio),
        ProviderRoute(feature=ProviderFeature.sms_voice, primary=ProviderName.authkey, secondary=ProviderName.twilio),
    ]
    return {route.feature: route for route in routes}


@lru_cache
def get_store() -> AppStore:
    if settings.data_store_provider == "firestore":
        return FirestoreStore()
    return LocalStore()


store = get_store()
