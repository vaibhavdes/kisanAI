enum ChatRole { farmer, assistant, system }

enum RequiredAction { none, location, farmSelection }

enum MediaIntent { camera, gallery, soilCard, voiceNote }

class LanguageOption {
  const LanguageOption({
    required this.code,
    required this.nativeName,
    required this.englishName,
  });

  final String code;
  final String nativeName;
  final String englishName;
}

class FarmerSession {
  const FarmerSession({
    required this.phone,
    required this.language,
    this.locationShared = false,
    this.farmSelected = false,
  });

  final String phone;
  final LanguageOption language;
  final bool locationShared;
  final bool farmSelected;

  FarmerSession copyWith({
    String? phone,
    LanguageOption? language,
    bool? locationShared,
    bool? farmSelected,
  }) {
    return FarmerSession(
      phone: phone ?? this.phone,
      language: language ?? this.language,
      locationShared: locationShared ?? this.locationShared,
      farmSelected: farmSelected ?? this.farmSelected,
    );
  }
}

class ChatMessage {
  const ChatMessage({
    required this.id,
    required this.role,
    required this.text,
    required this.time,
    this.action = RequiredAction.none,
    this.mediaLabel,
  });

  final String id;
  final ChatRole role;
  final String text;
  final DateTime time;
  final RequiredAction action;
  final String? mediaLabel;

  bool get isFarmer => role == ChatRole.farmer;
}

