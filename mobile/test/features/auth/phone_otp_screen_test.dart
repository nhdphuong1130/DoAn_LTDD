import 'package:english7_mobile/features/auth/phone_otp_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../support/fakes.dart';

void main() {
  testWidgets('sends OTP via SMS and verifies successfully', (tester) async {
    final api = FakeStudentApi();
    var authenticated = false;

    await tester.pumpWidget(
      MaterialApp(
        home: PhoneOtpScreen(
          api: api,
          onAuthenticated: () => authenticated = true,
        ),
      ),
    );

    // Enter phone number
    await tester.enterText(find.byKey(const Key('phone-input-field')), '0912345678');
    await tester.pump();

    // Tap SMS send button
    await tester.tap(find.byKey(const Key('send-otp-btn')));
    await tester.pumpAndSettle();

    expect(api.sentOtpPhones, ['+84912345678']);
    expect(api.sentOtpChannels, ['sms']);
    expect(find.byKey(const Key('otp-input-field')), findsOneWidget);
    expect(find.textContaining('Mã xác nhận 6 số đã được gửi'), findsOneWidget);

    // Enter OTP code
    await tester.enterText(find.byKey(const Key('otp-input-field')), '123456');
    await tester.pumpAndSettle();

    expect(authenticated, isTrue);
  });

  testWidgets('sends OTP via Voice call and displays voice call message', (tester) async {
    final api = FakeStudentApi();

    await tester.pumpWidget(
      MaterialApp(
        home: PhoneOtpScreen(
          api: api,
          onAuthenticated: () {},
        ),
      ),
    );

    // Enter phone number
    await tester.enterText(find.byKey(const Key('phone-input-field')), '0987654321');
    await tester.pump();

    // Tap Voice send button
    await tester.tap(find.byKey(const Key('send-otp-voice-btn')));
    await tester.pumpAndSettle();

    expect(api.sentOtpPhones, ['+84987654321']);
    expect(api.sentOtpChannels, ['voice']);
    expect(find.byKey(const Key('otp-input-field')), findsOneWidget);
    expect(find.textContaining('Hệ thống đang gọi điện'), findsOneWidget);
  });

  testWidgets('resend OTP buttons appear after countdown', (tester) async {
    final api = FakeStudentApi();

    await tester.pumpWidget(
      MaterialApp(
        home: PhoneOtpScreen(
          api: api,
          onAuthenticated: () {},
        ),
      ),
    );

    await tester.enterText(find.byKey(const Key('phone-input-field')), '0912345678');
    await tester.tap(find.byKey(const Key('send-otp-btn')));
    await tester.pumpAndSettle();

    expect(find.textContaining('Gửi lại mã sau'), findsOneWidget);

    // Fast-forward 61 seconds
    await tester.pump(const Duration(seconds: 61));

    expect(find.byKey(const Key('resend-sms-btn')), findsOneWidget);
    expect(find.byKey(const Key('resend-voice-btn')), findsOneWidget);

    // Resend via voice call
    await tester.tap(find.byKey(const Key('resend-voice-btn')));
    await tester.pumpAndSettle();

    expect(api.sentOtpChannels, ['sms', 'voice']);
  });
}
