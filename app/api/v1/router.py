from fastapi import APIRouter

from app.api.v1.endpoints import (
    advisory_test,
    advisories,
    calls,
    conversations,
    data,
    diagnosis,
    expert,
    farmers,
    health,
    providers,
    recommendations,
    sms,
    soil_cards,
    voice,
    whatsapp,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(advisory_test.router, tags=["advisory-test"])
api_router.include_router(providers.router, prefix="/api/v1/providers", tags=["providers"])
api_router.include_router(farmers.router, prefix="/api/v1/farmers", tags=["farmers"])
api_router.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["recommendations"])
api_router.include_router(advisories.router, prefix="/api/v1/advisories", tags=["advisories"])
api_router.include_router(diagnosis.router, prefix="/api/v1/diagnosis", tags=["diagnosis"])
api_router.include_router(data.router, prefix="/api/v1/data", tags=["government-data"])
api_router.include_router(soil_cards.router, prefix="/api/v1/soil-cards", tags=["soil-cards"])
api_router.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])
api_router.include_router(voice.router, prefix="/api/v1/voice", tags=["voice"])
api_router.include_router(sms.router, prefix="/api/v1/sms", tags=["sms"])
api_router.include_router(whatsapp.router, prefix="/api/v1/whatsapp", tags=["whatsapp"])
api_router.include_router(calls.router, prefix="/api/v1/calls", tags=["calls"])
api_router.include_router(expert.router, prefix="/api/v1/expert", tags=["expert"])
