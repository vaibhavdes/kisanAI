from app.models.schemas import ChannelDeliveryReceipt, ChannelReceiptRequest, ChannelReceiptResponse
from app.repositories.store import store


class ChannelReceiptService:
    def save_receipt(self, payload: ChannelReceiptRequest, channel: str | None = None) -> ChannelReceiptResponse:
        normalized_status = self._normalize_status(payload.status)
        receipt = ChannelDeliveryReceipt(
            provider=payload.provider,
            channel=channel or payload.channel,
            provider_message_id=payload.provider_message_id,
            message_id=payload.message_id,
            phone=payload.phone,
            status=payload.status,
            normalized_status=normalized_status,
            event_type=payload.event_type,
            retryable=self._is_retryable(normalized_status),
            raw_payload=payload.raw_payload,
        )
        return ChannelReceiptResponse(saved=True, receipt=store.save_delivery_receipt(receipt))

    def _normalize_status(self, status: str) -> str:
        normalized = status.strip().lower().replace(" ", "_")
        if normalized in {"delivered", "success", "completed"}:
            return "delivered"
        if normalized in {"sent", "submitted", "accepted"}:
            return "sent"
        if normalized in {"read", "seen"}:
            return "read"
        if normalized in {"queued", "pending", "processing", "in_progress"}:
            return "pending"
        if normalized in {"failed", "undelivered", "rejected", "bounced", "expired"}:
            return "failed"
        return "unknown"

    def _is_retryable(self, normalized_status: str) -> bool:
        return normalized_status in {"failed", "pending", "unknown"}
