import 'package:flutter/material.dart';

import '../models/app_models.dart';
import '../theme/app_theme.dart';

class MediaPickerSheet extends StatelessWidget {
  const MediaPickerSheet({super.key});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(18, 10, 18, 18),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 42,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.black26,
                  borderRadius: BorderRadius.circular(999),
                ),
              ),
            ),
            const SizedBox(height: 18),
            const Text(
              'Send to Kisan Alert',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
            ),
            const SizedBox(height: 14),
            GridView.count(
              shrinkWrap: true,
              crossAxisCount: 2,
              childAspectRatio: 2.6,
              mainAxisSpacing: 10,
              crossAxisSpacing: 10,
              physics: const NeverScrollableScrollPhysics(),
              children: [
                _MediaTile(
                  icon: Icons.photo_camera_outlined,
                  label: 'Camera',
                  color: AppTheme.green,
                  onTap: () => Navigator.of(context).pop(MediaIntent.camera),
                ),
                _MediaTile(
                  icon: Icons.photo_library_outlined,
                  label: 'Gallery',
                  color: Colors.purple,
                  onTap: () => Navigator.of(context).pop(MediaIntent.gallery),
                ),
                _MediaTile(
                  icon: Icons.receipt_long_outlined,
                  label: 'Soil card',
                  color: Colors.orange,
                  onTap: () => Navigator.of(context).pop(MediaIntent.soilCard),
                ),
                _MediaTile(
                  icon: Icons.mic_none_outlined,
                  label: 'Voice note',
                  color: Colors.blue,
                  onTap: () => Navigator.of(context).pop(MediaIntent.voiceNote),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _MediaTile extends StatelessWidget {
  const _MediaTile({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(18),
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12),
        decoration: BoxDecoration(
          color: color.withOpacity(0.08),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: color.withOpacity(0.14)),
        ),
        child: Row(
          children: [
            CircleAvatar(
              radius: 18,
              backgroundColor: color.withOpacity(0.14),
              child: Icon(icon, color: color, size: 20),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontWeight: FontWeight.w900),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

