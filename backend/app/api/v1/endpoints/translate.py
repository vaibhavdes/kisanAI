from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    DetectLanguageRequest,
    DetectLanguageResponse,
    TranslateTextRequest,
    TranslateTextResponse,
)
from app.services.translation_service import TranslationProviderUnavailable, TranslationService

router = APIRouter()


@router.post("/text", response_model=TranslateTextResponse)
def translate_text(payload: TranslateTextRequest) -> TranslateTextResponse:
    try:
        return TranslationService().translate(payload)
    except TranslationProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/detect-language", response_model=DetectLanguageResponse)
def detect_language(payload: DetectLanguageRequest) -> DetectLanguageResponse:
    try:
        return TranslationService().detect_language(payload)
    except TranslationProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
