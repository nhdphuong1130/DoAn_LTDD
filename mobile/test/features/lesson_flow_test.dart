import 'package:english7_mobile/app/english7_app.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support/fakes.dart';

void main() {
  testWidgets('login opens lesson list and lesson detail', (tester) async {
    await tester.pumpWidget(
      English7App(api: FakeStudentApi(), imageSelector: FakeImageSelector()),
    );
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('email-field')),
      'student@example.com',
    );
    await tester.enterText(find.byKey(const Key('password-field')), 'password');
    await tester.tap(find.text('Đăng nhập'));
    await tester.pumpAndSettle();

    expect(find.text('Unit 1: Hobbies'), findsOneWidget);
    expect(find.text('Unit 2: Healthy Living'), findsOneWidget);

    await tester.tap(find.text('Unit 1: Hobbies'));
    await tester.pumpAndSettle();

    expect(find.text('Getting Started'), findsWidgets);
    expect(find.text('Nguồn: SGK Tiếng Anh 7'), findsOneWidget);
  });
}
