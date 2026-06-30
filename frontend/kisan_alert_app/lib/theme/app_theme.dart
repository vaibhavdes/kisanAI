import 'package:flutter/material.dart';

class AppTheme {
  static const green = Color(0xFF075E54);
  static const lightGreen = Color(0xFFDCF8C6);
  static const accentGreen = Color(0xFF128C7E);
  static const background = Color(0xFFECE5DD);
  static const textDark = Color(0xFF17212B);

  static ThemeData get light {
    return ThemeData(
      colorScheme: ColorScheme.fromSeed(
        seedColor: green,
        primary: green,
        secondary: accentGreen,
        surface: Colors.white,
      ),
      scaffoldBackgroundColor: background,
      useMaterial3: true,
      appBarTheme: const AppBarTheme(
        backgroundColor: green,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: false,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: accentGreen, width: 1.4),
        ),
      ),
    );
  }
}

