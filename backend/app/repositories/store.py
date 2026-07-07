from datetime import UTC, datetime
from functools import lru_cache
from typing import Protocol

from app.core.config import settings
from app.models.schemas import (
    AlertRunRecord,
    AlertScheduleConfig,
    ChannelDeliveryReceipt,
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
    SensorReading,
    ServiceAuditLog,
)
from app.utils.phone import normalize_phone


class AppStore(Protocol):
    provider_routes_updated_at: datetime

    def create_farmer(self, payload: FarmerCreate) -> FarmerResponse: ...

    def identify_farmer(self, payload: FarmerIdentifyRequest) -> FarmerIdentifyResponse: ...

    def get_farmer(self, farmer_id: str) -> FarmerResponse | None: ...

    def get_farmer_by_phone(self, phone: str) -> FarmerResponse | None: ...

    def save_farmer(self, farmer: FarmerResponse) -> FarmerResponse: ...

    def delete_farmer(self, farmer_id: str) -> bool: ...

    def list_farmers(self, limit: int = 100) -> list[FarmerResponse]: ...

    def save_ticket(self, ticket: ExpertTicket) -> ExpertTicket: ...

    def get_ticket(self, ticket_id: str) -> ExpertTicket | None: ...

    def list_tickets(self, farmer_id: str) -> list[ExpertTicket]: ...

    def save_conversation_message(self, message: ConversationMessage) -> ConversationMessage: ...

    def list_conversation_messages(self, farmer_id: str, limit: int = 20) -> list[ConversationMessage]: ...

    def save_delivery_receipt(self, receipt: ChannelDeliveryReceipt) -> ChannelDeliveryReceipt: ...

    def list_delivery_receipts(self, limit: int = 100) -> list[ChannelDeliveryReceipt]: ...

    def save_sensor_reading(self, reading: SensorReading) -> SensorReading: ...

    def latest_sensor_reading(self, farmer_id: str, sensor_id: str | None = None) -> SensorReading | None: ...

    def list_sensor_readings(self, farmer_id: str, limit: int = 20) -> list[SensorReading]: ...

    def save_alert_run_record(self, record: AlertRunRecord) -> AlertRunRecord: ...

    def get_alert_run_record(self, key: str) -> AlertRunRecord | None: ...

    def get_alert_schedule_config(self) -> AlertScheduleConfig: ...

    def save_alert_schedule_config(self, config: AlertScheduleConfig) -> AlertScheduleConfig: ...

    def list_provider_routes(self) -> list[ProviderRoute]: ...

    def get_provider_route(self, feature: ProviderFeature) -> ProviderRoute: ...

    def save_provider_route(self, route: ProviderRoute) -> ProviderRoute: ...

    def save_service_audit_log(self, log: ServiceAuditLog) -> ServiceAuditLog: ...

    def list_service_audit_logs(self, limit: int = 100, farmer_id: str | None = None) -> list[ServiceAuditLog]: ...

    def reset(self) -> None: ...


