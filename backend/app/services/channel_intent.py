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

    if _has_any(normalized, GREETING_TERMS):
        return "greeting"
    if _has_any(normalized, IDENTITY_TERMS):
        return "identity_query"
    if _has_any(normalized, WEATHER_TERMS):
        return "weather_query"

    if _has_any(normalized, DIAGNOSIS_TERMS):
        return "crop_diagnosis"
    if _has_any(normalized, IRRIGATION_TERMS):
        return "irrigation_advisory"
    if _has_any(normalized, CROP_RECOMMENDATION_TERMS):
        return "crop_recommendation"

    if is_crop_followup_text(normalized):
        return "crop_recommendation"

    return "general_advisory"


GREETING_TERMS = [
    "hi",
    "hello",
    "hey",
    "namaste",
    "namaskar",
    "नमस्ते",
    "नमस्कार",
    "राम राम",
    "नमस्ते",
    "નમસ્તે",
    "வணக்கம்",
    "నమస్తే",
    "ನಮಸ್ತೆ",
]

IDENTITY_TERMS = [
    "who am i",
    "do you know me",
    "mein kon hu",
    "main kon hu",
    "mein kaun hu",
    "main kaun hu",
    "mai kaun hu",
    "me kaun hu",
    "मुझे जानते",
    "मैं कौन",
    "मै कौन",
    "मी कोण",
    "मला ओळखता",
    "હું કોણ",
    "நான் யார்",
    "నేను ఎవరు",
    "ನಾನು ಯಾರು",
]

WEATHER_TERMS = [
    "weather",
    "forecast",
    "mausam",
    "mosam",
    "havaman",
    "havamana",
    "hawaman",
    "havama",
    "havamna",
    "aaj ka hava",
    "aaj ka mausam",
    "rain forecast",
    "barish hogi",
    "baarish hogi",
    "मौसम",
    "हवामान",
    "बारिश",
    "बारिस",
    "पाऊस",
    "हवामान",
    "વરસાદ",
    "હવામાન",
    "மழை",
    "வானிலை",
    "వాతావరణం",
    "వర్షం",
    "ಹವಾಮಾನ",
    "ಮಳೆ",
]

IRRIGATION_TERMS = [
    "water",
    "irrigation",
    "irrigate",
    "pani",
    "paanee",
    "dry",
    "soil moisture",
    "पाणी",
    "सिंचन",
    "ओलावा",
    "सूखा",
    "सिंचाई",
    "પાણી",
    "સિંચાઈ",
    "நீர்",
    "பாசனம்",
    "నీరు",
    "సాగు నీరు",
    "ನೀರು",
    "ನೀರಾವರಿ",
]

DIAGNOSIS_TERMS = [
    "photo",
    "image",
    "disease",
    "leaf",
    "spot",
    "curl",
    "pest",
    "फोटो",
    "रोग",
    "पान",
    "डाग",
    "बीमारी",
    "पत्ता",
    "कीड़ा",
    "ફોટો",
    "રોગ",
    "પાન",
    "நோய்",
    "இலை",
    "ఫోటో",
    "వ్యాధి",
    "ఆకు",
    "ರೋಗ",
    "ಎಲೆ",
]

CROP_RECOMMENDATION_TERMS = [
    "crop",
    "sow",
    "plant",
    "recommend",
    "which crop",
    "what crop",
    "jowar",
    "sorghum",
    "bajra",
    "millet",
    "maize",
    "cotton",
    "soybean",
    "tur",
    "pulses",
    "groundnut",
    "rice",
    "paddy",
    "wheat",
    "onion",
    "tomato",
    "chilli",
    "पीक",
    "पेरणी",
    "लागवड",
    "ज्वारी",
    "बाजरी",
    "कापूस",
    "सोयाबीन",
    "फसल",
    "बुवाई",
    "ज्वार",
    "बाजरा",
    "कपास",
    "गेहूं",
    "धान",
    "પાક",
    "જુવાર",
    "કપાસ",
    "பயிர்",
    "சோளம்",
    "పంట",
    "జొన్న",
    "ಬೆಳೆ",
    "ಜೋಳ",
]

CROP_FOLLOWUP_TERMS = [
    "soil",
    "water",
    "rain",
    "rainfall",
    "black soil",
    "red soil",
    "medium water",
    "low water",
    "high water",
    "मिट्टी",
    "माती",
    "काली मिट्टी",
    "काळी माती",
    "बारिश",
    "पाऊस",
    "पानी",
    "पाणी",
    "માટી",
    "વરસાદ",
    "மண்",
    "மழை",
    "నేల",
    "వర్షం",
    "ಮಣ್ಣು",
    "ಮಳೆ",
]

YES_NO_TERMS = ["yes", "no", "haan", "ha", "nahi", "हो", "नाही", "हां", "नहीं", "હા", "ના"]


def is_crop_followup_text(text: str | None) -> bool:
    normalized = (text or "").strip().lower()
    if not normalized:
        return False
    return _has_any(normalized, CROP_FOLLOWUP_TERMS + CROP_RECOMMENDATION_TERMS)


def is_water_followup_text(text: str | None) -> bool:
    normalized = (text or "").strip().lower()
    if not normalized:
        return False
    return _has_any(normalized, IRRIGATION_TERMS + WEATHER_TERMS + YES_NO_TERMS)


def _has_any(text: str, terms: list[str]) -> bool:
    tokens = set(text.replace("?", " ").replace(",", " ").replace(".", " ").split())
    for term in terms:
        if len(term) <= 3 and term.isascii():
            if term in tokens:
                return True
            continue
        if term in text:
            return True
    return False
