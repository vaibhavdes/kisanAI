import 'package:flutter/material.dart';

import '../models/app_models.dart';
import '../theme/app_theme.dart';

class ChatBubble extends StatelessWidget {
  const ChatBubble({
    super.key,
    required this.message,
    required this.onActionTap,
  });

  final ChatMessage message;
  final ValueChanged<RequiredAction> onActionTap;

  @override
  Widget build(BuildContext context) {
    if (message.role == ChatRole.system) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Center(
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
            decoration: BoxDecoration(
              color: Colors.black.withOpacity(0.08),
              borderRadius: BorderRadius.circular(999),
            ),
            child: Text(
              message.text,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 12, color: Colors.black54, fontWeight: FontWeight.w700),
            ),
          ),
        ),
      );
    }

    final alignment = message.isFarmer ? Alignment.centerRight : Alignment.centerLeft;
    final bubbleColor = message.isFarmer ? AppTheme.lightGreen : Colors.white;
    final radius = BorderRadius.only(
      topLeft: const Radius.circular(18),
      topRight: const Radius.circular(18),
      bottomLeft: Radius.circular(message.isFarmer ? 18 : 4),
      bottomRight: Radius.circular(message.isFarmer ? 4 : 18),
    );

    return Align(
      alignment: alignment,
      child: ConstrainedBox(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.78,
        ),
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 4),
          padding: const EdgeInsets.fromLTRB(12, 9, 10, 7),
          decoration: BoxDecoration(
            color: bubbleColor,
            borderRadius: radius,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 5,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (message.mediaLabel != null) _MediaPreview(label: message.mediaLabel!),
              Text(
                message.text,
                style: const TextStyle(fontSize: 15.5, height: 1.32, color: AppTheme.textDark),
              ),
              if (message.action != RequiredAction.none) ...[
                const SizedBox(height: 10),
                _ActionButton(action: message.action, onTap: () => onActionTap(message.action)),
              ],
              const SizedBox(height: 3),
              Align(
                alignment: Alignment.centerRight,
                child: Text(
                  _formatTime(message.time),
                  style: TextStyle(fontSize: 10.5, color: Colors.black.withOpacity(0.45)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatTime(DateTime time) {
    final hour = time.hour.toString().padLeft(2, '0');
    final minute = time.minute.toString().padLeft(2, '0');
    return '$hour:$minute';
  }
}

class _ActionButton extends StatelessWidget {
  const _ActionButton({required this.action, required this.onTap});

  final RequiredAction action;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final isLocation = action == RequiredAction.location;
    return OutlinedButton.icon(
      onPressed: onTap,
      style: OutlinedButton.styleFrom(
        foregroundColor: AppTheme.green,
        side: const BorderSide(color: AppTheme.accentGreen),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      ),
      icon: Icon(isLocation ? Icons.my_location : Icons.map_outlined, size: 18),
      label: Text(isLocation ? 'Share location' : 'Select farm'),
    );
  }
}

class _MediaPreview extends StatelessWidget {
  const _MediaPreview({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 210,
      height: 124,
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: AppTheme.green.withOpacity(0.08),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.green.withOpacity(0.12)),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            label.toLowerCase().contains('voice') ? Icons.mic : Icons.image_outlined,
            color: AppTheme.green,
            size: 34,
          ),
          const SizedBox(height: 8),
          Text(label, style: const TextStyle(fontWeight: FontWeight.w800)),
        ],
      ),
    );
  }
}

