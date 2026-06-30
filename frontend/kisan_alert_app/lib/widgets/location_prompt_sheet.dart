import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

class LocationPromptSheet extends StatelessWidget {
  const LocationPromptSheet({super.key});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 10, 20, 22),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 42,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.black26,
                borderRadius: BorderRadius.circular(999),
              ),
            ),
            const SizedBox(height: 24),
            Container(
              width: 68,
              height: 68,
              decoration: BoxDecoration(
                color: AppTheme.green.withOpacity(0.10),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.my_location, color: AppTheme.green, size: 34),
            ),
            const SizedBox(height: 18),
            const Text(
              'Share location once',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900),
            ),
            const SizedBox(height: 8),
            const Text(
              'Location helps provide district weather, dry-spell alerts and nearby expert support. In the full app this will request phone permission.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.black54, height: 1.4),
            ),
            const SizedBox(height: 22),
            FilledButton.icon(
              onPressed: () => Navigator.of(context).pop(true),
              style: FilledButton.styleFrom(
                backgroundColor: AppTheme.green,
                minimumSize: const Size.fromHeight(52),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              ),
              icon: const Icon(Icons.location_on_outlined),
              label: const Text('Share location'),
            ),
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('Not now'),
            ),
          ],
        ),
      ),
    );
  }
}

