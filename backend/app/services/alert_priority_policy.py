from app.models.schemas import AlertPlan, AlertPriority, RiskLevel


class AlertPriorityPolicy:
    def build_plan(
        self,
        risk_level: RiskLevel,
        *,
        has_whatsapp: bool = True,
        allow_call: bool = True,
        reason: str | None = None,
    ) -> AlertPlan:
        if risk_level == RiskLevel.critical:
            channels = ["whatsapp", "sms"]
            if allow_call:
                channels.append("voice_call")
            return AlertPlan(
                priority=AlertPriority.urgent,
                channels=channels,
                reason=reason or "Critical farm risk requires immediate farmer contact.",
                call_required=allow_call,
            )

        if risk_level == RiskLevel.high:
            channels = ["whatsapp", "sms"] if has_whatsapp else ["sms"]
            return AlertPlan(
                priority=AlertPriority.high,
                channels=channels,
                reason=reason or "High farm risk requires same-day alert.",
            )

        if risk_level == RiskLevel.medium:
            return AlertPlan(
                priority=AlertPriority.medium,
                channels=["whatsapp"] if has_whatsapp else ["sms"],
                reason=reason or "Moderate risk can be sent as advisory notification.",
            )

        return AlertPlan(
            priority=AlertPriority.low,
            channels=["whatsapp"] if has_whatsapp else ["sms"],
            reason=reason or "Low risk can remain in normal advisory feed.",
        )

