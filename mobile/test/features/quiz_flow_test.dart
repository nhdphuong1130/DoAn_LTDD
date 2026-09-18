import 'package:english7_mobile/app/english7_app.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support/fakes.dart';

void main() {
  testWidgets(
    'configures timed quiz, enforces play indicator and submits result',
    (tester) async {
      await tester.pumpWidget(
        English7App(api: FakeStudentApi(), imageSelector: FakeImageSelector()),
      );
      await tester.enterText(
        find.byKey(const Key('email-field')),
        'student@example.com',
      );
      await tester.enterText(
        find.byKey(const Key('password-field')),
        'password',
      );
      await tester.tap(find.text('Đăng nhập'));
      await tester.pumpAndSettle();
      await tester.tap(find.byIcon(Icons.quiz_outlined));
      await tester.pumpAndSettle();

      await tester.tap(find.text('15 phút'));
      await tester.tap(find.text('Bắt đầu'));
      await tester.pumpAndSettle();

      expect(find.text('15:00'), findsOneWidget);
      expect(find.text('Lượt nghe còn lại: 2'), findsOneWidget);
      await tester.tap(find.byKey(const Key('play-audio')));
      await tester.pump();
      expect(find.text('Lượt nghe còn lại: 1'), findsOneWidget);

      await tester.tap(find.text('Nộp bài'));
      await tester.pumpAndSettle();
      expect(find.text('Kết quả: 8/10'), findsOneWidget);
    },
  );
}
