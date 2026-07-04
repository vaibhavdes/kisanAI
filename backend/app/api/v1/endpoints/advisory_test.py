from fastapi import APIRouter, HTTPException

from app.models.schemas import AdvisoryTestRequest, AdvisoryTestResponse
from app.services.gemini_service import AdvisoryProviderUnavailable, GeminiService

router = APIRouter()


@router.post("/advisory/test", response_model=AdvisoryTestResponse)
def advisory_test(payload: AdvisoryTestRequest) -> AdvisoryTestResponse:
    return _generate_advisory(payload)


@router.post("/api/v1/advisory/test", response_model=AdvisoryTestResponse)
def advisory_test_v1(payload: AdvisoryTestRequest) -> AdvisoryTestResponse:
    return _generate_advisory(payload)


def _generate_advisory(payload: AdvisoryTestRequest) -> AdvisoryTestResponse:
    try:
        return GeminiService().generate_test_advisory(payload)
    except AdvisoryProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
