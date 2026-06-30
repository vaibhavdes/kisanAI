from app.core.config import settings
from app.models.schemas import DiagnosisRequest, DiagnosisResult, ExpertTicket, FarmerResponse


class ExpertService:
    def create_ticket(
        self,
        farmer: FarmerResponse,
        payload: DiagnosisRequest,
        diagnosis: DiagnosisResult,
    ) -> ExpertTicket:
        center = f"{farmer.district} {settings.rythu_seva_default_center}".strip()
        return ExpertTicket(
            farmer_id=farmer.id,
            farmer_name=farmer.name,
            crop=payload.crop,
            issue=diagnosis.likely_issue,
            severity=diagnosis.severity,
            assigned_center=center,
        )

