import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

class ChatComposer extends StatefulWidget {
  const ChatComposer({
    super.key,
    required this.onSend,
    required this.onMedia,
    required this.onVoice,
  });

  final ValueChanged<String> onSend;
  final VoidCallback onMedia;
  final VoidCallback onVoice;

  @override
  State<ChatComposer> createState() => _ChatComposerState();
}

class _ChatComposerState extends State<ChatComposer> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _submit() {
    final text = _controller.text;
    if (text.trim().isEmpty) return;
    _controller.clear();
    widget.onSend(text);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(8, 8, 8, 8 + MediaQuery.of(context).padding.bottom),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.92),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.06),
            blurRadius: 12,
            offset: const Offset(0, -4),
          ),
        ],
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Expanded(
            child: Container(
              constraints: const BoxConstraints(minHeight: 48, maxHeight: 112),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: Colors.black.withOpacity(0.08)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  IconButton(
                    tooltip: 'Media',
                    onPressed: widget.onMedia,
                    icon: const Icon(Icons.attach_file, color: Colors.black54),
                  ),
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      minLines: 1,
                      maxLines: 4,
                      textInputAction: TextInputAction.newline,
                      decoration: const InputDecoration(
                        hintText: 'Type your farm question...',
                        border: InputBorder.none,
                        enabledBorder: InputBorder.none,
                        focusedBorder: InputBorder.none,
                        filled: false,
                        contentPadding: EdgeInsets.symmetric(vertical: 13),
                      ),
                    ),
                  ),
                  IconButton(
                    tooltip: 'Camera',
                    onPressed: widget.onMedia,
                    icon: const Icon(Icons.photo_camera_outlined, color: Colors.black54),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(width: 8),
          ValueListenableBuilder<TextEditingValue>(
            valueListenable: _controller,
            builder: (context, value, _) {
              final canSend = value.text.trim().isNotEmpty;
              return FloatingActionButton.small(
                heroTag: 'composer-action',
                elevation: 0,
                backgroundColor: AppTheme.green,
                onPressed: canSend ? _submit : widget.onVoice,
                child: Icon(canSend ? Icons.send : Icons.mic),
              );
            },
          ),
        ],
      ),
    );
  }
}

