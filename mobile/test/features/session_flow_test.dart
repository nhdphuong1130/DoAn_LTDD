import 'package:english7_mobile/app/english7_app.dart';
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
}
