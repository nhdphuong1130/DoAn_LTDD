import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:english7_mobile/app/student_api.dart';
import 'package:english7_mobile/app/learning_api.dart';
import 'package:english7_mobile/app/english7_app.dart';
import 'package:english7_mobile/features/progress/progress_screen.dart';

import 'support/fakes.dart';

class ProgressApi extends FakeStudentApi {
  bool learningOffline = false;
  @override
  Future<LearningProgress> loadLearningProgress() async {
    if (learningOffline) throw Exception('offline');
    return const LearningProgress(
      reviewedCards: 3,
      dueCards: 2,
      difficultCards: 1,
      speakingCount: 4,
      recentSpeaking: [],
    );
  }

  int calls = 0;
  bool offline = false;
  bool failSubmit = false;
  StudentProgress progress = const StudentProgress(0, 0, 0, []);
  @override
  Future<StudentProgress> loadProgress() async {
    calls++;
    if (offline) throw Exception('offline');
    return progress;
  }

  @override
  Future<QuizResult> submitQuiz(
    String quizId, [
    Map<String, String>? answers,
  ]) async {
    if (failSubmit) throw Exception('offline');
    progress = StudentProgress(1, 0, 2, [
      QuizHistoryItem(quizId, DateTime.utc(2026, 9, 25), 0, 2),
    ]);
    return const QuizResult(0, 2);
  }
}

void main() {
  testWidgets('learning tab is reachable from the student shell', (
    tester,
  ) async {
    final api = ProgressApi()..restoredProfile = FakeStudentApi.defaultProfile;
    await tester.pumpWidget(
      English7App(api: api, imageSelector: FakeImageSelector()),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Luyện tập'));
    await tester.pumpAndSettle();
    expect(find.text('Học từ & luyện nói'), findsOneWidget);
    expect(find.text('Tạo bộ từ'), findsOneWidget);
  });
  testWidgets('progress includes learning counts without fabricated scores', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: ProgressScreen(api: ProgressApi(), active: true)),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('3 thẻ đã ôn'), findsOneWidget);
    expect(find.text('2 thẻ đến hạn'), findsOneWidget);
    expect(find.text('4 lượt luyện nói'), findsOneWidget);
  });
  testWidgets('learning failure preserves quiz results', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ProgressScreen(
            api: ProgressApi()..learningOffline = true,
            active: true,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Chưa có bài kiểm tra đã nộp'), findsOneWidget);
    expect(
      find.text('Chưa tải được tiến độ từ vựng và luyện nói.'),
      findsOneWidget,
    );
  });
  testWidgets(
    'submit failure can retry and tab refreshes after successful submission',
    (tester) async {
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final api = ProgressApi()
        ..restoredProfile = FakeStudentApi.defaultProfile;
      await tester.pumpWidget(
        English7App(api: api, imageSelector: FakeImageSelector()),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byIcon(Icons.insights_outlined));
      await tester.pumpAndSettle();
      expect(find.text('Chưa có bài kiểm tra đã nộp'), findsOneWidget);
      await tester.tap(find.byIcon(Icons.quiz_outlined));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Bắt đầu'));
      await tester.pumpAndSettle();
      api.failSubmit = true;
      await tester.tap(find.text('Nộp bài'));
      await tester.pumpAndSettle();
      expect(
        find.text('Không thể lưu kết quả. Vui lòng thử nộp lại.'),
        findsOneWidget,
      );
      api.failSubmit = false;
      await tester.tap(find.text('Nộp bài'));
      await tester.pumpAndSettle();
      expect(find.text('Kết quả: 0/2'), findsOneWidget);
      await tester.tap(find.byIcon(Icons.insights_outlined));
      await tester.pumpAndSettle();
      expect(find.text('1 bài kiểm tra đã nộp'), findsOneWidget);
      expect(find.text('0/2 câu đúng'), findsOneWidget);
    },
  );
  testWidgets('empty state and reload on entering tab show persisted history', (
    tester,
  ) async {
    final api = ProgressApi();
    Future<void> show(bool active) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ProgressScreen(api: api, active: active),
          ),
        ),
      );
      await tester.pumpAndSettle();
    }

    await show(false);
    expect(api.calls, 0);
    await show(true);
    expect(find.text('Chưa có bài kiểm tra đã nộp'), findsOneWidget);
    await show(false);
    api.progress = StudentProgress(1, 1, 2, [
      QuizHistoryItem('quiz-1', DateTime.utc(2026, 9, 25), 1, 2),
    ]);
    await show(true);
    expect(api.calls, 2);
    expect(find.text('50%'), findsOneWidget);
    expect(find.text('1/2 câu đúng'), findsOneWidget);
  });

  testWidgets('network failure shows retry and recovers', (tester) async {
    final api = ProgressApi()..offline = true;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: ProgressScreen(api: api, active: true)),
      ),
    );
    await tester.pumpAndSettle();
    expect(
      find.text('Không thể tải tiến độ. Vui lòng thử lại.'),
      findsOneWidget,
    );
    api.offline = false;
    await tester.tap(find.text('Thử lại'));
    await tester.pumpAndSettle();
    expect(find.text('Chưa có bài kiểm tra đã nộp'), findsOneWidget);
  });
}
