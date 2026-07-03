import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

const apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8080',
);

void main() {
  runApp(const KisanAlertChatApp());
}

class KisanAlertChatApp extends StatelessWidget {
  const KisanAlertChatApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Kisan Alert',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF0B7A3B)),
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFFF7F5EE),
      ),
      home: const ChatShell(),
    );
  }
}

class ChatShell extends StatefulWidget {
  const ChatShell({super.key});

  @override
  State<ChatShell> createState() => _ChatShellState();
}

class _ChatShellState extends State<ChatShell> {
  String? phone;
  String language = 'hi-IN';

  @override
  Widget build(BuildContext context) {
    if (phone == null) {
      return LoginScreen(
        language: language,
        onStart: (value, selectedLanguage) {
          setState(() {
            phone = value;
            language = selectedLanguage;
          });
        },
      );
    }
    return ChatScreen(
      phone: phone!,
      language: language,
      onLanguageChanged: (value) => setState(() => language = value),
    );
  }
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({
    required this.language,
    required this.onStart,
    super.key,
  });

  final String language;
  final void Function(String phone, String language) onStart;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final phoneController = TextEditingController();
  late String language = widget.language;

  @override
  void dispose() {
    phoneController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(22),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 18),
              Container(
                width: 58,
                height: 58,
                decoration: BoxDecoration(
                  color: const Color(0xFF0B7A3B),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const Icon(Icons.agriculture, color: Colors.white, size: 34),
              ),
              const SizedBox(height: 24),
              const Text(
                'Kisan Alert',
                style: TextStyle(fontSize: 32, fontWeight: FontWeight.w900),
              ),
              const SizedBox(height: 8),
              Text(
                'Start a farmer advisory conversation in your language.',
                style: TextStyle(fontSize: 16, color: Colors.grey.shade700),
              ),
              const SizedBox(height: 28),
              TextField(
                controller: phoneController,
                keyboardType: TextInputType.phone,
                decoration: const InputDecoration(
                  labelText: 'Phone number',
                  prefixIcon: Icon(Icons.phone),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 18),
              const Text('Language', style: TextStyle(fontWeight: FontWeight.w800)),
              const SizedBox(height: 10),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: languageOptions.entries.map((entry) {
                  return ChoiceChip(
                    label: Text(entry.value),
                    selected: language == entry.key,
                    onSelected: (_) => setState(() => language = entry.key),
                  );
                }).toList(),
              ),
              const Spacer(),
              SizedBox(
                width: double.infinity,
                height: 54,
                child: FilledButton(
                  onPressed: () {
                    final value = phoneController.text.trim();
                    if (value.isEmpty) return;
                    widget.onStart(value, language);
                  },
                  child: const Text('Start Conversation'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({
    required this.phone,
    required this.language,
    required this.onLanguageChanged,
    super.key,
  });

  final String phone;
  final String language;
  final ValueChanged<String> onLanguageChanged;

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final inputController = TextEditingController();
  final scrollController = ScrollController();
  final messages = <ChatMessage>[
    ChatMessage(
      text: 'Namaste. Ask about irrigation, crop recommendation, or send crop photo details.',
      mine: false,
    ),
  ];
  bool sending = false;

  @override
  void dispose() {
    inputController.dispose();
    scrollController.dispose();
    super.dispose();
  }

  Future<void> sendText() async {
    final text = inputController.text.trim();
    if (text.isEmpty || sending) return;
    inputController.clear();
    await sendPayload(
      userText: text,
      payload: {
        'from_phone': widget.phone,
        'text': text,
        'language': widget.language,
      },
    );
  }

  Future<void> shareLocation() async {
    await sendPayload(
      userText: 'Shared farm location',
      payload: {
        'from_phone': widget.phone,
        'language': widget.language,
        'latitude': 16.3,
        'longitude': 80.4,
        'location_label': 'Demo farm location',
      },
    );
  }

  Future<void> sendPhotoSignal() async {
    await sendPayload(
      userText: 'Crop photo attached: leaf has spots',
      payload: {
        'from_phone': widget.phone,
        'language': widget.language,
        'text': 'crop leaf has spots',
        'media_type': 'image',
        'media_uri': 'demo://crop-photo.jpg',
      },
    );
  }

  Future<void> sendVoiceSignal() async {
    await sendPayload(
      userText: 'Voice note: should I irrigate today?',
      payload: {
        'from_phone': widget.phone,
        'language': widget.language,
        'text': 'Should I irrigate today?',
        'media_type': 'voice',
      },
    );
  }

  Future<void> sendPayload({
    required String userText,
    required Map<String, Object?> payload,
  }) async {
    setState(() {
      sending = true;
      messages.add(ChatMessage(text: userText, mine: true));
    });
    scrollToBottom();
    try {
      final response = await http.post(
        Uri.parse('$apiBaseUrl/api/v1/whatsapp/webhook'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );
      if (response.statusCode >= 400) {
        throw Exception('Backend error ${response.statusCode}');
      }
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      setState(() {
        messages.add(ChatMessage(
          text: (data['reply'] as String?) ?? 'No reply received.',
          mine: false,
          intent: data['intent'] as String?,
        ));
      });
    } catch (error) {
      setState(() {
        messages.add(ChatMessage(
          text: 'Could not reach backend. Check API_BASE_URL and backend server.',
          mine: false,
          intent: 'error',
        ));
      });
    } finally {
      setState(() => sending = false);
      scrollToBottom();
    }
  }

  void scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!scrollController.hasClients) return;
      scrollController.animateTo(
        scrollController.position.maxScrollExtent + 120,
        duration: const Duration(milliseconds: 240),
        curve: Curves.easeOut,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF075E54),
        foregroundColor: Colors.white,
        titleSpacing: 0,
        title: const Row(
          children: [
            CircleAvatar(
              backgroundColor: Color(0xFF128C4A),
              child: Icon(Icons.agriculture, color: Colors.white),
            ),
            SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Kisan Alert', style: TextStyle(fontWeight: FontWeight.w800)),
                  Text('Smart water, crop and advisory', style: TextStyle(fontSize: 12)),
                ],
              ),
            ),
          ],
        ),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.translate),
            initialValue: widget.language,
            onSelected: widget.onLanguageChanged,
            itemBuilder: (context) => languageOptions.entries
                .map((entry) => PopupMenuItem(value: entry.key, child: Text(entry.value)))
                .toList(),
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: scrollController,
              padding: const EdgeInsets.fromLTRB(14, 16, 14, 8),
              itemCount: messages.length,
              itemBuilder: (context, index) => MessageBubble(message: messages[index]),
            ),
          ),
          if (sending) const LinearProgressIndicator(minHeight: 2),
          SafeArea(
            top: false,
            child: Container(
              padding: const EdgeInsets.fromLTRB(8, 8, 8, 10),
              decoration: BoxDecoration(
                color: Colors.white,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.06),
                    blurRadius: 12,
                    offset: const Offset(0, -2),
                  ),
                ],
              ),
              child: Row(
                children: [
                  IconButton(
                    tooltip: 'Share location',
                    onPressed: sending ? null : shareLocation,
                    icon: const Icon(Icons.location_on_outlined),
                  ),
                  IconButton(
                    tooltip: 'Attach crop photo',
                    onPressed: sending ? null : sendPhotoSignal,
                    icon: const Icon(Icons.camera_alt_outlined),
                  ),
                  Expanded(
                    child: TextField(
                      controller: inputController,
                      minLines: 1,
                      maxLines: 4,
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => sendText(),
                      decoration: const InputDecoration(
                        hintText: 'Type a message...',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.all(Radius.circular(24)),
                        ),
                        contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      ),
                    ),
                  ),
                  IconButton(
                    tooltip: 'Voice note demo',
                    onPressed: sending ? null : sendVoiceSignal,
                    icon: const Icon(Icons.mic_none),
                  ),
                  IconButton.filled(
                    tooltip: 'Send',
                    onPressed: sending ? null : sendText,
                    icon: const Icon(Icons.send),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class MessageBubble extends StatelessWidget {
  const MessageBubble({required this.message, super.key});

  final ChatMessage message;

  @override
  Widget build(BuildContext context) {
    final color = message.mine ? const Color(0xFFD9FDD3) : Colors.white;
    final alignment = message.mine ? Alignment.centerRight : Alignment.centerLeft;
    return Align(
      alignment: alignment,
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.78),
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 5),
          padding: const EdgeInsets.fromLTRB(13, 10, 13, 8),
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(12),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 7,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(message.text, style: const TextStyle(fontSize: 15.5, height: 1.35)),
              if (message.intent != null) ...[
                const SizedBox(height: 6),
                Text(
                  message.intent!,
                  style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class ChatMessage {
  ChatMessage({
    required this.text,
    required this.mine,
    this.intent,
  });

  final String text;
  final bool mine;
  final String? intent;
}

const languageOptions = {
  'en-IN': 'English',
  'hi-IN': 'हिन्दी',
  'mr-IN': 'मराठी',
  'te-IN': 'తెలుగు',
  'ta-IN': 'தமிழ்',
  'kn-IN': 'ಕನ್ನಡ',
  'gu-IN': 'ગુજરાતી',
};
