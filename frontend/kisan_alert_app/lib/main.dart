import 'package:flutter/material.dart';

import 'screens/login_screen.dart';
import 'theme/app_theme.dart';

void main() {
  runApp(const KisanAlertApp());
}

class KisanAlertApp extends StatelessWidget {
  const KisanAlertApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Kisan Alert',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      home: const LoginScreen(),
    );
  }
}

