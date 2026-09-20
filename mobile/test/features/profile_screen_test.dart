import 'package:english7_mobile/app/english7_app.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support/fakes.dart';

void main() {
  testWidgets('profile tab displays and updates student information', (
    tester,
  ) async {
    final api = FakeStudentApi()
      ..restoredProfile = FakeStudentApi.defaultProfile;

    await tester.pumpWidget(
      English7App(api: api, imageSelector: FakeImageSelector()),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Cá nhân'));
    await tester.pumpAndSettle();

    expect(find.text('student@example.com'), findsOneWidget);
    await tester.tap(find.text('Chỉnh sửa hồ sơ'));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('profile-full-name')),
      'Nguyễn An',
    );
    await tester.enterText(find.byKey(const Key('profile-class-name')), '7A1');
    await tester.ensureVisible(find.text('Lưu thay đổi'));
    await tester.tap(find.text('Lưu thay đổi'));
    await tester.pumpAndSettle();

    expect(api.profile.fullName, 'Nguyễn An');
    expect(api.profile.className, '7A1');
  });

  testWidgets('password mismatch is caught before calling API', (tester) async {
    final api = FakeStudentApi()
      ..restoredProfile = FakeStudentApi.defaultProfile;

    await tester.pumpWidget(
      English7App(api: api, imageSelector: FakeImageSelector()),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Cá nhân'));
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.byKey(const Key('current-password-field')));
    await tester.enterText(
      find.byKey(const Key('current-password-field')),
      'old-pass',
    );
    await tester.enterText(
      find.byKey(const Key('new-password-field')),
      'new-pass-1',
    );
    await tester.enterText(
      find.byKey(const Key('confirm-password-field')),
      'new-pass-2',
    );
    final changePasswordBtn = find.widgetWithText(FilledButton, 'Đổi mật khẩu');
    await tester.ensureVisible(changePasswordBtn);
    await tester.tap(changePasswordBtn);
    await tester.pumpAndSettle();

    expect(find.text('Mật khẩu xác nhận không khớp'), findsOneWidget);
    expect(api.passwordArguments, isNull);
  });

  testWidgets('save failure retains entered form values and shows error', (
    tester,
  ) async {
    final api = FakeStudentApi()
      ..restoredProfile = FakeStudentApi.defaultProfile
      ..profileUpdateError = Exception('Cập nhật thất bại');

    await tester.pumpWidget(
      English7App(api: api, imageSelector: FakeImageSelector()),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Cá nhân'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Chỉnh sửa hồ sơ'));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('profile-full-name')),
      'Trần Bình',
    );
    await tester.ensureVisible(find.text('Lưu thay đổi'));
    await tester.tap(find.text('Lưu thay đổi'));
    await tester.pumpAndSettle();

    expect(find.text('Cập nhật hồ sơ thất bại'), findsOneWidget);
    expect(find.widgetWithText(TextField, 'Trần Bình'), findsOneWidget);
  });

  testWidgets('logout requires confirmation and returns to login', (
    tester,
  ) async {
    final api = FakeStudentApi()
      ..restoredProfile = FakeStudentApi.defaultProfile;

    await tester.pumpWidget(
      English7App(api: api, imageSelector: FakeImageSelector()),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Cá nhân'));
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.text('Đăng xuất'));
    await tester.tap(find.text('Đăng xuất'));
    await tester.pumpAndSettle();

    expect(find.text('Bạn có chắc muốn đăng xuất?'), findsOneWidget);
    await tester.tap(find.widgetWithText(FilledButton, 'Đăng xuất'));
    await tester.pumpAndSettle();

    expect(api.logoutCalled, isTrue);
    expect(find.byKey(const Key('email-field')), findsOneWidget);
  });
}
