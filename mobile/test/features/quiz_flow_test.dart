import 'package:english7_mobile/app/english7_app.dart';
import 'package:english7_mobile/widgets/audio_player.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support/fakes.dart';

void setPhoneViewport(WidgetTester tester) {
  tester.view.physicalSize = const Size(1080, 2400);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('vn.english7/audio_player');
  final audioMethodCalls = <MethodCall>[];

  setUp(() {
    audioMethodCalls.clear();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (MethodCall methodCall) async {
      audioMethodCalls.add(methodCall);
      if (methodCall.method == 'play') {
        return {'status': 'playing', 'duration': 60000};
      }
      return true;
    });
  });

  testWidgets(
    'configures timed quiz, enforces play indicator and submits result',
    (tester) async {
      setPhoneViewport(tester);
      await tester.pumpWidget(
        English7App(api: FakeStudentApi(), imageSelector: FakeImageSelector()),
      );
      await tester.pumpAndSettle();
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

      expect(find.text('True'), findsOneWidget);
      expect(find.text('False'), findsOneWidget);
      expect(find.text('Not given'), findsOneWidget);

      await tester.tap(find.text('True'));
      await tester.pumpAndSettle();

      await tester.tap(find.text('Nộp bài'));
      await tester.pumpAndSettle();
      expect(find.text('Kết quả: 8/10'), findsOneWidget);
    },
  );

  testWidgets(
    'submitting quiz without answers yields zero score',
    (tester) async {
      setPhoneViewport(tester);
      await tester.pumpWidget(
        English7App(api: FakeStudentApi(), imageSelector: FakeImageSelector()),
      );
      await tester.pumpAndSettle();
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

      await tester.tap(find.text('Nộp bài'));
      await tester.pumpAndSettle();
      expect(find.text('Kết quả: 0/10'), findsOneWidget);
    },
  );

  testWidgets('allows selecting quiz mode and sends mode in quiz setup', (
    tester,
  ) async {
    setPhoneViewport(tester);
    final api = FakeStudentApi();
    await tester.pumpWidget(
      English7App(api: api, imageSelector: FakeImageSelector()),
    );
    await tester.pumpAndSettle();
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

    expect(find.text('Đề thi Tổng hợp'), findsOneWidget);
    expect(find.text('Kỹ năng Nghe'), findsOneWidget);
    expect(find.text('Đọc hiểu & Ngôn ngữ'), findsOneWidget);

    await tester.tap(find.text('Kỹ năng Nghe'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Bắt đầu'));
    await tester.pumpAndSettle();

    expect(api.lastSetup?.mode, 'listening');
  });

  testWidgets('hides audio player when quiz has no audio in reading mode', (
    tester,
  ) async {
    setPhoneViewport(tester);
    final api = FakeStudentApi();
    await tester.pumpWidget(
      English7App(api: api, imageSelector: FakeImageSelector()),
    );
    await tester.pumpAndSettle();
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

    await tester.tap(find.text('Đọc hiểu & Ngôn ngữ'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Bắt đầu'));
    await tester.pumpAndSettle();

    expect(api.lastSetup?.mode, 'reading');
    expect(find.byType(LimitedAudioPlayer), findsNothing);
    expect(find.textContaining('Lượt nghe còn lại'), findsNothing);
  });

  testWidgets('plays authentic audio track via native player on play tap', (
    tester,
  ) async {
    setPhoneViewport(tester);
    const channel = MethodChannel('vn.english7/audio_player');
    final log = <MethodCall>[];
    tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(
      channel,
      (MethodCall methodCall) async {
        log.add(methodCall);
        if (methodCall.method == 'play') {
          return {'status': 'playing', 'duration': 60000};
        }
        return true;
      },
    );

    final api = FakeStudentApi();
    api.fakeAudioUrl = '/api/v1/media/audio/18';
    api.fakeAudioTitle = 'Track 18 - Skills 2 Listening';

    await tester.pumpWidget(
      English7App(api: api, imageSelector: FakeImageSelector()),
    );
    await tester.pumpAndSettle();
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

    await tester.tap(find.text('Bắt đầu'));
    await tester.pumpAndSettle();

    expect(find.text('Track 18 - Skills 2 Listening'), findsOneWidget);
    expect(find.text('Lượt nghe còn lại: 2'), findsOneWidget);

    await tester.tap(find.byKey(const Key('play-audio')));
    await tester.pump();

    expect(find.text('Lượt nghe còn lại: 1'), findsOneWidget);
    expect(
      log.any(
        (call) =>
            call.method == 'play' &&
            (call.arguments as Map)['url'].toString().contains('/api/v1/media/audio/18'),
      ),
      isTrue,
    );
  });
}
