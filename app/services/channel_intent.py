def detect_farmer_intent(
    text: str | None,
    media_uri: str | None = None,
    *,
    media_type: str | None = None,
    has_location: bool = False,
) -> str:
    if has_location:
        return "location_update"

    normalized_media_type = (media_type or "").lower()
    if normalized_media_type in {"audio", "voice"}:
        return "voice_message"

    if media_uri or normalized_media_type in {"image", "photo", "document"}:
        return "crop_diagnosis"

    normalized = (text or "").strip().lower()
    if not normalized:
        return "unknown"
    if any(word in normalized for word in ["water", "irrigation", "irrigate", "pani", "dry", "rain"]):
        return "irrigation_advisory"
    if any(word in normalized for word in ["photo", "disease", "leaf", "spot", "curl"]):
        return "crop_diagnosis"
    if any(word in normalized for word in ["crop", "sow", "plant", "recommend"]):
        return "crop_recommendation"
    return "general_advisory"
