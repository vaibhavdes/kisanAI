import 'package:flutter/material.dart';

import '../models/app_models.dart';
import '../models/languages.dart';
import '../theme/app_theme.dart';
import 'chat_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _phoneController = TextEditingController();
  LanguageOption _selectedLanguage = supportedLanguages.first;

  @override
  void dispose() {
    _phoneController.dispose();
    super.dispose();
  }

  void _continue() {
    final phone = _phoneController.text.trim();
    if (phone.length < 8) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Enter a valid phone number')),
      );
      return;
    }

    final session = FarmerSession(phone: phone, language: _selectedLanguage);
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => ChatScreen(initialSession: session)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 28),
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: constraints.maxHeight - 48),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const SizedBox(height: 18),
                    const _BrandHeader(),
                    const SizedBox(height: 32),
                    Text(
                      'Start in your language',
                      style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                            fontWeight: FontWeight.w900,
                            color: AppTheme.textDark,
                          ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Kisan Alert will use this phone and language for WhatsApp, SMS, voice call and app chat.',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: Colors.black54,
                            height: 1.35,
                          ),
                    ),
                    const SizedBox(height: 24),
                    TextField(
                      controller: _phoneController,
                      keyboardType: TextInputType.phone,
                      decoration: const InputDecoration(
                        prefixIcon: Icon(Icons.phone_outlined),
                        labelText: 'Phone number',
                        hintText: '+91 98765 43210',
                      ),
                    ),
                    const SizedBox(height: 18),
                    _LanguageGrid(
                      selected: _selectedLanguage,
                      onSelected: (language) => setState(() => _selectedLanguage = language),
                    ),
                    const SizedBox(height: 28),
                    FilledButton(
                      onPressed: _continue,
                      style: FilledButton.styleFrom(
                        backgroundColor: AppTheme.green,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
                      ),
                      child: const Text(
                        'Continue',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}

class _BrandHeader extends StatelessWidget {
  const _BrandHeader();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 58,
          height: 58,
          decoration: BoxDecoration(
            color: AppTheme.green,
            borderRadius: BorderRadius.circular(18),
            boxShadow: [
              BoxShadow(
                color: AppTheme.green.withOpacity(0.25),
                blurRadius: 18,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: const Icon(Icons.eco_rounded, color: Colors.white, size: 32),
        ),
        const SizedBox(width: 14),
        const Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Kisan Alert',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900),
              ),
              SizedBox(height: 3),
              Text(
                'Smart crop, water and advisory chat',
                style: TextStyle(color: Colors.black54, fontWeight: FontWeight.w600),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _LanguageGrid extends StatelessWidget {
  const _LanguageGrid({required this.selected, required this.onSelected});

  final LanguageOption selected;
  final ValueChanged<LanguageOption> onSelected;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Language',
          style: TextStyle(fontWeight: FontWeight.w900, color: AppTheme.textDark),
        ),
        const SizedBox(height: 10),
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: supportedLanguages.length,
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            mainAxisSpacing: 10,
            crossAxisSpacing: 10,
            childAspectRatio: 2.75,
          ),
          itemBuilder: (context, index) {
            final language = supportedLanguages[index];
            final isSelected = selected.code == language.code;
            return InkWell(
              borderRadius: BorderRadius.circular(16),
              onTap: () => onSelected(language),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 180),
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(
                  color: isSelected ? AppTheme.lightGreen : Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: isSelected ? AppTheme.accentGreen : Colors.black.withOpacity(0.08),
                    width: isSelected ? 1.4 : 1,
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      isSelected ? Icons.check_circle : Icons.language,
                      color: isSelected ? AppTheme.green : Colors.black45,
                      size: 19,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        language.nativeName,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontWeight: FontWeight.w800),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        ),
      ],
    );
  }
}
