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
        "ta-IN": "{name}, முதலில் மண் ஈரத்தை பார்க்கவும். நிலம் உலர்ந்திருந்தால் இன்று லேசாக நீர் விடுங்கள்.",
        "kn-IN": "{name}, ಮೊದಲು ಮಣ್ಣಿನ ತೇವಾಂಶ ನೋಡಿ. ಹೊಲ ಒಣಗಿದ್ದರೆ ಇಂದು ಸ್ವಲ್ಪ ನೀರು ಕೊಡಿ.",
        "gu-IN": "{name}, પહેલા માટીની ભેજ તપાસો. ખેતર સુકું હોય તો આજે હળવું સિંચાઈ કરો.",
    },
    "diagnosis_response": {
        "en-IN": "{name}, upload a clear crop photo and I will create an expert follow-up ticket.",
        "hi-IN": "{name}, फसल की साफ फोटो अपलोड करें, मैं विशेषज्ञ फॉलो-अप टिकट बनाऊंगा।",
        "mr-IN": "{name}, पिकाचा स्पष्ट फोटो अपलोड करा, मी तज्ञ फॉलो-अप तिकीट तयार करतो.",
        "te-IN": "{name}, పంట స్పష్టమైన ఫోటో అప్లోడ్ చేయండి, నేను నిపుణుల ఫాలో-అప్ టికెట్ సృష్టిస్తాను.",
        "ta-IN": "{name}, பயிரின் தெளிவான புகைப்படத்தை அனுப்புங்கள். நான் நிபுணர் பின்தொடர்பு டிக்கெட் உருவாக்குவேன்.",
        "kn-IN": "{name}, ಬೆಳೆ ಸ್ಪಷ್ಟ ಫೋಟೋ ಕಳುಹಿಸಿ. ನಾನು ತಜ್ಞರ ಫಾಲೋ-ಅಪ್ ಟಿಕೆಟ್ ಸೃಷ್ಟಿಸುತ್ತೇನೆ.",
        "gu-IN": "{name}, પાકનો સ્પષ્ટ ફોટો મોકલો. હું નિષ્ણાત ફોલો-અપ ટિકિટ બનાવું છું.",
    },
    "crop_response": {
        "en-IN": "{name}, I can recommend crops using soil, rain, water depth and satellite health.",
        "hi-IN": "{name}, मैं मिट्टी, बारिश, पानी की गहराई और सैटेलाइट संकेतों से फसल सुझा सकता हूं।",
        "mr-IN": "{name}, मी माती, पाऊस, पाण्याची खोली आणि सॅटेलाइट संकेतांवरून पीक सुचवू शकतो.",
        "te-IN": "{name}, నేల, వర్షం, నీటి లోతు మరియు ఉపగ్రహ సంకేతాలతో నేను పంటలు సూచించగలను.",
        "ta-IN": "{name}, மண், மழை, நீர் நிலை மற்றும் செயற்கைக்கோள் தகவலால் பயிர் பரிந்துரைக்க முடியும்.",
        "kn-IN": "{name}, ಮಣ್ಣು, ಮಳೆ, ನೀರಿನ ಲಭ್ಯತೆ ಮತ್ತು ಉಪಗ್ರಹ ಸೂಚನೆಗಳಿಂದ ಬೆಳೆ ಸಲಹೆ ಕೊಡಬಹುದು.",
        "gu-IN": "{name}, માટી, વરસાદ, પાણી અને ઉપગ્રહ સંકેતો પરથી પાક સૂચવી શકું છું.",
    },
    "general_response": {
        "en-IN": "Namaste {name}. I am Kisan AI. Ask me about today's weather, irrigation, crop choice, or send a crop photo for disease help. If you share your farm location, I can give more local advice.",
        "hi-IN": "नमस्ते {name}। मैं किसान AI हूं। आप आज का मौसम, सिंचाई, कौन सी फसल लगानी है, या फसल की बीमारी के लिए फोटो भेजकर पूछ सकते हैं। खेत की लोकेशन देंगे तो सलाह और स्थानीय होगी।",
        "mr-IN": "नमस्कार {name}. मी किसान AI आहे. आजचे हवामान, पाणी द्यायचे का, कोणते पीक घ्यावे किंवा रोगासाठी पिकाचा फोटो पाठवू शकता. शेताची लोकेशन दिल्यास सल्ला अधिक स्थानिक मिळेल.",
        "te-IN": "నమస్తే {name}. నేను కిసాన్ AI. ఈరోజు వాతావరణం, నీరు పెట్టాలా, ఏ పంట వేయాలి లేదా పంట రోగం కోసం ఫోటో పంపి అడగండి. పొలం లొకేషన్ ఇస్తే మరింత స్థానిక సలహా ఇస్తాను.",
        "ta-IN": "வணக்கம் {name}. நான் Kisan AI. இன்று வானிலை, நீர் விடலாமா, எந்த பயிர் போடலாம், அல்லது நோய்க்கு பயிர் புகைப்படம் அனுப்பி கேளுங்கள். நில இடம் கொடுத்தால் உள்ளூர் ஆலோசனை தருவேன்.",
        "kn-IN": "ನಮಸ್ತೆ {name}. ನಾನು Kisan AI. ಇಂದಿನ ಹವಾಮಾನ, ನೀರು ಕೊಡಬೇಕೇ, ಯಾವ ಬೆಳೆ ಬೆಳೆಸಬೇಕು, ಅಥವಾ ರೋಗಕ್ಕೆ ಬೆಳೆ ಫೋಟೋ ಕಳುಹಿಸಿ ಕೇಳಬಹುದು. ಹೊಲದ ಸ್ಥಳ ಕೊಟ್ಟರೆ ಸ್ಥಳೀಯ ಸಲಹೆ ಕೊಡುತ್ತೇನೆ.",
        "gu-IN": "નમસ્તે {name}. હું Kisan AI છું. આજનું હવામાન, સિંચાઈ, કયો પાક કરવો અથવા રોગ માટે પાકનો ફોટો મોકલી પૂછો. ખેતરની લોકેશન આપશો તો વધુ સ્થાનિક સલાહ મળશે.",
    },
    "first_greeting_name": {
        "en-IN": "Namaste. I am Kisan AI. What is your name? I will remember it for the next advice. You can also ask weather, irrigation, crop recommendation, or send a crop photo.",
        "hi-IN": "नमस्ते। मैं किसान AI हूं। आपका नाम क्या है? अगली सलाह में मैं इसे याद रखूंगा। आप मौसम, सिंचाई, फसल सुझाव पूछ सकते हैं या फसल की फोटो भेज सकते हैं।",
        "mr-IN": "नमस्कार. मी किसान AI आहे. तुमचे नाव काय आहे? पुढच्या सल्ल्यासाठी मी ते लक्षात ठेवेन. तुम्ही हवामान, पाणी, पीक सल्ला विचारू शकता किंवा पिकाचा फोटो पाठवू शकता.",
        "te-IN": "నమస్తే. నేను Kisan AI. మీ పేరు ఏమిటి? తదుపరి సలహాకు గుర్తుంచుకుంటాను. వాతావరణం, నీరు, పంట సలహా అడగవచ్చు లేదా పంట ఫోటో పంపవచ్చు.",
        "ta-IN": "வணக்கம். நான் Kisan AI. உங்கள் பெயர் என்ன? அடுத்த ஆலோசனைக்கு நினைவில் வைத்துக் கொள்கிறேன். வானிலை, நீர், பயிர் பரிந்துரை கேட்கலாம் அல்லது பயிர் புகைப்படம் அனுப்பலாம்.",
        "kn-IN": "ನಮಸ್ತೆ. ನಾನು Kisan AI. ನಿಮ್ಮ ಹೆಸರು ಏನು? ಮುಂದಿನ ಸಲಹೆಗೆ ನೆನಪಿಟ್ಟುಕೊಳ್ಳುತ್ತೇನೆ. ಹವಾಮಾನ, ನೀರು, ಬೆಳೆ ಸಲಹೆ ಕೇಳಬಹುದು ಅಥವಾ ಬೆಳೆ ಫೋಟೋ ಕಳುಹಿಸಬಹುದು.",
        "gu-IN": "નમસ્તે. હું Kisan AI છું. તમારું નામ શું છે? આગળની સલાહ માટે યાદ રાખીશ. હવામાન, સિંચાઈ, પાક સલાહ પૂછો અથવા પાકનો ફોટો મોકલો.",
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
        "en-IN": "I can check irrigation risk. Tell me crop name and village/pincode, or share farm location. Example: my jowar field is near Ahilyanagar.",
        "hi-IN": "मैं सिंचाई की जरूरत जांच सकता हूं। फसल का नाम और गांव/पिनकोड बताएं, या खेत की लोकेशन भेजें। जैसे: मेरी ज्वार की फसल अहिल्यानगर के पास है।",
        "mr-IN": "मी पाणी देण्याची गरज तपासू शकतो. पिकाचे नाव आणि गाव/पिनकोड सांगा किंवा शेताची लोकेशन पाठवा. उदा. माझे ज्वारीचे शेत अहिल्यानगर जवळ आहे.",
        "te-IN": "నేను నీటి అవసరం చూడగలను. పంట పేరు మరియు గ్రామం/పిన్ కోడ్ చెప్పండి లేదా పొలం లొకేషన్ పంపండి.",
        "ta-IN": "நீர் தேவையை நான் பார்க்க முடியும். பயிர் பெயர் மற்றும் கிராமம்/பின்கோடு சொல்லுங்கள் அல்லது நில இடம் பகிருங்கள்.",
        "kn-IN": "ನೀರಿನ ಅಗತ್ಯವನ್ನು ನೋಡಬಹುದು. ಬೆಳೆ ಹೆಸರು ಮತ್ತು ಗ್ರಾಮ/ಪಿನ್ ಕೋಡ್ ಹೇಳಿ ಅಥವಾ ಹೊಲದ ಸ್ಥಳ ಕಳುಹಿಸಿ.",
        "gu-IN": "હું સિંચાઈની જરૂર તપાસી શકું છું. પાકનું નામ અને ગામ/પિનકોડ કહો અથવા ખેતરની લોકેશન મોકલો.",
    },
    "sms_photo": {
        "en-IN": "Send a clear crop photo on the app or WhatsApp channel for expert review.",
        "hi-IN": "विशेषज्ञ जांच के लिए ऐप या WhatsApp पर फसल की साफ फोटो भेजें।",
        "mr-IN": "तज्ञ तपासणीसाठी अॅप किंवा WhatsApp वर पिकाचा स्पष्ट फोटो पाठवा.",
        "te-IN": "నిపుణుల పరిశీలన కోసం యాప్ లేదా WhatsApp లో పంట స్పష్టమైన ఫోటో పంపండి.",
        "ta-IN": "நிபுணர் பார்க்க பயிரின் தெளிவான புகைப்படத்தை app அல்லது WhatsApp-ல் அனுப்புங்கள்.",
        "kn-IN": "ತಜ್ಞರು ಪರಿಶೀಲಿಸಲು app ಅಥವಾ WhatsApp ನಲ್ಲಿ ಬೆಳೆ ಸ್ಪಷ್ಟ ಫೋಟೋ ಕಳುಹಿಸಿ.",
        "gu-IN": "નિષ્ણાત તપાસ માટે app અથવા WhatsApp પર પાકનો સ્પષ્ટ ફોટો મોકલો.",
    },
    "whatsapp_document_received": {
        "en-IN": "Document received. For crop disease help, send a clear crop photo. For soil-card details, use the app upload flow.",
    },
    "sms_crop": {
        "en-IN": "For crop recommendation, tell me your soil type if you know it, water availability, and village/pincode. You can simply say: black soil, medium water, near Pune.",
        "hi-IN": "फसल सुझाव के लिए अगर पता हो तो मिट्टी का प्रकार, पानी की उपलब्धता और गांव/पिनकोड बताएं। ऐसे लिख सकते हैं: काली मिट्टी, मध्यम पानी, पुणे के पास।",
        "mr-IN": "पीक सुचवण्यासाठी मातीचा प्रकार, पाण्याची उपलब्धता आणि गाव/पिनकोड सांगा. असे लिहू शकता: काळी माती, मध्यम पाणी, पुणे जवळ.",
        "te-IN": "పంట సలహా కోసం నేల రకం, నీటి లభ్యత మరియు గ్రామం/పిన్ కోడ్ చెప్పండి. ఉదా: నల్ల నేల, మధ్యస్థ నీరు.",
        "ta-IN": "பயிர் பரிந்துரைக்கு மண் வகை தெரிந்தால், நீர் கிடைக்கும் நிலை மற்றும் கிராமம்/பின்கோடு சொல்லுங்கள்.",
        "kn-IN": "ಬೆಳೆ ಸಲಹೆಗೆ ಮಣ್ಣಿನ ಪ್ರಕಾರ ಗೊತ್ತಿದ್ದರೆ, ನೀರಿನ ಲಭ್ಯತೆ ಮತ್ತು ಗ್ರಾಮ/ಪಿನ್ ಕೋಡ್ ಹೇಳಿ.",
        "gu-IN": "પાક ભલામણ માટે માટીનો પ્રકાર, પાણીની ઉપલબ્ધતા અને ગામ/પિનકોડ કહો.",
    },
    "sms_location_saved": {
        "en-IN": "Farm location saved. Ask for water, crop recommendation, or send a crop photo.",
        "hi-IN": "खेत की लोकेशन सेव हो गई। पानी, फसल सलाह पूछें या फसल की फोटो भेजें।",
        "mr-IN": "शेताचे लोकेशन सेव झाले. पाणी, पीक सल्ला विचारा किंवा पिकाचा फोटो पाठवा.",
        "te-IN": "పొలం స్థానం సేవ్ అయింది. నీరు, పంట సలహా అడగండి లేదా పంట ఫోటో పంపండి.",
        "ta-IN": "நில இடம் சேமிக்கப்பட்டது. நீர், பயிர் ஆலோசனை கேளுங்கள் அல்லது பயிர் புகைப்படம் அனுப்புங்கள்.",
        "kn-IN": "ಹೊಲದ ಸ್ಥಳ ಉಳಿಸಲಾಗಿದೆ. ನೀರು, ಬೆಳೆ ಸಲಹೆ ಕೇಳಿ ಅಥವಾ ಬೆಳೆ ಫೋಟೋ ಕಳುಹಿಸಿ.",
        "gu-IN": "ખેતરની લોકેશન સેવ થઈ. પાણી, પાક સલાહ પૂછો અથવા પાકનો ફોટો મોકલો.",
    },
    "location_saved_detailed": {
        "en-IN": "Farm location saved. I identified village/city: {village}, taluka: {taluka}, district: {district}, state: {state}, pincode: {pincode}. I will reuse this for weather, irrigation and crop advice.",
        "hi-IN": "खेत की लोकेशन सेव हो गई। पहचाना गया गांव/शहर: {village}, तालुका: {taluka}, जिला: {district}, राज्य: {state}, पिनकोड: {pincode}. अब मौसम, सिंचाई और फसल सलाह में इसी जानकारी का उपयोग होगा।",
        "mr-IN": "शेताचे लोकेशन सेव झाले. ओळखलेले गाव/शहर: {village}, तालुका: {taluka}, जिल्हा: {district}, राज्य: {state}, पिनकोड: {pincode}. आता हवामान, पाणी आणि पीक सल्ल्यासाठी हीच माहिती वापरेन.",
        "te-IN": "పొలం స్థానం సేవ్ అయింది. గుర్తించిన గ్రామం/పట్టణం: {village}, తాలూకా: {taluka}, జిల్లా: {district}, రాష్ట్రం: {state}, పిన్ కోడ్: {pincode}. వాతావరణం, నీరు, పంట సలహాకు దీనినే వాడుతాను.",
        "ta-IN": "நில இடம் சேமிக்கப்பட்டது. கண்டறிந்த கிராமம்/நகரம்: {village}, தாலுகா: {taluka}, மாவட்டம்: {district}, மாநிலம்: {state}, பின்கோடு: {pincode}. வானிலை, நீர், பயிர் ஆலோசனையில் இதையே பயன்படுத்துவேன்.",
        "kn-IN": "ಹೊಲದ ಸ್ಥಳ ಉಳಿಸಲಾಗಿದೆ. ಕಂಡ ಗ್ರಾಮ/ನಗರ: {village}, ತಾಲೂಕು: {taluka}, ಜಿಲ್ಲೆ: {district}, ರಾಜ್ಯ: {state}, ಪಿನ್ ಕೋಡ್: {pincode}. ಹವಾಮಾನ, ನೀರು ಮತ್ತು ಬೆಳೆ ಸಲಹೆಗೆ ಇದನ್ನೇ ಬಳಸುತ್ತೇನೆ.",
        "gu-IN": "ખેતરની લોકેશન સેવ થઈ. ઓળખાયેલ ગામ/શહેર: {village}, તાલુકો: {taluka}, જિલ્લો: {district}, રાજ્ય: {state}, પિનકોડ: {pincode}. હવામાન, સિંચાઈ અને પાક સલાહમાં આ જ માહિતી વાપરીશ.",
    },
    "sms_unknown": {
        "en-IN": "I did not fully understand. You can ask in simple words: today's weather, should I irrigate, which crop should I grow, or send a crop photo.",
        "hi-IN": "मैं पूरी तरह समझ नहीं पाया। आप सरल भाषा में पूछें: आज का मौसम, पानी देना है क्या, कौन सी फसल लगाऊं, या फसल की फोटो भेजें।",
        "mr-IN": "मला पूर्ण समजले नाही. सोप्या भाषेत विचारा: आजचे हवामान, पाणी द्यायचे का, कोणते पीक घ्यावे किंवा पिकाचा फोटो पाठवा.",
        "te-IN": "నాకు పూర్తిగా అర్థం కాలేదు. సులభంగా అడగండి: ఈరోజు వాతావరణం, నీరు పెట్టాలా, ఏ పంట వేయాలి లేదా పంట ఫోటో పంపండి.",
        "ta-IN": "எனக்கு முழுமையாக புரியவில்லை. எளிமையாக கேளுங்கள்: இன்றைய வானிலை, நீர் விடலாமா, எந்த பயிர், அல்லது பயிர் புகைப்படம்.",
        "kn-IN": "ನನಗೆ ಸಂಪೂರ್ಣವಾಗಿ ಅರ್ಥವಾಗಲಿಲ್ಲ. ಸರಳವಾಗಿ ಕೇಳಿ: ಇಂದಿನ ಹವಾಮಾನ, ನೀರು ಕೊಡಬೇಕೇ, ಯಾವ ಬೆಳೆ, ಅಥವಾ ಬೆಳೆ ಫೋಟೋ.",
        "gu-IN": "મને પૂરેપૂરું સમજાયું નથી. સરળ રીતે પૂછો: આજનું હવામાન, પાણી આપવું કે નહીં, કયો પાક, અથવા પાકનો ફોટો.",
    },
    "weather_response": {
        "en-IN": "I can tell local weather. Please share farm location or village/pincode. If location is already saved, I will use it for rainfall and irrigation advice.",
        "hi-IN": "मैं आपके इलाके का मौसम बता सकता हूं। कृपया खेत की लोकेशन या गांव/पिनकोड भेजें। लोकेशन सेव है तो उसी से बारिश और सिंचाई की सलाह दूंगा।",
        "mr-IN": "मी तुमच्या भागाचे हवामान सांगू शकतो. कृपया शेताची लोकेशन किंवा गाव/पिनकोड पाठवा. लोकेशन सेव असेल तर त्यावरून पाऊस आणि पाण्याचा सल्ला देईन.",
        "te-IN": "నేను మీ ప్రాంత వాతావరణం చెప్పగలను. దయచేసి పొలం లొకేషన్ లేదా గ్రామం/పిన్ కోడ్ పంపండి.",
        "ta-IN": "உங்கள் பகுதி வானிலையை சொல்ல முடியும். நில இடம் அல்லது கிராமம்/பின்கோடு அனுப்புங்கள்.",
        "kn-IN": "ನಿಮ್ಮ ಪ್ರದೇಶದ ಹವಾಮಾನ ಹೇಳಬಹುದು. ಹೊಲದ ಸ್ಥಳ ಅಥವಾ ಗ್ರಾಮ/ಪಿನ್ ಕೋಡ್ ಕಳುಹಿಸಿ.",
        "gu-IN": "તમારા વિસ્તારનું હવામાન કહી શકું છું. ખેતરની લોકેશન અથવા ગામ/પિનકોડ મોકલો.",
    },
    "weather_need_location": {
        "en-IN": "To tell exact weather, please share farm location or type village/pincode once. After that I will not ask again.",
        "hi-IN": "सटीक मौसम बताने के लिए खेत की लोकेशन भेजें या गांव/पिनकोड एक बार लिखें। उसके बाद मैं फिर नहीं पूछूंगा।",
        "mr-IN": "अचूक हवामान सांगण्यासाठी शेताची लोकेशन पाठवा किंवा गाव/पिनकोड एकदा लिहा. त्यानंतर मी पुन्हा विचारणार नाही.",
        "te-IN": "ఖచ్చితమైన వాతావరణం కోసం పొలం లొకేషన్ పంపండి లేదా గ్రామం/పిన్ కోడ్ ఒకసారి రాయండి.",
        "ta-IN": "சரியான வானிலைக்கு நில இடம் பகிருங்கள் அல்லது கிராமம்/பின்கோடு ஒருமுறை எழுதுங்கள்.",
        "kn-IN": "ನಿಖರ ಹವಾಮಾನಕ್ಕೆ ಹೊಲದ ಸ್ಥಳ ಕಳುಹಿಸಿ ಅಥವಾ ಗ್ರಾಮ/ಪಿನ್ ಕೋಡ್ ಒಮ್ಮೆ ಬರೆಯಿರಿ.",
        "gu-IN": "ચોક્કસ હવામાન માટે ખેતરની લોકેશન મોકલો અથવા ગામ/પિનકોડ એક વાર લખો.",
    },
    "weather_answer": {
        "en-IN": "{location}: today is cool at about {temp} C and humidity is {humidity}%. Rain chance looks high: about {rain3} mm in 3 days and {rain7} mm in 7 days. Keep drainage open and avoid spraying if clouds/rain continue.",
        "hi-IN": "{location}: आज तापमान करीब {temp} C है और नमी {humidity}% है। बारिश अच्छी दिख रही है: 3 दिन में करीब {rain3} mm और 7 दिन में {rain7} mm। खेत में पानी निकास खुला रखें और बारिश में छिड़काव न करें।",
        "mr-IN": "{location}: आज तापमान सुमारे {temp} C आहे आणि आर्द्रता {humidity}% आहे. पाऊस जास्त दिसतोय: 3 दिवसांत सुमारे {rain3} mm आणि 7 दिवसांत {rain7} mm. पाण्याचा निचरा खुला ठेवा आणि पावसात फवारणी टाळा.",
        "te-IN": "{location}: ప్రస్తుతం సుమారు {temp} C, తేమ {humidity}%. వర్షం అంచనా: 3 రోజుల్లో {rain3} mm, 7 రోజుల్లో {rain7} mm. వాడిన డేటా: {source}.",
        "ta-IN": "{location}: இப்போது சுமார் {temp} C, ஈரப்பதம் {humidity}%. மழை கணிப்பு: 3 நாளில் {rain3} mm, 7 நாளில் {rain7} mm. பயன்படுத்திய தரவு: {source}.",
        "kn-IN": "{location}: ಈಗ ಸುಮಾರು {temp} C, ತೇವಾಂಶ {humidity}%. ಮಳೆ ಅಂದಾಜು: 3 ದಿನದಲ್ಲಿ {rain3} mm, 7 ದಿನದಲ್ಲಿ {rain7} mm. ಬಳಸಿದ ಡೇಟಾ: {source}.",
        "gu-IN": "{location}: હાલમાં અંદાજે {temp} C, ભેજ {humidity}%. વરસાદ અંદાજ: 3 દિવસમાં {rain3} mm અને 7 દિવસમાં {rain7} mm. વપરાયેલ ડેટા: {source}.",
    },
    "weather_public_context": {
        "en-IN": "{location}: exact live weather needs farm coordinates. From public rainfall data, normal rainfall is {rainfall} mm. Data used: {source}.",
        "hi-IN": "{location}: सटीक लाइव मौसम के लिए खेत की लोकेशन चाहिए। सार्वजनिक बारिश डेटा के अनुसार सामान्य बारिश {rainfall} mm है। उपयोग किया गया डेटा: {source}.",
        "mr-IN": "{location}: अचूक लाईव्ह हवामानासाठी शेताचे coordinates हवेत. सार्वजनिक पाऊस डेटानुसार सामान्य पाऊस {rainfall} mm आहे. वापरलेला डेटा: {source}.",
    },
    "weather_failed": {
        "en-IN": "{location}: weather service failed right now. I have logged the provider issue; please try again in a few minutes.",
        "hi-IN": "{location}: अभी मौसम सेवा से डेटा नहीं मिला। सेवा की समस्या लॉग हो गई है, कृपया कुछ देर बाद फिर पूछें।",
        "mr-IN": "{location}: सध्या हवामान सेवेतून डेटा मिळाला नाही. सेवा समस्या लॉग झाली आहे, कृपया थोड्या वेळाने पुन्हा विचारा.",
    },
    "crop_need_location": {
        "en-IN": "For crop recommendation I need at least village/pincode or farm location. Share it once; then I will use stored soil, rainfall and satellite/public data.",
        "hi-IN": "फसल सुझाव के लिए कम से कम गांव/पिनकोड या खेत की लोकेशन चाहिए। एक बार भेजें, फिर मैं मिट्टी, बारिश और सैटेलाइट/सरकारी डेटा से सलाह दूंगा।",
        "mr-IN": "पीक सल्ल्यासाठी किमान गाव/पिनकोड किंवा शेताची लोकेशन हवी. एकदा पाठवा, मग माती, पाऊस आणि सॅटेलाइट/सरकारी डेटावरून सल्ला देईन.",
    },
    "crop_recommendation_answer": {
        "en-IN": "{location}: suitable crop options are {crops}. Main reason: {reason}",
        "hi-IN": "{location}: इस इलाके के लिए अच्छे विकल्प हैं: {crops}. मुख्य कारण: {reason}",
        "mr-IN": "{location}: या भागासाठी चांगले पर्याय आहेत: {crops}. मुख्य कारण: {reason}",
    },
    "crop_soil_refine": {
        "en-IN": "If you share soil type or soil-card photo later, I will refine this recommendation.",
        "hi-IN": "बाद में मिट्टी का प्रकार या soil-card फोटो भेजेंगे तो मैं यह सलाह और सटीक कर दूंगा।",
        "mr-IN": "नंतर मातीचा प्रकार किंवा soil-card फोटो पाठवल्यास मी हा सल्ला अजून अचूक करेन.",
    },
    "crop_reason_available_data": {
        "en-IN": "It fits the available regional data.",
        "hi-IN": "यह उपलब्ध क्षेत्रीय डेटा से मेल खाता है.",
        "mr-IN": "हे उपलब्ध प्रादेशिक डेटाशी जुळते.",
    },
    "crop_recommendation_failed": {
        "en-IN": "{location}: I could not complete the data-backed crop recommendation right now. The service issue is logged; share soil/water details if available and ask again.",
        "hi-IN": "{location}: अभी डेटा आधारित फसल सुझाव पूरा नहीं हो पाया। सेवा समस्या लॉग हो गई है; मिट्टी/पानी की जानकारी हो तो भेजें और फिर पूछें।",
        "mr-IN": "{location}: सध्या डेटा आधारित पीक सल्ला पूर्ण झाला नाही. सेवा समस्या लॉग झाली आहे; माती/पाणी माहिती असल्यास पाठवा आणि पुन्हा विचारा.",
    },
    "water_need_location": {
        "en-IN": "For irrigation advice I need farm location or pincode once, because rainfall and soil-moisture forecast depend on location.",
        "hi-IN": "सिंचाई सलाह के लिए खेत की लोकेशन या पिनकोड एक बार चाहिए, क्योंकि बारिश और मिट्टी नमी का अंदाज लोकेशन पर निर्भर है।",
        "mr-IN": "पाणी सल्ल्यासाठी शेताची लोकेशन किंवा पिनकोड एकदा हवा, कारण पाऊस आणि माती ओलावा अंदाज लोकेशनवर अवलंबून असतो.",
    },
    "irrigation_answer": {
        "en-IN": "{location}: irrigation risk is {risk}. Dry days expected: {dry_days}. Suggested irrigation: {irrigation} mm. {advisory}",
        "hi-IN": "{location}: सिंचाई का जोखिम {risk} है। अगले दिनों में सूखे दिन: {dry_days}. जरूरत हो तो लगभग {irrigation} mm पानी दें। {advisory}",
        "mr-IN": "{location}: पाणी देण्याचा धोका {risk} आहे. पुढील दिवसांत कोरडे दिवस: {dry_days}. गरज असल्यास सुमारे {irrigation} mm पाणी द्या. {advisory}",
    },
    "crop_plan_missing": {
        "en-IN": "I noted {crop}. To give time-to-time advisory, please tell {missing}. Example: planted 2 weeks ago, variety M35-1.",
        "hi-IN": "मैंने {crop} नोट कर लिया। समय-समय पर सही सलाह के लिए {missing} बताएं। जैसे: 2 हफ्ते पहले लगाया, variety M35-1.",
        "mr-IN": "{crop} नोंदवले. वेळोवेळी योग्य सल्ल्यासाठी {missing} सांगा. उदा. 2 आठवडे आधी पेरणी केली, वाण M35-1.",
    },
    "crop_plan_saved": {
        "en-IN": "{crop} crop plan is saved. Planting date: {date}, variety: {variety}. I will use this for stage-wise weather, irrigation and crop-health alerts.",
        "hi-IN": "{crop} की crop planning सेव हो गई। लगाने की तारीख: {date}, variety: {variety}. अब इसी से stage-wise मौसम, सिंचाई और बीमारी अलर्ट दूंगा।",
        "mr-IN": "{crop} चे crop planning सेव झाले. पेरणी तारीख: {date}, वाण: {variety}. आता यावरून stage-wise हवामान, पाणी आणि रोग अलर्ट देईन.",
    },
    "diagnosis_result": {
        "en-IN": "{issue}. {action} Expert follow-up Ticket: {ticket}.",
        "hi-IN": "{issue}. {action} विशेषज्ञ फॉलो-अप टिकट: {ticket}.",
        "mr-IN": "{issue}. {action} तज्ञ फॉलो-अप तिकीट: {ticket}.",
    },
    "open_ticket_status": {
        "en-IN": "Open expert ticket {ticket}: {issue}. Current status: {status}.",
        "hi-IN": "खुला विशेषज्ञ टिकट {ticket}: {issue}. वर्तमान स्थिति: {status}.",
        "mr-IN": "उघडे तज्ञ तिकीट {ticket}: {issue}. सध्याची स्थिती: {status}.",
    },
    "identity_response": {
        "en-IN": "I know you by this phone number as {name}. If you share village, crop and farm location, I will remember it for the next advice.",
        "hi-IN": "मैं आपको इस फोन नंबर से {name} के रूप में पहचानता हूं। आप गांव, फसल और खेत की लोकेशन बताएंगे तो अगली सलाह में याद रखूंगा।",
        "mr-IN": "मी तुम्हाला या फोन नंबरवरून {name} म्हणून ओळखतो. गाव, पीक आणि शेताची लोकेशन दिल्यास पुढच्या सल्ल्यासाठी लक्षात ठेवेन.",
        "te-IN": "ఈ ఫోన్ నంబర్ ద్వారా మిమ్మల్ని {name}గా గుర్తిస్తున్నాను. గ్రామం, పంట, పొలం లొకేషన్ ఇస్తే తదుపరి సలహాకు గుర్తుంచుకుంటాను.",
        "ta-IN": "இந்த தொலைபேசி எண்ணால் உங்களை {name} என்று அறிகிறேன். கிராமம், பயிர், நில இடம் சொன்னால் அடுத்த ஆலோசனையில் நினைவில் வைப்பேன்.",
        "kn-IN": "ಈ ಫೋನ್ ಸಂಖ್ಯೆಯಿಂದ ನಿಮ್ಮನ್ನು {name} ಎಂದು ಗುರುತಿಸಿದ್ದೇನೆ. ಗ್ರಾಮ, ಬೆಳೆ, ಹೊಲದ ಸ್ಥಳ ಹೇಳಿದರೆ ಮುಂದಿನ ಸಲಹೆಗೆ ಉಳಿಸುತ್ತೇನೆ.",
        "gu-IN": "આ ફોન નંબરથી તમને {name} તરીકે ઓળખું છું. ગામ, પાક અને ખેતરની લોકેશન આપશો તો આગળની સલાહમાં યાદ રાખીશ.",
    },
    "crop_followup_ack": {
        "en-IN": "Good. I noted this crop detail. For a better crop recommendation, also tell water availability and soil type, or share farm location.",
        "hi-IN": "ठीक है, मैंने यह फसल जानकारी नोट कर ली। बेहतर फसल सलाह के लिए पानी की उपलब्धता और मिट्टी का प्रकार भी बताएं, या खेत की लोकेशन भेजें।",
        "mr-IN": "ठीक आहे, मी ही पीक माहिती नोंदवली. चांगल्या पीक सल्ल्यासाठी पाण्याची उपलब्धता आणि मातीचा प्रकार सांगा किंवा शेताची लोकेशन पाठवा.",
        "te-IN": "సరే, ఈ పంట వివరాన్ని గమనించాను. మంచి పంట సలహా కోసం నీటి లభ్యత మరియు నేల రకం కూడా చెప్పండి.",
        "ta-IN": "சரி, இந்த பயிர் தகவலை குறித்துக் கொண்டேன். நல்ல பரிந்துரைக்கு நீர் கிடைக்கும் நிலை மற்றும் மண் வகையும் சொல்லுங்கள்.",
        "kn-IN": "ಸರಿ, ಈ ಬೆಳೆ ವಿವರವನ್ನು ದಾಖಲಿಸಿದೆ. ಉತ್ತಮ ಸಲಹೆಗೆ ನೀರಿನ ಲಭ್ಯತೆ ಮತ್ತು ಮಣ್ಣಿನ ಪ್ರಕಾರವೂ ಹೇಳಿ.",
        "gu-IN": "બરાબર, આ પાક માહિતી નોંધેલી છે. સારી ભલામણ માટે પાણીની ઉપલબ્ધતા અને માટીનો પ્રકાર પણ કહો.",
    },
    "water_followup_ack": {
        "en-IN": "Good. I noted water/rain information. Tell crop name and farm location so I can give a specific irrigation or crop recommendation.",
        "hi-IN": "ठीक है, मैंने पानी/बारिश की जानकारी नोट कर ली। फसल का नाम और खेत की लोकेशन बताएं ताकि सही सिंचाई या फसल सलाह दे सकूं।",
        "mr-IN": "ठीक आहे, मी पाणी/पाऊस माहिती नोंदवली. पिकाचे नाव आणि शेताची लोकेशन सांगा म्हणजे योग्य पाणी किंवा पीक सल्ला देऊ शकतो.",
        "te-IN": "సరే, నీరు/వర్షం వివరాన్ని గమనించాను. పంట పేరు మరియు పొలం లొకేషన్ చెప్పండి.",
        "ta-IN": "சரி, நீர்/மழை தகவலை குறித்துக் கொண்டேன். சரியான ஆலோசனைக்கு பயிர் பெயர் மற்றும் நில இடம் சொல்லுங்கள்.",
        "kn-IN": "ಸರಿ, ನೀರು/ಮಳೆ ಮಾಹಿತಿಯನ್ನು ದಾಖಲಿಸಿದೆ. ಸರಿಯಾದ ಸಲಹೆಗೆ ಬೆಳೆ ಹೆಸರು ಮತ್ತು ಹೊಲದ ಸ್ಥಳ ಹೇಳಿ.",
        "gu-IN": "બરાબર, પાણી/વરસાદ માહિતી નોંધેલી છે. યોગ્ય સલાહ માટે પાકનું નામ અને ખેતરની લોકેશન કહો.",
    },
    "voice_transcription_needed": {
        "en-IN": "Voice received. Speech service is not available right now, so please type the same question once.",
        "hi-IN": "आवाज मिला। अभी speech service उपलब्ध नहीं है, कृपया वही सवाल एक बार लिखकर भेजें।",
        "mr-IN": "आवाज मिळाला. सध्या आवाज ओळख सेवा उपलब्ध नाही, कृपया तोच प्रश्न एकदा लिहून पाठवा.",
        "te-IN": "వాయిస్ వచ్చింది. ప్రస్తుతం speech service లేదు, దయచేసి అదే ప్రశ్నను ఒకసారి టైప్ చేసి పంపండి.",
    },
    "farmer_default_name": {
        "en-IN": "Farmer",
        "hi-IN": "किसान",
        "mr-IN": "शेतकरी",
        "te-IN": "రైతు",
        "ta-IN": "விவசாயி",
        "kn-IN": "ರೈತ",
        "gu-IN": "ખેડૂત",
    },
}


