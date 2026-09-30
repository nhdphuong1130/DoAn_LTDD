import 'package:english7_mobile/api/api_error.dart';
import 'package:english7_mobile/features/auth/forgot_password_screen.dart';
import 'package:english7_mobile/features/auth/login_screen.dart';
import 'package:english7_mobile/features/auth/register_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../support/fakes.dart';

void main() {
  group('RegisterScreen', () {
    testWidgets('sends OTP with register purpose and registers successfully', (tester) async {
      final api = FakeStudentApi();
      var authenticated = false;

      await tester.pumpWidget(
        MaterialApp(
          home: RegisterScreen(
            api: api,
            onAuthenticated: () => authenticated = true,
          ),
        ),
      );

      // Enter phone
      await tester.enterText(find.byKey(const Key('register-phone-input')), '0374423251');
      await tester.pump();

      // Tap Send OTP
      await tester.tap(find.byKey(const Key('register-send-otp-btn')));
      await tester.pumpAndSettle();

      expect(api.sentOtpPhones, ['+84374423251']);
      expect(api.sentOtpPurposes, ['register']);
      expect(find.byKey(const Key('register-otp-input')), findsOneWidget);

      // Enter OTP and Passwords
      await tester.enterText(find.byKey(const Key('register-otp-input')), '123456');
      await tester.enterText(find.byKey(const Key('register-password-input')), 'NewSecurePass123!');
      await tester.enterText(find.byKey(const Key('register-confirm-password-input')), 'NewSecurePass123!');
      await tester.pump();

      final submitBtn = find.byKey(const Key('submit-register-btn'));
      await tester.ensureVisible(submitBtn);
      await tester.tap(submitBtn);
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      expect(api.lastRegisteredPhone, '+84374423251');
      expect(api.lastRegisteredPassword, 'NewSecurePass123!');
      expect(authenticated, isTrue);
    });

    testWidgets('shows conflict error and links when phone already exists', (tester) async {
      final api = FakeStudentApi()
        ..nextOtpError = const ApiException(
          code: 'phone_already_registered',
          message: 'Số điện thoại này đã được đăng ký tài khoản. Vui lòng đăng nhập lại hoặc sử dụng "Quên mật khẩu".',
          statusCode: 409,
        );

      await tester.pumpWidget(
        MaterialApp(
          home: RegisterScreen(
            api: api,
            onAuthenticated: () {},
          ),
        ),
      );

      final phoneField = find.byKey(const Key('register-phone-input'));
      await tester.ensureVisible(phoneField);
      await tester.enterText(phoneField, '0374423251');
      await tester.pump();

      final sendBtn = find.byKey(const Key('register-send-otp-btn'));
      await tester.ensureVisible(sendBtn);
      await tester.tap(sendBtn);
      await tester.pumpAndSettle();

      expect(find.textContaining('Số điện thoại này đã được đăng ký tài khoản'), findsOneWidget);
      expect(find.text('Đăng nhập lại'), findsOneWidget);
      expect(find.text('Quên mật khẩu?'), findsOneWidget);
    });
  });

  group('ForgotPasswordScreen', () {
    testWidgets('sends OTP and resets password successfully', (tester) async {
      final api = FakeStudentApi();

      await tester.pumpWidget(
        MaterialApp(
          home: ForgotPasswordScreen(api: api),
        ),
      );

      // Enter phone
      final phoneField = find.byKey(const Key('forgot-phone-input'));
      await tester.ensureVisible(phoneField);
      await tester.enterText(phoneField, '0374423251');
      await tester.pump();

      // Tap Send OTP
      final sendBtn = find.byKey(const Key('forgot-send-otp-btn'));
      await tester.ensureVisible(sendBtn);
      await tester.tap(sendBtn);
      await tester.pumpAndSettle();

      expect(api.sentOtpPhones, ['+84374423251']);
      expect(api.sentOtpPurposes, ['reset_password']);
      expect(find.byKey(const Key('reset-otp-input')), findsOneWidget);

      // Enter OTP and Passwords
      await tester.enterText(find.byKey(const Key('reset-otp-input')), '654321');
      await tester.enterText(find.byKey(const Key('reset-new-password-input')), 'ResetPass123!');
      await tester.enterText(find.byKey(const Key('reset-confirm-password-input')), 'ResetPass123!');
      await tester.pump();

      final submitBtn = find.byKey(const Key('submit-reset-password-btn'));
      await tester.ensureVisible(submitBtn);
      await tester.tap(submitBtn);
      await tester.pumpAndSettle();

      expect(api.lastResetPhone, '+84374423251');
      expect(api.lastResetNewPassword, 'ResetPass123!');
    });

    testWidgets('shows error when phone is not registered', (tester) async {
      final api = FakeStudentApi()
        ..nextOtpError = const ApiException(
          code: 'phone_not_found',
          message: 'Số điện thoại này chưa được đăng ký trong hệ thống.',
          statusCode: 404,
        );

      await tester.pumpWidget(
        MaterialApp(
          home: ForgotPasswordScreen(api: api),
        ),
      );

      await tester.enterText(find.byKey(const Key('forgot-phone-input')), '0999999999');
      await tester.pump();
      await tester.tap(find.byKey(const Key('forgot-send-otp-btn')));
      await tester.pumpAndSettle();

      expect(find.textContaining('Số điện thoại này chưa được đăng ký trong hệ thống'), findsOneWidget);
    });
  });

  group('LoginScreen navigation', () {
    testWidgets('links to RegisterScreen and ForgotPasswordScreen', (tester) async {
      final api = FakeStudentApi();

      await tester.pumpWidget(
        MaterialApp(
          home: LoginScreen(
            api: api,
            onAuthenticated: () {},
          ),
        ),
      );

      expect(find.byKey(const Key('forgot-password-btn')), findsOneWidget);
      expect(find.byKey(const Key('open-register-btn')), findsOneWidget);

      // Tap forgot password
      await tester.tap(find.byKey(const Key('forgot-password-btn')));
      await tester.pumpAndSettle();
      expect(find.byType(ForgotPasswordScreen), findsOneWidget);

      // Go back
      await tester.pageBack();
      await tester.pumpAndSettle();

      // Tap register
      await tester.tap(find.byKey(const Key('open-register-btn')));
      await tester.pumpAndSettle();
      expect(find.byType(RegisterScreen), findsOneWidget);
    });
  });
}
