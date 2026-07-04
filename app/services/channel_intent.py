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
    irrigation_terms = [
        "water",
        "irrigation",
        "irrigate",
        "pani",
        "dry",
        "rain",
        "पाणी",
        "सिंचन",
        "ओलावा",
        "पाऊस",
        "सूखा",
        "बारिश",
        "સિંચાઈ",
        "પાણી",
        "நீர்",
        "மழை",
        "నీరు",
        "వర్షం",
        "ನೀರು",
        "ಮಳೆ",
    ]
    diagnosis_terms = [
        "photo",
        "disease",
        "leaf",
        "spot",
        "curl",
        "फोटो",
        "रोग",
        "पान",
        "डाग",
        "बीमारी",
        "पत्ता",
        "फोटो",
        "રોગ",
        "પાન",
        "நோய்",
        "இலை",
        "వ్యాధి",
        "ఆకు",
        "ರೋಗ",
        "ಎಲೆ",
    ]
    crop_terms = [
        "crop",
        "sow",
        "plant",
        "recommend",
        "पीक",
        "पेरणी",
        "लागवड",
        "सुचवा",
        "फसल",
        "बुवाई",
        "પાક",
        "விவசாயம்",
        "பயிர்",
        "పంట",
        "ಬೆಳೆ",
    ]
    if any(word in normalized for word in irrigation_terms):
        return "irrigation_advisory"
    if any(word in normalized for word in diagnosis_terms):
        return "crop_diagnosis"
    if any(word in normalized for word in crop_terms):
        return "crop_recommendation"
    return "general_advisory"