def language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code)


def phrase(key: str, locale: str, **kwargs: object) -> str:
    localized = PHRASES.get(key, {})
    template = localized.get(locale) or localized.get("en-IN") or key
    return template.format(**kwargs)


def infer_message_language(text: str | None, fallback: str | None = None) -> str | None:
    normalized = (text or "").strip().lower()
    if not normalized:
        return fallback

    if any("\u0900" <= char <= "\u097f" for char in normalized):
        if any(token in normalized for token in ["आहे", "माझ", "सांगा", "हवामान", "पीक", "पाणी"]):
            return "mr-IN"
        return "hi-IN"
    if any("\u0a80" <= char <= "\u0aff" for char in normalized):
        return "gu-IN"
    if any("\u0b80" <= char <= "\u0bff" for char in normalized):
        return "ta-IN"
    if any("\u0c00" <= char <= "\u0c7f" for char in normalized):
        return "te-IN"
    if any("\u0c80" <= char <= "\u0cff" for char in normalized):
        return "kn-IN"

    hindi_roman = [
        "aaj", "kal", "mausam", "hindi", "mein", "batao", "pani", "barish", "fasal",
        "kheti", "lagani", "sichai", "kaise", "kya", "kab", "kisan",
    ]
    marathi_roman = [
        "marathi", "madhe", "sanga", "havaman", "pavus", "paani", "pik", "jwari",
        "bajri", "lagvad", "shet", "maza", "majha",
    ]
    if any(token in normalized for token in marathi_roman):
        return "mr-IN"
    if any(token in normalized for token in hindi_roman):
        return "hi-IN"
    return fallback
