def detect_farmer_intent(text: str | None, media_uri: str | None = None) -> str:
    if media_uri:
        return "crop_diagnosis"

    normalized = (text or "").strip().lower()
    if not normalized:
        return "unknown"
    if any(word in normalized for word in ["water", "irrigation", "pani", "dry", "rain"]):
        return "irrigation_advisory"
    if any(word in normalized for word in ["photo", "disease", "leaf", "spot", "curl"]):
        return "crop_diagnosis"
    if any(word in normalized for word in ["crop", "sow", "plant", "recommend"]):
        return "crop_recommendation"
    return "general_advisory"

