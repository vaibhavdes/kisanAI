export const autoLanguageCode = "auto";

type UiCopy = {
  appName: string;
  appTagline: string;
  farmerPhone: string;
  phoneRequiredTitle: string;
  phoneRequiredMessage: string;
  replyLanguage: string;
  autoLanguage: string;
  autoLanguageHint: string;
  suggestedLanguage: string;
  startChat: string;
  chatOnWhatsApp: string;
  whatsAppSandboxHint: string;
  whatsAppSandboxCode: string;
  whatsAppOpenFailedTitle: string;
  whatsAppOpenFailedMessage: string;
  welcome: string;
  autoLanguageShort: string;
  backendFailed: string;
  locationPermissionTitle: string;
  locationPermissionMessage: string;
  locationShared: string;
  locationLabel: string;
  photoPermissionTitle: string;
  photoPermissionMessage: string;
  photoUploadFailedTitle: string;
  photoUploadFailedMessage: string;
  cropPhotoCaption: string;
  microphonePermissionTitle: string;
  microphonePermissionMessage: string;
  voiceFailedTitle: string;
  voiceFailedMessage: string;
  voiceUploadFailedMessage: string;
  recordingPlaceholder: string;
  messagePlaceholder: string;
  camera: string;
  gallery: string;
  location: string;
  farmLocation: string;
  voice: string;
  heard: string;
  voiceNote: (seconds: number) => string;
};

