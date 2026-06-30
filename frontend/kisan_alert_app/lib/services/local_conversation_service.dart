import '../models/app_models.dart';

class LocalConversationService {
  RequiredAction requiredActionFor(String text, FarmerSession session) {
    final normalized = text.toLowerCase();
    final asksLocation = normalized.contains('weather') ||
        normalized.contains('rain') ||
        normalized.contains('pincode') ||
        normalized.contains('हवामान') ||
        normalized.contains('पाऊस') ||
        normalized.contains('मौसम') ||
        normalized.contains('बारिश');

    if (asksLocation && !session.locationShared) return RequiredAction.location;

    final asksFarm = normalized.contains('satellite') ||
        normalized.contains('ndvi') ||
        normalized.contains('map') ||
        normalized.contains('farm') ||
        normalized.contains('शेत') ||
        normalized.contains('खेत') ||
        normalized.contains('नकाशा');

    if (asksFarm && !session.farmSelected) return RequiredAction.farmSelection;
    return RequiredAction.none;
  }

  String greetingFor(LanguageOption language) {
    return switch (language.code) {
      'mr-IN' => 'नमस्कार! तुमचा प्रश्न लिहा किंवा फोटो/आवाज पाठवा.',
      'hi-IN' => 'नमस्ते! अपना सवाल लिखें या फोटो/आवाज भेजें।',
      'te-IN' => 'నమస్కారం! మీ ప్రశ్న టైప్ చేయండి లేదా ఫోటో/వాయిస్ పంపండి.',
      'ta-IN' => 'வணக்கம்! உங்கள் கேள்வியை எழுதுங்கள் அல்லது படம்/குரல் அனுப்புங்கள்.',
      'kn-IN' => 'ನಮಸ್ಕಾರ! ನಿಮ್ಮ ಪ್ರಶ್ನೆ ಬರೆಯಿರಿ ಅಥವಾ ಫೋಟೋ/ಧ್ವನಿ ಕಳುಹಿಸಿ.',
      'gu-IN' => 'નમસ્તે! તમારો પ્રશ્ન લખો અથવા ફોટો/અવાજ મોકલો.',
      _ => 'Hello! Ask your farm question or send a photo/voice note.',
    };
  }

  String replyFor(String text, FarmerSession session, RequiredAction action) {
    if (action == RequiredAction.location) {
      return _localized(
        session.language.code,
        en: 'Please share your location once so I can check local weather and alerts.',
        hi: 'स्थानीय मौसम और चेतावनी देखने के लिए कृपया एक बार लोकेशन शेयर करें।',
        mr: 'स्थानिक हवामान आणि सूचना पाहण्यासाठी कृपया एकदा लोकेशन शेअर करा.',
        te: 'స్థానిక వాతావరణం కోసం దయచేసి ఒకసారి మీ లొకేషన్ షేర్ చేయండి.',
      );
    }
    if (action == RequiredAction.farmSelection) {
      return _localized(
        session.language.code,
        en: 'Please select your farm on the map so satellite advice is accurate.',
        hi: 'सैटेलाइट सलाह सही मिले इसलिए कृपया नक्शे पर अपना खेत चुनें।',
        mr: 'सॅटेलाइट सल्ला अचूक मिळण्यासाठी नकाशावर तुमचे शेत निवडा.',
        te: 'ఉపగ్రహ సలహా ఖచ్చితంగా రావడానికి మ్యాప్‌లో మీ పొలం ఎంచుకోండి.',
      );
    }
    return _localized(
      session.language.code,
      en: 'I understood. In the full version I will check weather, crop stage, soil and expert data before replying.',
      hi: 'मैं समझ गया। पूर्ण संस्करण में मौसम, फसल अवस्था, मिट्टी और विशेषज्ञ डेटा देखकर जवाब दूंगा।',
      mr: 'मला समजले. पूर्ण आवृत्तीत हवामान, पीक अवस्था, माती आणि तज्ञ डेटा पाहून उत्तर देईन.',
      te: 'అర్థమైంది. పూర్తి వెర్షన్‌లో వాతావరణం, పంట దశ, నేల మరియు నిపుణుల డేటాతో సమాధానం ఇస్తాను.',
    );
  }

  String _localized(
    String code, {
    required String en,
    required String hi,
    required String mr,
    required String te,
  }) {
    return switch (code) {
      'hi-IN' => hi,
      'mr-IN' => mr,
      'te-IN' => te,
      _ => en,
    };
  }
}

