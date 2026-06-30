import 'package:flutter_test/flutter_test.dart';
import 'package:kisan_alert_app/main.dart';

void main() {
  testWidgets('shows login screen', (tester) async {
    await tester.pumpWidget(const KisanAlertApp());
    expect(find.text('Kisan Alert'), findsOneWidget);
    expect(find.text('Start in your language'), findsOneWidget);
  });
}

