import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

class FarmMapScreen extends StatefulWidget {
  const FarmMapScreen({super.key});

  @override
  State<FarmMapScreen> createState() => _FarmMapScreenState();
}

class _FarmMapScreenState extends State<FarmMapScreen> {
  Offset? _selectedPoint;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Select farm on map'),
        actions: [
          TextButton(
            onPressed: _selectedPoint == null ? null : () => Navigator.of(context).pop(true),
            child: Text(
              'Done',
              style: TextStyle(
                color: _selectedPoint == null ? Colors.white54 : Colors.white,
                fontWeight: FontWeight.w900,
              ),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(22),
                  child: GestureDetector(
                    onTapDown: (details) {
                      setState(() => _selectedPoint = details.localPosition);
                    },
                    child: CustomPaint(
                      painter: _FarmMapPainter(selectedPoint: _selectedPoint),
                      child: const SizedBox.expand(),
                    ),
                  ),
                ),
              ),
            ),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.fromLTRB(18, 14, 18, 18),
              decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'Tap your farm location',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'This is a UI placeholder. Later it can use Google Maps, Earth Engine farm boundary, or a simple pin selection.',
                    style: TextStyle(color: Colors.black54, height: 1.35),
                  ),
                  const SizedBox(height: 14),
                  FilledButton.icon(
                    onPressed: _selectedPoint == null ? null : () => Navigator.of(context).pop(true),
                    style: FilledButton.styleFrom(
                      backgroundColor: AppTheme.green,
                      minimumSize: const Size.fromHeight(52),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    ),
                    icon: const Icon(Icons.check_circle_outline),
                    label: const Text('Use selected farm'),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FarmMapPainter extends CustomPainter {
  const _FarmMapPainter({required this.selectedPoint});

  final Offset? selectedPoint;

  @override
  void paint(Canvas canvas, Size size) {
    final background = Paint()..color = const Color(0xFFB7D7A8);
    canvas.drawRect(Offset.zero & size, background);

    final fieldPaint = Paint()..color = const Color(0xFFE8D7A8).withOpacity(0.85);
    final waterPaint = Paint()..color = const Color(0xFF8EC5E8).withOpacity(0.8);
    final roadPaint = Paint()
      ..color = const Color(0xFFEEE8D8)
      ..strokeWidth = 18
      ..strokeCap = StrokeCap.round;

    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(size.width * 0.08, size.height * 0.10, size.width * 0.38, size.height * 0.28),
        const Radius.circular(18),
      ),
      fieldPaint,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(size.width * 0.52, size.height * 0.18, size.width * 0.36, size.height * 0.30),
        const Radius.circular(18),
      ),
      fieldPaint..color = const Color(0xFFD9C17E),
    );
    canvas.drawOval(
      Rect.fromLTWH(size.width * 0.58, size.height * 0.62, size.width * 0.30, size.height * 0.14),
      waterPaint,
    );
    canvas.drawLine(
      Offset(size.width * 0.10, size.height * 0.78),
      Offset(size.width * 0.92, size.height * 0.42),
      roadPaint,
    );

    final gridPaint = Paint()
      ..color = Colors.white.withOpacity(0.16)
      ..strokeWidth = 1;
    for (var x = 0.0; x < size.width; x += 42) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), gridPaint);
    }
    for (var y = 0.0; y < size.height; y += 42) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), gridPaint);
    }

    if (selectedPoint != null) {
      final pinPaint = Paint()..color = AppTheme.green;
      final ringPaint = Paint()
        ..color = AppTheme.green.withOpacity(0.18)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 12;
      canvas.drawCircle(selectedPoint!, 24, ringPaint);
      canvas.drawCircle(selectedPoint!, 9, pinPaint);
    }
  }

  @override
  bool shouldRepaint(covariant _FarmMapPainter oldDelegate) {
    return oldDelegate.selectedPoint != selectedPoint;
  }
}

