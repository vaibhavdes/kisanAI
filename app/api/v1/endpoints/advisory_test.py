from fastapi import APIRouter

from app.models.schemas import AdvisoryTestRequest, AdvisoryTestResponse
from app.services.gemini_service import GeminiService

router = APIRouter()


@router.post("/advisory/test", response_model=AdvisoryTestResponse)
def advisory_test(payload: AdvisoryTestRequest) -> AdvisoryTestResponse:
    return GeminiService().generate_test_advisory(payload)


@router.post("/api/v1/advisory/test", response_model=AdvisoryTestResponse)
def advisory_test_v1(payload: AdvisoryTestRequest) -> AdvisoryTestResponse:
    return GeminiService().generate_test_advisory(payload)
