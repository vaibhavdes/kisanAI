from datetime import UTC, datetime

from app.core.config import settings
from app.models.schemas import (
    AlertDeliveryRequest,
    AlertPlan,
    AlertPriority,
    ConversationMessage,
    ConversationRole,
    DiagnosisRequest,
    DiagnosisResult,
    ExpertTicket,
    ExpertTicketUpdateRequest,
    FarmerResponse,
)
from app.repositories.store import store
from app.services.alert_delivery_service import AlertDeliveryService


class ExpertService:
    def create_ticket(
        self,
        farmer: FarmerResponse,
        payload: DiagnosisRequest,
        diagnosis: DiagnosisResult,
    ) -> ExpertTicket:
        center = self._assigned_center(farmer)
        return ExpertTicket(
            farmer_id=farmer.id,
            farmer_name=farmer.name,
            farmer_phone=farmer.phone,
            district=farmer.district,
            crop=payload.crop,
            issue=diagnosis.likely_issue,
            severity=diagnosis.severity,
            assigned_center=center,
        )

    def update_ticket(self, ticket: ExpertTicket, payload: ExpertTicketUpdateRequest) -> ExpertTicket:
        data = ticket.model_dump()
        if payload.status:
            data["status"] = payload.status
        if payload.assigned_expert:
            data["assigned_expert"] = payload.assigned_expert
        if payload.expert_note:
            data["expert_notes"] = [*ticket.expert_notes, payload.expert_note]
        data["updated_at"] = datetime.now(UTC)
        updated = ExpertTicket(**data)

        if payload.notify_farmer:
            message = payload.farmer_message or self._farmer_notification(updated, payload.expert_note)
            updated = ExpertTicket(**{**updated.model_dump(), "farmer_notification": message})
            self._log_farmer_notification(updated, message)
            self._deliver_farmer_notification(updated, message)

        return store.save_ticket(updated)

    def _assigned_center(self, farmer: FarmerResponse) -> str:
        district = (farmer.district or "").strip()
        base_center = settings.rythu_seva_default_center.strip()
        if district and district.lower() != "unknown":
            return f"{district} {base_center}".strip()
        return base_center

    def _farmer_notification(self, ticket: ExpertTicket, expert_note: str | None) -> str:
        status_text = ticket.status.replace("_", " ")
        note_text = f" Expert note: {expert_note}" if expert_note else ""
        return f"Your expert ticket {ticket.id} is now {status_text}.{note_text}".strip()

    def _log_farmer_notification(self, ticket: ExpertTicket, message: str) -> None:
        store.save_conversation_message(
            ConversationMessage(
                farmer_id=ticket.farmer_id,
                role=ConversationRole.expert,
                text=message,
                channel="expert_followup",
                intent="expert_ticket_update",
                metadata={
                    "ticket_id": ticket.id,
                    "status": ticket.status,
                    "assigned_center": ticket.assigned_center,
                },
            )
        )

    def _deliver_farmer_notification(self, ticket: ExpertTicket, message: str) -> None:
        farmer = store.get_farmer(ticket.farmer_id)
        if not farmer:
            return
        AlertDeliveryService().deliver(
            farmer,
            AlertDeliveryRequest(
                farmer_id=farmer.id,
                message=message,
                language=farmer.language,
                requires_whatsapp_template=True,
                alert_plan=AlertPlan(
                    priority=AlertPriority.high,
                    channels=["whatsapp", "voice_call"],
                    reason=f"Expert ticket {ticket.id} status update.",
                    call_required=True,
                ),
            ),
        )
