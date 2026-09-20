import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:english7_mobile/app/student_api.dart';
import 'package:english7_mobile/features/lessons/lesson_screen.dart';

import 'support/fakes.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('renders audio player for activities with listening tracks', (tester) async {
    tester.view.physicalSize = const Size(1080, 2400);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    const channel = MethodChannel('vn.english7/audio_player');
    final log = <MethodCall>[];
    tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(
      channel,
      (MethodCall methodCall) async {
        log.add(methodCall);
        if (methodCall.method == 'play') {
          return {'status': 'playing', 'duration': 60000};
        }
        if (methodCall.method == 'getStatus') {
          return {'isPlaying': true, 'position': 1000, 'duration': 60000};
        }
        return true;
      },
    );

    final detail = LessonDetail(
      id: 'unit-1',
      unitNumber: 1,
      title: 'Hobbies',
      sections: [
        LessonSection(
          id: 'sec-1',
          title: 'GETTING STARTED - My favourite hobby',
          sectionType: 'lesson',
          position: 1,
          activities: [
            const LessonActivity(
              id: 'act-1',
              number: '1',
              activityType: 'reading_dialogue',
              instruction: 'Listen and read the conversation between Ann and Trang. (Track 2)',
              audioTracks: [
                LessonAudioTrack(
                  id: 'track-2-id',
                  trackNumber: 2,
                  audioUrl: '/api/v1/media/audio/2',
                ),
              ],
              fragments: [
                LessonFragment(
                  id: 'frag-1',
                  pdfPage: 8,
                  printedPage: 8,
                  text: 'Ann: Your house is very nice, Trang.\nTrang: Thanks! Let\'s go upstairs.',
                ),
              ],
            ),
            const LessonActivity(
              id: 'act-3',
              number: '3',
              activityType: 'vocabulary',
              instruction: 'Write the words and phrases from the box under the correct pictures. Then listen, check, and repeat. (Track 3)',
              audioTracks: [
                LessonAudioTrack(
                  id: 'track-3-id',
                  trackNumber: 3,
                  audioUrl: '/api/v1/media/audio/3',
                ),
              ],
              fragments: [
                LessonFragment(
                  id: 'frag-3',
                  pdfPage: 9,
                  printedPage: 9,
                  text: '1. making models\n2. riding a horse',
                ),
              ],
            ),
          ],
        ),
      ],
    );

    final api = FakeStudentApi();
    api.customDetail = detail;

    await tester.pumpWidget(
      MaterialApp(
        home: LessonDetailScreen(
          lesson: const LessonSummary(
            1,
            'Hobbies',
            'GETTING STARTED',
            id: 'unit-1',
          ),
          api: api,
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Verify both Track 2 and Track 3 audio players are rendered
    expect(find.byKey(const Key('audio-track-2')), findsOneWidget);
    expect(find.byKey(const Key('audio-track-3')), findsOneWidget);
    expect(find.text('Track 2'), findsOneWidget);
    expect(find.text('Track 3'), findsOneWidget);

    // Tap play on Track 2
    final playButtons = find.byKey(const Key('lesson-audio-play-button'));
    expect(playButtons, findsNWidgets(2));

    await tester.tap(playButtons.first);
    await tester.pumpAndSettle();

    expect(log.any((call) => call.method == 'play'), isTrue);
  });
}
