LANGUAGE_NAMES = {
    "en-IN": "English",
    "hi-IN": "Hindi",
    "mr-IN": "Marathi",
    "te-IN": "Telugu",
    "ta-IN": "Tamil",
    "kn-IN": "Kannada",
    "gu-IN": "Gujarati",
}

PHRASES = {
    "irrigation_response": {
        "en-IN": "{name}, check soil moisture first. If the field is dry, irrigate lightly today.",
        "hi-IN": "{name}, पहले मिट्टी की नमी जांचें। खेत सूखा हो तो आज हल्की सिंचाई करें।",
        "mr-IN": "{name}, आधी मातीतील ओलावा तपासा. शेत कोरडे असेल तर आज हलके पाणी द्या.",
        "te-IN": "{name}, ముందుగా నేల తేమను చూడండి. పొలం ఎండగా ఉంటే ఈరోజు తేలికగా నీరు పెట్టండి.",
    },
    "diagnosis_response": {
        "en-IN": "{name}, upload a clear crop photo and I will create an expert follow-up ticket.",
        "hi-IN": "{name}, फसल की साफ फोटो अपलोड करें, मैं विशेषज्ञ फॉलो-अप टिकट बनाऊंगा।",
        "mr-IN": "{name}, पिकाचा स्पष्ट फोटो अपलोड करा, मी तज्ञ फॉलो-अप तिकीट तयार करतो.",
        "te-IN": "{name}, పంట స్పష్టమైన ఫోటో అప్లోడ్ చేయండి, నేను నిపుణుల ఫాలో-అప్ టికెట్ సృష్టిస్తాను.",
    },
    "crop_response": {
        "en-IN": "{name}, I can recommend crops using soil, rain, water depth and satellite health.",
        "hi-IN": "{name}, मैं मिट्टी, बारिश, पानी की गहराई और सैटेलाइट संकेतों से फसल सुझा सकता हूं।",
        "mr-IN": "{name}, मी माती, पाऊस, पाण्याची खोली आणि सॅटेलाइट संकेतांवरून पीक सुचवू शकतो.",
        "te-IN": "{name}, నేల, వర్షం, నీటి లోతు మరియు ఉపగ్రహ సంకేతాలతో నేను పంటలు సూచించగలను.",
    },
    "general_response": {
        "en-IN": "{name}, ask by voice or SMS in {language} and I will guide you.",
        "hi-IN": "{name}, {language} में आवाज या SMS से पूछें, मैं मार्गदर्शन करूंगा।",
        "mr-IN": "{name}, {language} मध्ये आवाज किंवा SMS ने विचारा, मी मार्गदर्शन करेन.",
        "te-IN": "{name}, {language} లో వాయిస్ లేదా SMS ద్వారా అడగండి, నేను మార్గనిర్దేశం చేస్తాను.",
    },
    "dry_spell_irrigate": {
        "en-IN": "Dry spell risk is {risk}. Apply about {mm} mm irrigation for {crop} in the next 24-48 hours if field moisture is low.",
        "hi-IN": "सूखे अंतराल का जोखिम {risk} है। नमी कम हो तो अगले 24-48 घंटे में {crop} को लगभग {mm} mm सिंचाई दें।",
        "mr-IN": "कोरड्या कालावधीचा धोका {risk} आहे. ओलावा कमी असेल तर पुढील 24-48 तासांत {crop} ला सुमारे {mm} mm पाणी द्या.",
        "te-IN": "ఎండ విరామం ప్రమాదం {risk}. తేమ తక్కువగా ఉంటే వచ్చే 24-48 గంటల్లో {crop} కు సుమారు {mm} mm నీరు పెట్టండి.",
    },
    "dry_spell_wait": {
        "en-IN": "No immediate irrigation needed. Recheck field moisture in two days.",
        "hi-IN": "अभी सिंचाई की जरूरत नहीं है। दो दिन बाद खेत की नमी फिर जांचें।",
        "mr-IN": "आत्ता पाणी देण्याची गरज नाही. दोन दिवसांनी मातीतील ओलावा पुन्हा तपासा.",
        "te-IN": "ఇప్పుడే నీరు పెట్టాల్సిన అవసరం లేదు. రెండు రోజుల్లో నేల తేమను మళ్లీ చూడండి.",
    },
    "sms_water": {
        "en-IN": "Dry-spell check received. Reply with CROP and PINCODE, e.g. WATER MAIZE 522001.",
        "hi-IN": "सूखा जांच अनुरोध मिला। फसल और पिनकोड भेजें, जैसे WATER MAIZE 522001.",
        "mr-IN": "कोरडा कालावधी तपासणी मिळाली. पीक आणि पिनकोड पाठवा, उदा. WATER MAIZE 522001.",
        "te-IN": "ఎండ విరామం తనిఖీ వచ్చింది. పంట మరియు పిన్ కోడ్ పంపండి, ఉదా. WATER MAIZE 522001.",
    },
    "sms_photo": {
        "en-IN": "Send a clear crop photo on the app or WhatsApp channel for expert review.",
        "hi-IN": "विशेषज्ञ जांच के लिए ऐप या WhatsApp पर फसल की साफ फोटो भेजें।",
        "mr-IN": "तज्ञ तपासणीसाठी अॅप किंवा WhatsApp वर पिकाचा स्पष्ट फोटो पाठवा.",
        "te-IN": "నిపుణుల పరిశీలన కోసం యాప్ లేదా WhatsApp లో పంట స్పష్టమైన ఫోటో పంపండి.",
    },
    "sms_crop": {
        "en-IN": "Send SOIL, RAIN and WATER availability to receive crop recommendation.",
        "hi-IN": "फसल सलाह के लिए मिट्टी, बारिश और पानी की उपलब्धता भेजें।",
        "mr-IN": "पीक सल्ल्यासाठी माती, पाऊस आणि पाण्याची उपलब्धता पाठवा.",
        "te-IN": "పంట సలహా కోసం నేల, వర్షం మరియు నీటి లభ్యత పంపండి.",
    },
    "sms_unknown": {
        "en-IN": "Use WATER, CROP, or PHOTO to get advisory support.",
        "hi-IN": "सलाह के लिए WATER, CROP या PHOTO लिखें।",
        "mr-IN": "सल्ल्यासाठी WATER, CROP किंवा PHOTO लिहा.",
        "te-IN": "సలహా కోసం WATER, CROP లేదా PHOTO అని పంపండి.",
    },
}


def language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code)


def phrase(key: str, language: str, **kwargs: object) -> str:
    localized = PHRASES.get(key, {})
    template = localized.get(language) or localized.get("en-IN") or key
    return template.format(**kwargs)