const copies: Record<string, UiCopy> = {
  "en-IN": {
    appName: "Kisan Alert",
    appTagline: "Farmer advisory chat for voice, crop photos, location, SMS and calls.",
    farmerPhone: "Farmer phone",
    phoneRequiredTitle: "Phone number required",
    phoneRequiredMessage: "Enter the farmer phone number to start.",
    replyLanguage: "Reply language",
    autoLanguage: "Auto",
    autoLanguageHint: "Auto detects the farmer language from the message when language services are enabled.",
    suggestedLanguage: "Suggested from your state",
    startChat: "Start chat",
    chatOnWhatsApp: "Chat on WhatsApp",
    whatsAppSandboxHint: "Use WhatsApp and send a message from your device to +1 415 523 8886.",
    whatsAppSandboxCode: "Code: join first-dig",
    whatsAppOpenFailedTitle: "Could not open WhatsApp",
    whatsAppOpenFailedMessage: "Open WhatsApp and send \"join first-dig\" to +1 415 523 8886.",
    welcome: "Namaste. Send a message, crop photo, voice note, or farm location.",
    autoLanguageShort: "Auto language",
    backendFailed: "Could not reach backend",
    locationPermissionTitle: "Location permission needed",
    locationPermissionMessage: "Allow location to share the farm point.",
    locationShared: "Farm location shared",
    locationLabel: "Shared from Kisan Alert app",
    photoPermissionTitle: "Photo permission needed",
    photoPermissionMessage: "Allow photo access to send a crop image.",
    photoUploadFailedTitle: "Photo could not be sent",
    photoUploadFailedMessage: "Please choose or capture the photo again so it can be uploaded.",
    cropPhotoCaption: "Crop photo for diagnosis",
    microphonePermissionTitle: "Microphone permission needed",
    microphonePermissionMessage: "Allow microphone access to send a voice note.",
    voiceFailedTitle: "Voice note failed",
    voiceFailedMessage: "Recording finished but no audio file was created.",
    voiceUploadFailedMessage: "The recording could not be prepared for upload. Please record again.",
    recordingPlaceholder: "Recording voice note...",
    messagePlaceholder: "Message",
    camera: "Camera",
    gallery: "Gallery",
    location: "Location",
    farmLocation: "Farm location",
    voice: "Voice",
    heard: "Heard",
    voiceNote: (seconds) => `Voice note ${seconds}s`,
  },
  "hi-IN": {
    appName: "Kisan Alert",
    appTagline: "आवाज, फसल फोटो, लोकेशन, SMS और कॉल के लिए किसान सलाह चैट।",
    farmerPhone: "किसान का फोन नंबर",
    phoneRequiredTitle: "फोन नंबर जरूरी है",
    phoneRequiredMessage: "चैट शुरू करने के लिए किसान का फोन नंबर डालें।",
    replyLanguage: "जवाब की भाषा",
    autoLanguage: "अपने आप",
    autoLanguageHint: "Auto में संदेश से किसान की भाषा पहचानकर जवाब दिया जाएगा।",
    suggestedLanguage: "आपके राज्य के आधार पर सुझाव",
    startChat: "चैट शुरू करें",
    chatOnWhatsApp: "WhatsApp पर चैट करें",
    whatsAppSandboxHint: "अपने फोन के WhatsApp से +1 415 523 8886 पर संदेश भेजें।",
    whatsAppSandboxCode: "कोड: join first-dig",
    whatsAppOpenFailedTitle: "WhatsApp नहीं खुला",
    whatsAppOpenFailedMessage: "WhatsApp खोलकर +1 415 523 8886 पर \"join first-dig\" भेजें।",
    welcome: "नमस्ते। संदेश, फसल फोटो, आवाज या खेत की लोकेशन भेजें।",
    autoLanguageShort: "Auto भाषा",
    backendFailed: "Backend तक पहुंच नहीं हो पाई",
    locationPermissionTitle: "लोकेशन अनुमति चाहिए",
    locationPermissionMessage: "खेत की लोकेशन भेजने के लिए अनुमति दें।",
    locationShared: "खेत की लोकेशन भेजी गई",
    locationLabel: "Kisan Alert ऐप से भेजी गई लोकेशन",
    photoPermissionTitle: "फोटो अनुमति चाहिए",
    photoPermissionMessage: "फसल की फोटो भेजने के लिए फोटो अनुमति दें।",
    photoUploadFailedTitle: "फोटो नहीं भेजी जा सकी",
    photoUploadFailedMessage: "कृपया फोटो फिर से चुनें या कैमरे से लें ताकि वह अपलोड हो सके।",
    cropPhotoCaption: "फसल फोटो जांच के लिए",
    microphonePermissionTitle: "माइक्रोफोन अनुमति चाहिए",
    microphonePermissionMessage: "आवाज संदेश भेजने के लिए माइक्रोफोन अनुमति दें।",
    voiceFailedTitle: "आवाज संदेश नहीं बना",
    voiceFailedMessage: "रिकॉर्डिंग पूरी हुई, लेकिन ऑडियो फाइल नहीं बनी।",
    voiceUploadFailedMessage: "रिकॉर्डिंग अपलोड के लिए तैयार नहीं हो पाई। कृपया फिर से रिकॉर्ड करें।",
    recordingPlaceholder: "आवाज रिकॉर्ड हो रही है...",
    messagePlaceholder: "संदेश",
    camera: "कैमरा",
    gallery: "गैलरी",
    location: "लोकेशन",
    farmLocation: "खेत की लोकेशन",
    voice: "आवाज",
    heard: "सुना गया",
    voiceNote: (seconds) => `आवाज संदेश ${seconds}s`,
  },
  "mr-IN": {
    appName: "Kisan Alert",
    appTagline: "आवाज, पिकाचे फोटो, लोकेशन, SMS आणि कॉलसाठी शेतकरी सल्ला चॅट.",
    farmerPhone: "शेतकऱ्याचा फोन",
    phoneRequiredTitle: "फोन नंबर आवश्यक आहे",
    phoneRequiredMessage: "चॅट सुरू करण्यासाठी शेतकऱ्याचा फोन नंबर टाका.",
    replyLanguage: "उत्तराची भाषा",
    autoLanguage: "आपोआप",
    autoLanguageHint: "Auto मध्ये संदेशावरून शेतकऱ्याची भाषा ओळखून उत्तर दिले जाईल.",
    suggestedLanguage: "तुमच्या राज्यावरून सुचवलेली भाषा",
    startChat: "चॅट सुरू करा",
    chatOnWhatsApp: "WhatsApp वर चॅट करा",
    whatsAppSandboxHint: "तुमच्या फोनच्या WhatsApp वरून +1 415 523 8886 ला संदेश पाठवा.",
    whatsAppSandboxCode: "कोड: join first-dig",
    whatsAppOpenFailedTitle: "WhatsApp उघडता आले नाही",
    whatsAppOpenFailedMessage: "WhatsApp उघडून +1 415 523 8886 ला \"join first-dig\" पाठवा.",
    welcome: "नमस्कार. संदेश, पिकाचा फोटो, आवाज किंवा शेताची लोकेशन पाठवा.",
    autoLanguageShort: "Auto भाषा",
    backendFailed: "Backend पर्यंत पोहोचता आले नाही",
    locationPermissionTitle: "लोकेशन परवानगी हवी",
    locationPermissionMessage: "शेताची लोकेशन पाठवण्यासाठी परवानगी द्या.",
    locationShared: "शेताची लोकेशन पाठवली",
    locationLabel: "Kisan Alert अॅपवरून पाठवलेली लोकेशन",
    photoPermissionTitle: "फोटो परवानगी हवी",
    photoPermissionMessage: "पिकाचा फोटो पाठवण्यासाठी फोटो परवानगी द्या.",
    photoUploadFailedTitle: "फोटो पाठवता आली नाही",
    photoUploadFailedMessage: "कृपया फोटो पुन्हा निवडा किंवा कॅमेराने घ्या म्हणजे ती अपलोड होईल.",
    cropPhotoCaption: "पिकाचा फोटो तपासणीसाठी",
    microphonePermissionTitle: "मायक्रोफोन परवानगी हवी",
    microphonePermissionMessage: "आवाज संदेश पाठवण्यासाठी मायक्रोफोन परवानगी द्या.",
    voiceFailedTitle: "आवाज संदेश तयार झाला नाही",
    voiceFailedMessage: "रेकॉर्डिंग पूर्ण झाले, पण ऑडिओ फाइल तयार झाली नाही.",
    voiceUploadFailedMessage: "रेकॉर्डिंग अपलोडसाठी तयार करता आली नाही. कृपया पुन्हा रेकॉर्ड करा.",
    recordingPlaceholder: "आवाज रेकॉर्ड होत आहे...",
    messagePlaceholder: "संदेश",
    camera: "कॅमेरा",
    gallery: "गॅलरी",
    location: "लोकेशन",
    farmLocation: "शेताची लोकेशन",
    voice: "आवाज",
    heard: "ऐकले",
    voiceNote: (seconds) => `आवाज संदेश ${seconds}s`,
  },
  "te-IN": {
    appName: "Kisan Alert",
    appTagline: "వాయిస్, పంట ఫోటోలు, లొకేషన్, SMS మరియు కాల్‌లకు రైతు సలహా చాట్.",
    farmerPhone: "రైతు ఫోన్",
    phoneRequiredTitle: "ఫోన్ నంబర్ అవసరం",
    phoneRequiredMessage: "చాట్ ప్రారంభించడానికి రైతు ఫోన్ నంబర్ నమోదు చేయండి.",
    replyLanguage: "జవాబు భాష",
    autoLanguage: "ఆటో",
    autoLanguageHint: "Auto లో సందేశం ఆధారంగా రైతు భాషను గుర్తించి జవాబు ఇస్తుంది.",
    suggestedLanguage: "మీ రాష్ట్రం ఆధారంగా సూచన",
    startChat: "చాట్ ప్రారంభించండి",
    chatOnWhatsApp: "WhatsAppలో చాట్ చేయండి",
    whatsAppSandboxHint: "మీ ఫోన్‌లో WhatsApp నుండి +1 415 523 8886కి సందేశం పంపండి.",
    whatsAppSandboxCode: "కోడ్: join first-dig",
    whatsAppOpenFailedTitle: "WhatsApp తెరవలేకపోయాం",
    whatsAppOpenFailedMessage: "WhatsApp తెరిచి +1 415 523 8886కి \"join first-dig\" పంపండి.",
    welcome: "నమస్తే. సందేశం, పంట ఫోటో, వాయిస్ నోట్ లేదా పొలం లొకేషన్ పంపండి.",
    autoLanguageShort: "Auto భాష",
    backendFailed: "Backend చేరుకోలేకపోయాం",
    locationPermissionTitle: "లొకేషన్ అనుమతి కావాలి",
    locationPermissionMessage: "పొలం పాయింట్ పంపడానికి లొకేషన్ అనుమతి ఇవ్వండి.",
    locationShared: "పొలం లొకేషన్ పంపబడింది",
    locationLabel: "Kisan Alert app నుండి పంపిన లొకేషన్",
    photoPermissionTitle: "ఫోటో అనుమతి కావాలి",
    photoPermissionMessage: "పంట చిత్రం పంపడానికి ఫోటో అనుమతి ఇవ్వండి.",
    photoUploadFailedTitle: "ఫోటో పంపలేకపోయాం",
    photoUploadFailedMessage: "అప్లోడ్ చేయడానికి ఫోటోను మళ్లీ ఎంచుకోండి లేదా కెమెరాతో తీసుకోండి.",
    cropPhotoCaption: "పంట వ్యాధి పరీక్ష కోసం ఫోటో",
    microphonePermissionTitle: "మైక్రోఫోన్ అనుమతి కావాలి",
    microphonePermissionMessage: "వాయిస్ నోట్ పంపడానికి మైక్రోఫోన్ అనుమతి ఇవ్వండి.",
    voiceFailedTitle: "వాయిస్ నోట్ విఫలమైంది",
    voiceFailedMessage: "రికార్డింగ్ పూర్తయింది కానీ ఆడియో ఫైల్ రాలేదు.",
    voiceUploadFailedMessage: "రికార్డింగ్ అప్లోడ్‌కు సిద్ధం కాలేదు. దయచేసి మళ్లీ రికార్డ్ చేయండి.",
    recordingPlaceholder: "వాయిస్ రికార్డ్ అవుతోంది...",
    messagePlaceholder: "సందేశం",
    camera: "కెమెరా",
    gallery: "గ్యాలరీ",
    location: "లొకేషన్",
    farmLocation: "పొలం లొకేషన్",
    voice: "వాయిస్",
    heard: "విన్నది",
    voiceNote: (seconds) => `వాయిస్ నోట్ ${seconds}s`,
  },
  "ta-IN": {
    appName: "Kisan Alert",
    appTagline: "குரல், பயிர் புகைப்படம், இடம், SMS மற்றும் அழைப்புகளுக்கான விவசாயி ஆலோசனை அரட்டை.",
    farmerPhone: "விவசாயி தொலைபேசி",
    phoneRequiredTitle: "தொலைபேசி எண் தேவை",
    phoneRequiredMessage: "அரட்டை தொடங்க விவசாயியின் தொலைபேசி எண்ணை உள்ளிடுங்கள்.",
    replyLanguage: "பதில் மொழி",
    autoLanguage: "Auto",
    autoLanguageHint: "Auto-வில் செய்தியிலிருந்து விவசாயியின் மொழியை அறிந்து பதில் தரப்படும்.",
    suggestedLanguage: "உங்கள் மாநிலத்தின் அடிப்படையில் பரிந்துரை",
    startChat: "அரட்டை தொடங்கு",
    chatOnWhatsApp: "WhatsApp-ல் அரட்டை",
    whatsAppSandboxHint: "உங்கள் தொலைபேசியில் WhatsApp-ல் இருந்து +1 415 523 8886-க்கு செய்தி அனுப்புங்கள்.",
    whatsAppSandboxCode: "குறியீடு: join first-dig",
    whatsAppOpenFailedTitle: "WhatsApp திறக்க முடியவில்லை",
    whatsAppOpenFailedMessage: "WhatsApp திறந்து +1 415 523 8886-க்கு \"join first-dig\" அனுப்புங்கள்.",
    welcome: "வணக்கம். செய்தி, பயிர் புகைப்படம், குரல் குறிப்போ அல்லது நில இடமோ அனுப்புங்கள்.",
    autoLanguageShort: "Auto மொழி",
    backendFailed: "Backend-ஐ அணுக முடியவில்லை",
    locationPermissionTitle: "இட அனுமதி தேவை",
    locationPermissionMessage: "நில இடத்தை பகிர அனுமதி அளிக்கவும்.",
    locationShared: "நில இடம் பகிரப்பட்டது",
    locationLabel: "Kisan Alert app மூலம் பகிரப்பட்ட இடம்",
    photoPermissionTitle: "புகைப்பட அனுமதி தேவை",
    photoPermissionMessage: "பயிர் புகைப்படத்தை அனுப்ப அனுமதி அளிக்கவும்.",
    photoUploadFailedTitle: "புகைப்படம் அனுப்ப முடியவில்லை",
    photoUploadFailedMessage: "பதிவேற்ற மீண்டும் புகைப்படத்தை தேர்வு செய்யுங்கள் அல்லது கேமராவில் எடுக்கவும்.",
    cropPhotoCaption: "பயிர் நோய் ஆய்வுக்கான புகைப்படம்",
    microphonePermissionTitle: "மைக்ரோஃபோன் அனுமதி தேவை",
    microphonePermissionMessage: "குரல் குறிப்பை அனுப்ப மைக்ரோஃபோன் அனுமதி அளிக்கவும்.",
    voiceFailedTitle: "குரல் குறிப்பு தோல்வி",
    voiceFailedMessage: "பதிவு முடிந்தது, ஆனால் audio file உருவாகவில்லை.",
    voiceUploadFailedMessage: "பதிவு upload-க்கு தயாராகவில்லை. தயவுசெய்து மீண்டும் பதிவு செய்யுங்கள்.",
    recordingPlaceholder: "குரல் பதிவு நடக்கிறது...",
    messagePlaceholder: "செய்தி",
    camera: "கேமரா",
    gallery: "கேலரி",
    location: "இடம்",
    farmLocation: "நில இடம்",
    voice: "குரல்",
    heard: "கேட்டது",
    voiceNote: (seconds) => `குரல் குறிப்பு ${seconds}s`,
  },
  "kn-IN": {
    appName: "Kisan Alert",
    appTagline: "ಧ್ವನಿ, ಬೆಳೆ ಫೋಟೋ, ಸ್ಥಳ, SMS ಮತ್ತು ಕರೆಗಳಿಗೆ ರೈತ ಸಲಹೆ ಚಾಟ್.",
    farmerPhone: "ರೈತರ ಫೋನ್",
    phoneRequiredTitle: "ಫೋನ್ ಸಂಖ್ಯೆ ಬೇಕು",
    phoneRequiredMessage: "ಚಾಟ್ ಪ್ರಾರಂಭಿಸಲು ರೈತರ ಫೋನ್ ಸಂಖ್ಯೆ ನಮೂದಿಸಿ.",
    replyLanguage: "ಉತ್ತರ ಭಾಷೆ",
    autoLanguage: "Auto",
    autoLanguageHint: "Auto ನಲ್ಲಿ ಸಂದೇಶದಿಂದ ರೈತರ ಭಾಷೆ ಗುರುತಿಸಿ ಉತ್ತರಿಸಲಾಗುತ್ತದೆ.",
    suggestedLanguage: "ನಿಮ್ಮ ರಾಜ್ಯದ ಆಧಾರದ ಮೇಲೆ ಸೂಚನೆ",
    startChat: "ಚಾಟ್ ಪ್ರಾರಂಭಿಸಿ",
    chatOnWhatsApp: "WhatsAppನಲ್ಲಿ ಚಾಟ್ ಮಾಡಿ",
    whatsAppSandboxHint: "ನಿಮ್ಮ ಫೋನ್‌ನ WhatsApp ಮೂಲಕ +1 415 523 8886 ಗೆ ಸಂದೇಶ ಕಳುಹಿಸಿ.",
    whatsAppSandboxCode: "ಕೋಡ್: join first-dig",
    whatsAppOpenFailedTitle: "WhatsApp ತೆರೆಯಲಿಲ್ಲ",
    whatsAppOpenFailedMessage: "WhatsApp ತೆರೆಯಿರಿ ಮತ್ತು +1 415 523 8886 ಗೆ \"join first-dig\" ಕಳುಹಿಸಿ.",
    welcome: "ನಮಸ್ತೆ. ಸಂದೇಶ, ಬೆಳೆ ಫೋಟೋ, ಧ್ವನಿ ಟಿಪ್ಪಣಿ ಅಥವಾ ಹೊಲದ ಸ್ಥಳ ಕಳುಹಿಸಿ.",
    autoLanguageShort: "Auto ಭಾಷೆ",
    backendFailed: "Backend ಸಂಪರ್ಕ ಆಗಲಿಲ್ಲ",
    locationPermissionTitle: "ಸ್ಥಳ ಅನುಮತಿ ಬೇಕು",
    locationPermissionMessage: "ಹೊಲದ ಸ್ಥಳ ಕಳುಹಿಸಲು ಅನುಮತಿ ನೀಡಿ.",
    locationShared: "ಹೊಲದ ಸ್ಥಳ ಕಳುಹಿಸಲಾಗಿದೆ",
    locationLabel: "Kisan Alert app ನಿಂದ ಕಳುಹಿಸಿದ ಸ್ಥಳ",
    photoPermissionTitle: "ಫೋಟೋ ಅನುಮತಿ ಬೇಕು",
    photoPermissionMessage: "ಬೆಳೆ ಚಿತ್ರ ಕಳುಹಿಸಲು ಫೋಟೋ ಅನುಮತಿ ನೀಡಿ.",
    photoUploadFailedTitle: "ಫೋಟೋ ಕಳುಹಿಸಲಾಗಲಿಲ್ಲ",
    photoUploadFailedMessage: "ಅಪ್ಲೋಡ್ ಮಾಡಲು ಫೋಟೋವನ್ನು ಮತ್ತೆ ಆರಿಸಿ ಅಥವಾ ಕ್ಯಾಮೆರಾದಿಂದ ತೆಗೆದುಕೊಳ್ಳಿ.",
    cropPhotoCaption: "ಬೆಳೆ ಪರೀಕ್ಷೆಗೆ ಫೋಟೋ",
    microphonePermissionTitle: "ಮೈಕ್ರೋಫೋನ್ ಅನುಮತಿ ಬೇಕು",
    microphonePermissionMessage: "ಧ್ವನಿ ಟಿಪ್ಪಣಿ ಕಳುಹಿಸಲು ಮೈಕ್ರೋಫೋನ್ ಅನುಮತಿ ನೀಡಿ.",
    voiceFailedTitle: "ಧ್ವನಿ ಟಿಪ್ಪಣಿ ವಿಫಲ",
    voiceFailedMessage: "ರೆಕಾರ್ಡಿಂಗ್ ಮುಗಿದಿದೆ, ಆದರೆ ಆಡಿಯೋ ಫೈಲ್ ಸಿಗಲಿಲ್ಲ.",
    voiceUploadFailedMessage: "ರೆಕಾರ್ಡಿಂಗ್ ಅಪ್ಲೋಡ್‌ಗೆ ಸಿದ್ಧವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ರೆಕಾರ್ಡ್ ಮಾಡಿ.",
    recordingPlaceholder: "ಧ್ವನಿ ರೆಕಾರ್ಡ್ ಆಗುತ್ತಿದೆ...",
    messagePlaceholder: "ಸಂದೇಶ",
    camera: "ಕ್ಯಾಮೆರಾ",
    gallery: "ಗ್ಯಾಲರಿ",
    location: "ಸ್ಥಳ",
    farmLocation: "ಹೊಲದ ಸ್ಥಳ",
    voice: "ಧ್ವನಿ",
    heard: "ಕೇಳಿದ್ದು",
    voiceNote: (seconds) => `ಧ್ವನಿ ಟಿಪ್ಪಣಿ ${seconds}s`,
  },
  "gu-IN": {
    appName: "Kisan Alert",
    appTagline: "આવાજ, પાક ફોટા, લોકેશન, SMS અને કૉલ માટે ખેડૂત સલાહ ચેટ.",
    farmerPhone: "ખેડૂતનો ફોન",
    phoneRequiredTitle: "ફોન નંબર જરૂરી છે",
    phoneRequiredMessage: "ચેટ શરૂ કરવા ખેડૂતનો ફોન નંબર લખો.",
    replyLanguage: "જવાબની ભાષા",
    autoLanguage: "Auto",
    autoLanguageHint: "Auto માં સંદેશ પરથી ખેડૂતની ભાષા ઓળખીને જવાબ મળશે.",
    suggestedLanguage: "તમારા રાજ્ય પરથી સૂચન",
    startChat: "ચેટ શરૂ કરો",
    chatOnWhatsApp: "WhatsApp પર ચેટ કરો",
    whatsAppSandboxHint: "તમારા ફોનના WhatsApp પરથી +1 415 523 8886 પર સંદેશ મોકલો.",
    whatsAppSandboxCode: "કોડ: join first-dig",
    whatsAppOpenFailedTitle: "WhatsApp ખૂલી શક્યું નહીં",
    whatsAppOpenFailedMessage: "WhatsApp ખોલીને +1 415 523 8886 પર \"join first-dig\" મોકલો.",
    welcome: "નમસ્તે. સંદેશ, પાક ફોટો, અવાજ નોંધ અથવા ખેતરની લોકેશન મોકલો.",
    autoLanguageShort: "Auto ભાષા",
    backendFailed: "Backend સુધી પહોંચી શક્યા નહીં",
    locationPermissionTitle: "લોકેશન પરવાનગી જોઈએ",
    locationPermissionMessage: "ખેતરની લોકેશન મોકલવા પરવાનગી આપો.",
    locationShared: "ખેતરની લોકેશન મોકલાઈ",
    locationLabel: "Kisan Alert app થી મોકલેલી લોકેશન",
    photoPermissionTitle: "ફોટો પરવાનગી જોઈએ",
    photoPermissionMessage: "પાકનો ફોટો મોકલવા ફોટો પરવાનગી આપો.",
    photoUploadFailedTitle: "ફોટો મોકલી શક્યા નહીં",
    photoUploadFailedMessage: "અપલોડ કરવા કૃપા કરીને ફોટો ફરી પસંદ કરો અથવા કેમેરાથી લો.",
    cropPhotoCaption: "પાક તપાસ માટે ફોટો",
    microphonePermissionTitle: "માઇક્રોફોન પરવાનગી જોઈએ",
    microphonePermissionMessage: "અવાજ નોંધ મોકલવા માઇક્રોફોન પરવાનગી આપો.",
    voiceFailedTitle: "અવાજ નોંધ નિષ્ફળ",
    voiceFailedMessage: "રેકોર્ડિંગ પૂરું થયું, પણ ઓડિયો ફાઇલ મળી નહીં.",
    voiceUploadFailedMessage: "રેકોર્ડિંગ અપલોડ માટે તૈયાર થઈ શક્યું નહીં. કૃપા કરીને ફરી રેકોર્ડ કરો.",
    recordingPlaceholder: "અવાજ રેકોર્ડ થઈ રહ્યો છે...",
    messagePlaceholder: "સંદેશ",
    camera: "કેમેરા",
    gallery: "ગેલેરી",
    location: "લોકેશન",
    farmLocation: "ખેતરની લોકેશન",
    voice: "અવાજ",
    heard: "સાંભળ્યું",
    voiceNote: (seconds) => `અવાજ નોંધ ${seconds}s`,
  },
};

export function uiCopy(language: string): UiCopy {
  return copies[language] || copies["en-IN"];
}

export function copyLanguage(language: string): string {
  return language === autoLanguageCode ? "en-IN" : language;
}

export function languageForState(state?: string | null): string | undefined {
  if (!state) return undefined;
  const normalized = state.toLowerCase();
  if (normalized.includes("maharashtra")) return "mr-IN";
  if (normalized.includes("gujarat")) return "gu-IN";
  if (normalized.includes("tamil")) return "ta-IN";
  if (normalized.includes("karnataka")) return "kn-IN";
  if (normalized.includes("telangana") || normalized.includes("andhra")) return "te-IN";
  if (
    normalized.includes("uttar") ||
    normalized.includes("madhya") ||
    normalized.includes("rajasthan") ||
    normalized.includes("bihar") ||
    normalized.includes("haryana") ||
    normalized.includes("himachal") ||
    normalized.includes("jharkhand") ||
    normalized.includes("chhattisgarh") ||
    normalized.includes("delhi")
  ) {
    return "hi-IN";
  }
  return undefined;
}