class LocalStore:
    def __init__(self) -> None:
        self.farmers: dict[str, FarmerResponse] = {}
        self.farmer_ids_by_phone: dict[str, str] = {}
        self.tickets: list[ExpertTicket] = []
        self.conversations: list[ConversationMessage] = []
        self.delivery_receipts: list[ChannelDeliveryReceipt] = []
        self.sensor_readings: list[SensorReading] = []
        self.service_audit_logs: list[ServiceAuditLog] = []
        self.alert_run_records: dict[str, AlertRunRecord] = {}
        self.alert_schedule_config = AlertScheduleConfig()
        self.provider_routes: dict[ProviderFeature, ProviderRoute] = default_provider_routes()
        self.provider_routes_updated_at = datetime.now(UTC)

    def create_farmer(self, payload: FarmerCreate) -> FarmerResponse:
        normalized_phone = normalize_phone(payload.phone)
        existing_id = self.farmer_ids_by_phone.get(normalized_phone)
        if existing_id and existing_id in self.farmers:
            farmer = merge_farmer_create_payload(self.farmers[existing_id], payload, normalized_phone)
            self.farmers[farmer.id] = farmer
            return farmer

        farmer = farmer_from_create_payload(payload, normalized_phone)
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
                taluka=payload.taluka,
                district=payload.district or "unknown",
                state=payload.state or "unknown",
                pincode=payload.pincode,
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

    def get_farmer_by_phone(self, phone: str) -> FarmerResponse | None:
        farmer_id = self.farmer_ids_by_phone.get(normalize_phone(phone))
        return self.get_farmer(farmer_id) if farmer_id else None

    def save_farmer(self, farmer: FarmerResponse) -> FarmerResponse:
        self.farmers[farmer.id] = farmer
        self.farmer_ids_by_phone[normalize_phone(farmer.phone)] = farmer.id
        return farmer

    def delete_farmer(self, farmer_id: str) -> bool:
        farmer = self.farmers.pop(farmer_id, None)
        if farmer is None:
            return False
        normalized_phone = normalize_phone(farmer.phone)
        if self.farmer_ids_by_phone.get(normalized_phone) == farmer_id:
            del self.farmer_ids_by_phone[normalized_phone]
        self.tickets = [ticket for ticket in self.tickets if ticket.farmer_id != farmer_id]
        self.conversations = [message for message in self.conversations if message.farmer_id != farmer_id]
        self.sensor_readings = [reading for reading in self.sensor_readings if reading.farmer_id != farmer_id]
        self.service_audit_logs = [log for log in self.service_audit_logs if log.farmer_id != farmer_id]
        self.alert_run_records = {
            key: record for key, record in self.alert_run_records.items() if record.farmer_id != farmer_id
        }
        return True

    def list_farmers(self, limit: int = 100) -> list[FarmerResponse]:
        return list(self.farmers.values())[:limit]

    def save_ticket(self, ticket: ExpertTicket) -> ExpertTicket:
        self.tickets = [existing for existing in self.tickets if existing.id != ticket.id]
        self.tickets.append(ticket)
        return ticket

    def get_ticket(self, ticket_id: str) -> ExpertTicket | None:
        return next((ticket for ticket in self.tickets if ticket.id == ticket_id), None)

    def list_tickets(self, farmer_id: str) -> list[ExpertTicket]:
        return [ticket for ticket in self.tickets if ticket.farmer_id == farmer_id]

    def save_conversation_message(self, message: ConversationMessage) -> ConversationMessage:
        self.conversations.append(message)
        return message

    def list_conversation_messages(self, farmer_id: str, limit: int = 20) -> list[ConversationMessage]:
        messages = [message for message in self.conversations if message.farmer_id == farmer_id]
        return messages[-limit:]

    def save_delivery_receipt(self, receipt: ChannelDeliveryReceipt) -> ChannelDeliveryReceipt:
        self.delivery_receipts.append(receipt)
        return receipt

    def list_delivery_receipts(self, limit: int = 100) -> list[ChannelDeliveryReceipt]:
        return self.delivery_receipts[-limit:]

    def save_sensor_reading(self, reading: SensorReading) -> SensorReading:
        self.sensor_readings = [existing for existing in self.sensor_readings if existing.id != reading.id]
        self.sensor_readings.append(reading)
        return reading

    def latest_sensor_reading(self, farmer_id: str, sensor_id: str | None = None) -> SensorReading | None:
        readings = [
            reading
            for reading in self.sensor_readings
            if reading.farmer_id == farmer_id and (sensor_id is None or reading.sensor_id == sensor_id)
        ]
        return max(readings, key=lambda reading: reading.timestamp, default=None)

    def list_sensor_readings(self, farmer_id: str, limit: int = 20) -> list[SensorReading]:
        readings = [reading for reading in self.sensor_readings if reading.farmer_id == farmer_id]
        return sorted(readings, key=lambda reading: reading.timestamp)[-limit:]

    def save_service_audit_log(self, log: ServiceAuditLog) -> ServiceAuditLog:
        self.service_audit_logs.append(log)
        return log

    def list_service_audit_logs(self, limit: int = 100, farmer_id: str | None = None) -> list[ServiceAuditLog]:
        logs = [log for log in self.service_audit_logs if not farmer_id or log.farmer_id == farmer_id]
        return logs[-limit:]

    def save_alert_run_record(self, record: AlertRunRecord) -> AlertRunRecord:
        self.alert_run_records[record.key] = record
        return record

    def get_alert_run_record(self, key: str) -> AlertRunRecord | None:
        return self.alert_run_records.get(key)

    def get_alert_schedule_config(self) -> AlertScheduleConfig:
        return self.alert_schedule_config

    def save_alert_schedule_config(self, config: AlertScheduleConfig) -> AlertScheduleConfig:
        self.alert_schedule_config = config
        return config

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
        self.delivery_receipts.clear()
        self.sensor_readings.clear()
        self.service_audit_logs.clear()
        self.alert_run_records.clear()
        self.alert_schedule_config = AlertScheduleConfig()
        self.provider_routes = default_provider_routes()
        self.provider_routes_updated_at = datetime.now(UTC)

    def _merge_farmer(self, farmer: FarmerResponse, payload: FarmerIdentifyRequest) -> FarmerResponse:
        data = farmer.model_dump()
        for field in ["name", "language", "village", "taluka", "district", "state", "pincode"]:
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
        identity_ref = self.client.collection("farmer_channel_identities").document(normalized_phone)
        identity_doc = identity_ref.get()
        if identity_doc.exists:
            farmer_id = identity_doc.to_dict().get("farmer_id")
            existing = self.get_farmer(farmer_id) if farmer_id else None
            if existing is not None:
                farmer = merge_farmer_create_payload(existing, payload, normalized_phone)
                self.client.collection("farmers").document(farmer.id).set(farmer.model_dump(mode="json"), merge=True)
                identity_ref.set(
                    {"farmer_id": farmer.id, "phone": normalized_phone, "updated_at": datetime.now(UTC).isoformat()},
                    merge=True,
                )
                return farmer

        existing = self._find_farmer_by_normalized_phone(normalized_phone)
        if existing is not None:
            farmer = merge_farmer_create_payload(existing, payload, normalized_phone)
            self.client.collection("farmers").document(farmer.id).set(farmer.model_dump(mode="json"), merge=True)
            identity_ref.set(
                {"farmer_id": farmer.id, "phone": normalized_phone, "updated_at": datetime.now(UTC).isoformat()},
                merge=True,
            )
            return farmer

        farmer = farmer_from_create_payload(payload, normalized_phone)
        self.client.collection("farmers").document(farmer.id).set(farmer.model_dump(mode="json"))
        identity_ref.set(
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
                taluka=payload.taluka,
                district=payload.district or "unknown",
                state=payload.state or "unknown",
                pincode=payload.pincode,
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
                    taluka=payload.taluka,
                    district=payload.district or "unknown",
                    state=payload.state or "unknown",
                    pincode=payload.pincode,
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

    def get_farmer_by_phone(self, phone: str) -> FarmerResponse | None:
        normalized_phone = normalize_phone(phone)
        identity_doc = self.client.collection("farmer_channel_identities").document(normalized_phone).get()
        if not identity_doc.exists:
            return None
        farmer_id = identity_doc.to_dict().get("farmer_id")
        return self.get_farmer(farmer_id) if farmer_id else None

    def save_farmer(self, farmer: FarmerResponse) -> FarmerResponse:
        normalized_phone = normalize_phone(farmer.phone)
        self.client.collection("farmers").document(farmer.id).set(farmer.model_dump(mode="json"), merge=True)
        self.client.collection("farmer_channel_identities").document(normalized_phone).set(
            {
                "farmer_id": farmer.id,
                "phone": normalized_phone,
                "updated_at": datetime.now(UTC).isoformat(),
            },
            merge=True,
        )
        return farmer

    def delete_farmer(self, farmer_id: str) -> bool:
        farmer = self.get_farmer(farmer_id)
        if farmer is None:
            return False

        self.client.collection("farmers").document(farmer_id).delete()
        identity_ref = self.client.collection("farmer_channel_identities").document(normalize_phone(farmer.phone))
        identity_doc = identity_ref.get()
        if identity_doc.exists and identity_doc.to_dict().get("farmer_id") == farmer_id:
            identity_ref.delete()

        for collection_name in [
            "expert_tickets",
            "conversation_messages",
            "sensor_readings",
            "service_audit_logs",
            "alert_run_records",
        ]:
            self._delete_farmer_scoped_documents(collection_name, farmer_id)
        return True

    def list_farmers(self, limit: int = 100) -> list[FarmerResponse]:
        docs = self.client.collection("farmers").limit(limit).stream()
        return [FarmerResponse(**doc.to_dict()) for doc in docs]

    def save_ticket(self, ticket: ExpertTicket) -> ExpertTicket:
        self.client.collection("expert_tickets").document(ticket.id).set(ticket.model_dump(mode="json"))
        return ticket

    def get_ticket(self, ticket_id: str) -> ExpertTicket | None:
        doc = self.client.collection("expert_tickets").document(ticket_id).get()
        return ExpertTicket(**doc.to_dict()) if doc.exists else None

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

    def save_delivery_receipt(self, receipt: ChannelDeliveryReceipt) -> ChannelDeliveryReceipt:
        self.client.collection("channel_delivery_receipts").document(receipt.id).set(receipt.model_dump(mode="json"))
        return receipt

    def list_delivery_receipts(self, limit: int = 100) -> list[ChannelDeliveryReceipt]:
        docs = (
            self.client.collection("channel_delivery_receipts")
            .order_by("received_at", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        return list(reversed([ChannelDeliveryReceipt(**doc.to_dict()) for doc in docs]))

    def save_sensor_reading(self, reading: SensorReading) -> SensorReading:
        self.client.collection("sensor_readings").document(reading.id).set(reading.model_dump(mode="json"))
        return reading

    def latest_sensor_reading(self, farmer_id: str, sensor_id: str | None = None) -> SensorReading | None:
        readings = self.list_sensor_readings(farmer_id, limit=100)
        if sensor_id:
            readings = [reading for reading in readings if reading.sensor_id == sensor_id]
        return max(readings, key=lambda reading: reading.timestamp, default=None)

    def list_sensor_readings(self, farmer_id: str, limit: int = 20) -> list[SensorReading]:
        docs = self.client.collection("sensor_readings").where("farmer_id", "==", farmer_id).stream()
        readings = [SensorReading(**doc.to_dict()) for doc in docs]
        return sorted(readings, key=lambda reading: reading.timestamp)[-limit:]

    def save_service_audit_log(self, log: ServiceAuditLog) -> ServiceAuditLog:
        self.client.collection("service_audit_logs").document(log.id).set(log.model_dump(mode="json"))
        return log

    def list_service_audit_logs(self, limit: int = 100, farmer_id: str | None = None) -> list[ServiceAuditLog]:
        query = self.client.collection("service_audit_logs").order_by("created_at", direction="DESCENDING").limit(limit)
        if farmer_id:
            query = (
                self.client.collection("service_audit_logs")
                .where("farmer_id", "==", farmer_id)
                .order_by("created_at", direction="DESCENDING")
                .limit(limit)
            )
        return list(reversed([ServiceAuditLog(**doc.to_dict()) for doc in query.stream()]))

    def save_alert_run_record(self, record: AlertRunRecord) -> AlertRunRecord:
        self.client.collection("alert_run_records").document(record.key).set(record.model_dump(mode="json"))
        return record

    def get_alert_run_record(self, key: str) -> AlertRunRecord | None:
        doc = self.client.collection("alert_run_records").document(key).get()
        return AlertRunRecord(**doc.to_dict()) if doc.exists else None

    def get_alert_schedule_config(self) -> AlertScheduleConfig:
        doc = self.client.collection("system_state").document("alert_schedule").get()
        if doc.exists:
            return AlertScheduleConfig(**doc.to_dict())
        config = AlertScheduleConfig()
        self.save_alert_schedule_config(config)
        return config

    def save_alert_schedule_config(self, config: AlertScheduleConfig) -> AlertScheduleConfig:
        self.client.collection("system_state").document("alert_schedule").set(config.model_dump(mode="json"))
        return config

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

    def _find_farmer_by_normalized_phone(self, normalized_phone: str) -> FarmerResponse | None:
        docs = self.client.collection("farmers").where("phone", "==", normalized_phone).limit(1).stream()
        for doc in docs:
            return FarmerResponse(**doc.to_dict())
        return None

    def _delete_farmer_scoped_documents(self, collection_name: str, farmer_id: str) -> None:
        docs = self.client.collection(collection_name).where("farmer_id", "==", farmer_id).stream()
        for doc in docs:
            doc.reference.delete()


def farmer_from_create_payload(payload: FarmerCreate, normalized_phone: str) -> FarmerResponse:
    data = payload.model_dump()
    data["phone"] = normalized_phone
    return FarmerResponse(**data)


def merge_farmer_create_payload(
    farmer: FarmerResponse,
    payload: FarmerCreate,
    normalized_phone: str,
) -> FarmerResponse:
    data = farmer.model_dump()
    incoming = payload.model_dump(exclude_unset=True)
    incoming["phone"] = normalized_phone
    farm_payload = incoming.pop("farm", None)
    for field, value in incoming.items():
        if value is not None:
            data[field] = value
    if farm_payload:
        farm = farmer.farm.model_dump()
        farm.update({field: value for field, value in farm_payload.items() if value is not None})
        data["farm"] = farm
    return FarmerResponse(**data)


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
        ProviderRoute(
            feature=ProviderFeature.whatsapp,
            primary=ProviderName.twilio,
            secondary=None,
            allow_fallback=False,
            note="WhatsApp inbound and outbound delivery uses Twilio only.",
        ),
        ProviderRoute(
            feature=ProviderFeature.sms_voice,
            primary=ProviderName.authkey,
            secondary=None,
            allow_fallback=False,
            note="Outbound SMS text and voice-call delivery uses Authkey only.",
        ),
    ]
    return {route.feature: route for route in routes}


@lru_cache
def get_store() -> AppStore:
    if settings.data_store_provider == "firestore":
        return FirestoreStore()
    return LocalStore()


store = get_store()
