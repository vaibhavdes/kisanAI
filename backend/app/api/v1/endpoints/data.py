from fastapi import APIRouter

from app.models.schemas import DatasetReference, GovernmentDataContextRequest, GovernmentDataContextResponse
from app.services.government_data_service import GovernmentDataService

router = APIRouter()


@router.get("/sources", response_model=list[DatasetReference])
def government_data_sources() -> list[DatasetReference]:
    return GovernmentDataService().list_sources()


@router.post("/context", response_model=GovernmentDataContextResponse)
def government_data_context(
    payload: GovernmentDataContextRequest,
) -> GovernmentDataContextResponse:
    return GovernmentDataService().build_context(payload)

