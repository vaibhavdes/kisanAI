import 'package:flutter/material.dart';

import '../models/app_models.dart';
import '../services/local_conversation_service.dart';
import '../theme/app_theme.dart';
import '../widgets/chat_bubble.dart';
import '../widgets/chat_composer.dart';
import '../widgets/location_prompt_sheet.dart';
import '../widgets/media_picker_sheet.dart';
import 'farm_map_screen.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key, required this.initialSession});

  final FarmerSession initialSession;

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _conversation = LocalConversationService();
  final _scrollController = ScrollController();
  late FarmerSession _session;
  late final List<ChatMessage> _messages;

  @override
  void initState() {
    super.initState();
    _session = widget.initialSession;
    _messages = [
      ChatMessage(
        id: 'welcome',
        role: ChatRole.assistant,
        text: _conversation.greetingFor(_session.language),
        time: DateTime.now(),
      ),
    ];
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _sendText(String text) {
    final trimmed = text.trim();
    if (trimmed.isEmpty) return;
    final action = _conversation.requiredActionFor(trimmed, _session);
    setState(() {
      _messages.add(
        ChatMessage(
          id: DateTime.now().microsecondsSinceEpoch.toString(),
          role: ChatRole.farmer,
          text: trimmed,
          time: DateTime.now(),
        ),
      );
      _messages.add(
        ChatMessage(
          id: 'reply-${DateTime.now().microsecondsSinceEpoch}',
          role: ChatRole.assistant,
          text: _conversation.replyFor(trimmed, _session, action),
          time: DateTime.now(),
          action: action,
        ),
      );
    });
    _scrollToBottom();

    if (action == RequiredAction.location) {
      Future<void>.delayed(const Duration(milliseconds: 350), _askLocation);
    } else if (action == RequiredAction.farmSelection) {
      Future<void>.delayed(const Duration(milliseconds: 350), _openFarmMap);
    }
  }

  Future<void> _askLocation() async {
    final shared = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      builder: (_) => const LocationPromptSheet(),
    );
    if (shared == true) {
      setState(() {
        _session = _session.copyWith(locationShared: true);
        _messages.add(
          ChatMessage(
            id: 'location-${DateTime.now().microsecondsSinceEpoch}',
            role: ChatRole.system,
            text: 'Location shared for weather and local alerts.',
            time: DateTime.now(),
          ),
        );
      });
      _scrollToBottom();
    }
  }

  Future<void> _openFarmMap() async {
    final selected = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => const FarmMapScreen()),
    );
    if (selected == true) {
      setState(() {
        _session = _session.copyWith(farmSelected: true);
        _messages.add(
          ChatMessage(
            id: 'farm-${DateTime.now().microsecondsSinceEpoch}',
            role: ChatRole.system,
            text: 'Farm selected for satellite and crop-stage advice.',
            time: DateTime.now(),
          ),
        );
      });
      _scrollToBottom();
    }
  }

  Future<void> _showMediaPicker() async {
    final media = await showModalBottomSheet<MediaIntent>(
      context: context,
      isScrollControlled: true,
      builder: (_) => const MediaPickerSheet(),
    );
    if (media == null) return;

    final label = switch (media) {
      MediaIntent.camera => 'Camera photo',
      MediaIntent.gallery => 'Gallery image',
      MediaIntent.soilCard => 'Soil card',
      MediaIntent.voiceNote => 'Voice note',
    };
    setState(() {
      _messages.add(
        ChatMessage(
          id: 'media-${DateTime.now().microsecondsSinceEpoch}',
          role: ChatRole.farmer,
          text: label,
          time: DateTime.now(),
          mediaLabel: label,
        ),
      );
      _messages.add(
        ChatMessage(
          id: 'media-reply-${DateTime.now().microsecondsSinceEpoch}',
          role: ChatRole.assistant,
          text: media == MediaIntent.soilCard
              ? 'Soil card received. I will extract pH, EC, OC and NPK in the full version.'
              : 'Media received. I will analyze it with Gemini Vision in the full version.',
          time: DateTime.now(),
        ),
      );
    });
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOut,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 0,
        title: Row(
          children: [
            const CircleAvatar(
              radius: 20,
              backgroundColor: Colors.white,
              child: Icon(Icons.eco_rounded, color: AppTheme.green),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Kisan Alert',
                    style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900),
                  ),
                  Text(
                    '${_session.language.nativeName} • ${_session.phone}',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 12, color: Colors.white70),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'Farm map',
            onPressed: _openFarmMap,
            icon: const Icon(Icons.map_outlined),
          ),
          IconButton(
            tooltip: 'More',
            onPressed: () {},
            icon: const Icon(Icons.more_vert),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.fromLTRB(12, 14, 12, 10),
                itemCount: _messages.length,
                itemBuilder: (context, index) {
                  return ChatBubble(
                    message: _messages[index],
                    onActionTap: (action) {
                      if (action == RequiredAction.location) _askLocation();
                      if (action == RequiredAction.farmSelection) _openFarmMap();
                    },
                  );
                },
              ),
            ),
            ChatComposer(
              onSend: _sendText,
              onMedia: _showMediaPicker,
              onVoice: () => _showMediaPicker(),
            ),
          ],
        ),
      ),
    );
  }
}

