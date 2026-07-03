from datetime import UTC, datetime

from app.models.schemas import (
    ConversationMessage,
    ExpertTicket,
    FarmerCreate,
    FarmerResponse,
    ProviderFeature,
    ProviderName,
    ProviderRoute,
)


class MemoryStore:
    def __init__(self) -> None:
        self.farmers: dict[str, FarmerResponse] = {}
        self.tickets: list[ExpertTicket] = []
        self.conversations: list[ConversationMessage] = []
        self.provider_routes: dict[ProviderFeature, ProviderRoute] = self._default_provider_routes()
        self.provider_routes_updated_at = datetime.now(UTC)

    def create_farmer(self, payload: FarmerCreate) -> FarmerResponse:
        farmer = FarmerResponse(**payload.model_dump())
        self.farmers[farmer.id] = farmer
        return farmer

    def get_farmer(self, farmer_id: str) -> FarmerResponse | None:
        return self.farmers.get(farmer_id)

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
        self.tickets.clear()
        self.conversations.clear()
        self.provider_routes = self._default_provider_routes()
        self.provider_routes_updated_at = datetime.now(UTC)

    def _default_provider_routes(self) -> dict[ProviderFeature, ProviderRoute]:
        routes = [
            ProviderRoute(
                feature=ProviderFeature.weather,
                primary=ProviderName.imd,
                secondary=ProviderName.open_meteo,
                note="Use IMD/government weather first; Open-Meteo only as free fallback.",
            ),
            ProviderRoute(
                feature=ProviderFeature.stt,
                primary=ProviderName.google_stt,
                secondary=ProviderName.sarvam_stt,
            ),
            ProviderRoute(
                feature=ProviderFeature.tts,
                primary=ProviderName.google_tts,
                secondary=ProviderName.sarvam_tts,
            ),
            ProviderRoute(
                feature=ProviderFeature.translation,
                primary=ProviderName.google_translate,
                secondary=ProviderName.sarvam_translate,
                note="Prefer cheaper cached translation; use Gemini only inside advisory generation when needed.",
            ),
            ProviderRoute(
                feature=ProviderFeature.llm_advisory,
                primary=ProviderName.gemini,
                secondary=ProviderName.vertex_ai,
            ),
            ProviderRoute(
                feature=ProviderFeature.vision_ocr,
                primary=ProviderName.gemini_vision,
                secondary=ProviderName.vertex_ai_vision,
            ),
            ProviderRoute(
                feature=ProviderFeature.satellite,
                primary=ProviderName.earth_engine,
                secondary=None,
                allow_fallback=False,
                note="No manual NDVI fallback; original satellite data is required.",
            ),
            ProviderRoute(
                feature=ProviderFeature.geocoding_maps,
                primary=ProviderName.google_maps,
                secondary=ProviderName.osm_nominatim,
            ),
            ProviderRoute(
                feature=ProviderFeature.whatsapp,
                primary=ProviderName.authkey,
                secondary=ProviderName.twilio,
            ),
            ProviderRoute(
                feature=ProviderFeature.sms_voice,
                primary=ProviderName.authkey,
                secondary=ProviderName.twilio,
            ),
        ]
        return {route.feature: route for route in routes}


store = MemoryStore()
