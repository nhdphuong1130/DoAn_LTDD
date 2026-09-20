import 'package:english7_mobile/app/english7_app.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support/fakes.dart';

Future<void> login(WidgetTester tester, FakeStudentApi api) async {
  await tester.pumpWidget(
    English7App(api: api, imageSelector: FakeImageSelector()),
  );
  await tester.pumpAndSettle();
  await tester.enterText(
    find.byKey(const Key('email-field')),
    'student@example.com',
  );
  await tester.enterText(find.byKey(const Key('password-field')), 'password');
  await tester.tap(find.text('Đăng nhập'));
  await tester.pumpAndSettle();
  await tester.tap(find.byIcon(Icons.chat_bubble_outline));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('switches language, selects image and shows grounded citation', (
    tester,
  ) async {
    final api = FakeStudentApi();
    await login(tester, api);

    await tester.tap(find.text('Tiếng Anh'));
    await tester.tap(find.byKey(const Key('select-image')));
    await tester.pumpAndSettle();
    expect(find.text('textbook-page.jpg'), findsOneWidget);

    await tester.enterText(
      find.byKey(const Key('tutor-question')),
      'How can I stay healthy?',
    );
    await tester.tap(find.text('Hỏi AI'));
    await tester.pumpAndSettle();

    expect(find.text('Exercise every day.'), findsOneWidget);
    expect(find.text('SGK trang 20 (PDF 22)'), findsOneWidget);
    expect(api.tutorQueries.single.image?.name, 'textbook-page.jpg');
  });

  testWidgets('shows stable refusal when no verified evidence exists', (
    tester,
  ) async {
    final api = FakeStudentApi()..refuseTutor = true;
    await login(tester, api);

    await tester.enterText(
      find.byKey(const Key('tutor-question')),
      'Tell me about algebra',
    );
    await tester.tap(find.text('Hỏi AI'));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('tutor-refusal')), findsOneWidget);
    expect(find.textContaining('không có trong phạm vi SGK'), findsOneWidget);
  });
}
