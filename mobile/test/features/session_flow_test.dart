import 'package:english7_mobile/app/english7_app.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support/fakes.dart';

void main() {
  testWidgets('valid stored session opens student shell without login', (
    tester,
  ) async {
    final api = FakeStudentApi()
      ..restoredProfile = FakeStudentApi.defaultProfile;

    await tester.pumpWidget(
      English7App(api: api, imageSelector: FakeImageSelector()),
    );
    await tester.pumpAndSettle();

    expect(find.byType(StudentShell), findsOneWidget);
    expect(find.text('Đăng nhập'), findsNothing);
  });

  testWidgets('missing session opens login', (tester) async {
    final api = FakeStudentApi()..restoredProfile = null;

    await tester.pumpWidget(
      English7App(api: api, imageSelector: FakeImageSelector()),
    );
    await tester.pumpAndSettle();

    expect(find.text('Đăng nhập'), findsOneWidget);
  });

  testWidgets('restore network error shows retry without clearing session', (
    tester,
  ) async {
    final api = FakeStudentApi()..restoreError = Exception('offline');

    await tester.pumpWidget(
      English7App(api: api, imageSelector: FakeImageSelector()),
    );
    await tester.pumpAndSettle();

    expect(find.text('Không thể kiểm tra phiên đăng nhập'), findsOneWidget);
    expect(find.text('Thử lại'), findsOneWidget);
    expect(api.logoutCalled, isFalse);
  });

  testWidgets('retry checks the stored session again', (tester) async {
    final api = FakeStudentApi()..restoreError = Exception('offline');
    await tester.pumpWidget(
      English7App(api: api, imageSelector: FakeImageSelector()),
    );
    await tester.pumpAndSettle();

    api
      ..restoreError = null
      ..restoredProfile = FakeStudentApi.defaultProfile;
    await tester.tap(find.text('Thử lại'));
    await tester.pumpAndSettle();

    expect(api.restoreCalls, 2);
    expect(find.byType(StudentShell), findsOneWidget);
  });

  testWidgets('session error allows logging out to login screen', (
    tester,
  ) async {
    final api = FakeStudentApi()..restoreError = Exception('offline');
    await tester.pumpWidget(
      English7App(api: api, imageSelector: FakeImageSelector()),
    );
    await tester.pumpAndSettle();

    expect(find.text('Đăng nhập tài khoản khác'), findsOneWidget);
    await tester.tap(find.text('Đăng nhập tài khoản khác'));
    await tester.pumpAndSettle();

    expect(api.logoutCalled, isTrue);
    expect(find.text('Đăng nhập'), findsOneWidget);
  });

  testWidgets(
    'registering new account from login screen navigates to student shell',
    (tester) async {
      final api = FakeStudentApi()..restoredProfile = null;
      await tester.pumpWidget(
        English7App(api: api, imageSelector: FakeImageSelector()),
      );
      await tester.pumpAndSettle();

      expect(find.text('Đăng nhập'), findsOneWidget);
      await tester.tap(find.byKey(const Key('open-register-btn')));
      await tester.pumpAndSettle();

      expect(find.text('Tạo tài khoản học sinh'), findsOneWidget);

      // Enter phone and send OTP
      await tester.enterText(
        find.byKey(const Key('register-phone-input')),
        '0374423251',
      );
      await tester.tap(find.byKey(const Key('register-send-otp-btn')));
      await tester.pumpAndSettle();

      // Enter OTP and validate
      await tester.enterText(
        find.byKey(const Key('register-otp-input')),
        '123456',
      );
      await tester.tap(find.byKey(const Key('verify-otp-btn')));
      await tester.pumpAndSettle();

      // Enter Passwords
      await tester.enterText(
        find.byKey(const Key('register-password-input')),
        'NewSecurePass123!',
      );
      await tester.enterText(
        find.byKey(const Key('register-confirm-password-input')),
        'NewSecurePass123!',
      );
      await tester.pump();

      // Submit register
      final submitBtn = find.byKey(const Key('submit-register-btn'));
      await tester.ensureVisible(submitBtn);
      await tester.tap(submitBtn);
      await tester.pumpAndSettle();

      expect(find.text('Tạo tài khoản học sinh'), findsNothing);
      expect(find.text('Thiết lập mật khẩu'), findsNothing);
      expect(find.byType(StudentShell), findsOneWidget);
    },
  );
}

