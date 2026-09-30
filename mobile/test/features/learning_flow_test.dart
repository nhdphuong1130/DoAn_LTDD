import 'dart:async';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:english7_mobile/app/learning_api.dart';
import 'package:english7_mobile/api/api_error.dart';
import 'package:english7_mobile/features/flashcards/learning_screen.dart';
import 'package:english7_mobile/features/flashcards/review_screen.dart';
import 'package:english7_mobile/features/speaking/sentence_practice_screen.dart';
import 'package:english7_mobile/features/speaking/speaking_screen.dart';
import 'package:english7_mobile/services/speech_recorder.dart';
import 'package:english7_mobile/services/tts_service.dart';

class FakeLearningApi implements LearningApi {
  Object? submitError;
  Object? cardAudioError;
  bool voicesAvailable = true;
  bool failFirstSpeakingRequest = true;
  double mockMatchPercent = 100;
  Completer<Uint8List>? preview;
  Completer<Uint8List>? cardAudioCompleter;
  int cardAudioCalls = 0;
  @override
  Future<Uint8List> loadCardAudio(String cardId) async {
    cardAudioCalls++;
    if (cardAudioError != null) throw cardAudioError!;
    if (cardAudioCompleter != null) return cardAudioCompleter!.future;
    return Uint8List.fromList([82, 73, 70, 70]);
  }
  @override
  Future<Uint8List> previewVoice(String id) => preview!.future;
  final requests = <String>[];
  final reviews = <({String requestId, String answer, String rating})>[];
  static const card = Flashcard(
    id: 'card',
    deckId: 'deck',
    word: 'hobby',
    meaning: 'sở thích',
  );
  @override
  Future<List<Flashcard>> loadCards(String deckId) async => [card];
  @override
  Future<List<Flashcard>> loadReviewCards(String deckId) async => [card];
  @override
  Future<FlashcardReviewResult> reviewCard(
    String id, {
    required String requestId,
    required String answer,
    required String rating,
  }) async {
    reviews.add((requestId: requestId, answer: answer, rating: rating));
    if (reviews.length == 1) throw Exception('Mất kết nối');
    return FlashcardReviewResult(
      correct: false,
      meaning: 'sở thích',
      dueAt: DateTime.utc(2026, 9, 26),
    );
  }

  @override
  Future<List<FlashcardDeck>> loadDecks() async => [
    const FlashcardDeck(
      id: 'deck',
      name: 'Unit 1',
      kind: 'textbook',
      cardCount: 1,
    ),
  ];
  @override
  Future<SpeakingVoices> loadVoices() async => SpeakingVoices(
    items: const [SpeakingVoice(id: 'voice', name: 'Giọng mẫu')],
    selectedVoice: 'voice',
    available: voicesAvailable,
  );
  @override
  Future<SpeakingResult> submitSpeaking({
    required String requestId,
    required String cardId,
    required String voiceId,
    required Uint8List audio,
    String? prompt,
  }) async {
    requests.add(requestId);
    if (submitError != null) throw submitError!;
    if (failFirstSpeakingRequest && requests.length == 1) throw Exception('Mất kết nối');
    return SpeakingResult.fromJson({
      'id': 'attempt',
      'card_id': cardId,
      'prompt': prompt ?? 'hobby',
      'transcript': prompt ?? 'hobby',
      'match_percent': mockMatchPercent,
      'feedback': mockMatchPercent >= 80 ? 'Đã khớp từ mẫu.' : 'Chưa khớp câu mẫu.',
      'source_label': '[Unit 1, Page 8]',
      'created_at': '2026-09-25T00:00:00Z',
      'missing_words': [],
      'extra_words': [],
    });
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class FakeRecorder implements SpeechRecorder {
  int plays = 0;
  final bool denied;
  FakeRecorder({this.denied = false});
  @override
  Future<void> start() async {
    if (denied) {
      throw const SpeechRecordingException('Chưa có quyền microphone.');
    }
  }

  @override
  Future<Uint8List> stop() async => Uint8List.fromList([1, 2, 3]);
  @override
  Future<void> play(Uint8List bytes) async {
    plays++;
  }

  @override
  Future<void> dispose() async {}
}

void main() {
  testWidgets('silence error asks learner to record again', (tester) async {
    final api = FakeLearningApi()
      ..submitError = const ApiException(
        code: 'no_speech',
        message: 'No speech',
        statusCode: 422,
      );
    await tester.pumpWidget(
      MaterialApp(
        home: SpeakingScreen(
          api: api,
          card: FakeLearningApi.card,
          recorder: FakeRecorder(),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Thu âm'));
    await tester.pump();
    await tester.tap(find.text('Dừng thu'));
    await tester.pumpAndSettle();
    expect(
      find.text(
        'Chưa nghe rõ bản thu. Em hãy chọn Thu lại và nói rõ trong 15 giây.',
      ),
      findsOneWidget,
    );
  });
  testWidgets('blank recall can reveal and record not remembered', (
    tester,
  ) async {
    final api = FakeLearningApi();
    await tester.pumpWidget(
      MaterialApp(
        home: ReviewScreen(
          api: api,
          deck: const FlashcardDeck(
            id: 'deck',
            name: 'My words',
            kind: 'personal',
            cardCount: 1,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Xem đáp án'));
    await tester.pumpAndSettle();
    expect(find.text('hobby'), findsOneWidget);
    await tester.tap(find.text('Chưa nhớ'));
    await tester.pumpAndSettle();
    expect(api.reviews.single.answer, '');
    expect(api.reviews.single.rating, 'again');
  });
  testWidgets('offline voice service can be retried in place', (tester) async {
    final api = FakeLearningApi()..voicesAvailable = false;
    await tester.pumpWidget(
      MaterialApp(
        home: SpeakingScreen(
          api: api,
          card: FakeLearningApi.card,
          recorder: FakeRecorder(),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.textContaining('chưa sẵn sàng'), findsOneWidget);
    api.voicesAvailable = true;
    await tester.tap(find.text('Tải lại giọng đọc'));
    await tester.pumpAndSettle();
    expect(find.textContaining('chưa sẵn sàng'), findsNothing);
  });
  testWidgets('late audio response cannot play after leaving screen', (
    tester,
  ) async {
    final api = FakeLearningApi()..preview = Completer<Uint8List>();
    final recorder = FakeRecorder();
    await tester.pumpWidget(
      MaterialApp(
        home: SpeakingScreen(
          api: api,
          card: FakeLearningApi.card,
          recorder: recorder,
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Nghe thử giọng'));
    await tester.pump();
    await tester.pumpWidget(const MaterialApp(home: SizedBox()));
    api.preview!.complete(Uint8List.fromList([1, 2]));
    await tester.pumpAndSettle();
    expect(recorder.plays, 0);
  });
  testWidgets('recall retry is idempotent and retains request identity', (
    tester,
  ) async {
    final api = FakeLearningApi();
    await tester.pumpWidget(
      MaterialApp(
        home: ReviewScreen(
          api: api,
          deck: const FlashcardDeck(
            id: 'deck',
            name: 'Unit 1',
            kind: 'textbook',
            cardCount: 1,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('hobby'), findsOneWidget);
    expect(find.text('Đã nhớ'), findsOneWidget);
    await tester.tap(find.text('Đã nhớ'));
    await tester.pumpAndSettle();
    expect(find.text('Thử lại'), findsOneWidget);
    await tester.tap(find.text('Thử lại'));
    await tester.pumpAndSettle();
    expect(api.reviews.length, 2);
    expect(api.reviews.first.requestId, api.reviews.last.requestId);
    expect(api.reviews.first.rating, 'good');
  });
  testWidgets('published deck offers copy but no edit move or delete', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: DeckScreen(
          api: FakeLearningApi(),
          deck: const FlashcardDeck(
            id: 'deck',
            name: 'Unit 1',
            kind: 'textbook',
            cardCount: 1,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byType(PopupMenuButton<String>));
    await tester.pumpAndSettle();
    expect(find.text('Lưu vào bộ cá nhân'), findsOneWidget);
    expect(find.text('Sửa từ'), findsNothing);
    expect(find.text('Xóa từ'), findsNothing);
    expect(find.text('Chuyển bộ'), findsNothing);
  });
  testWidgets('permission denial explains recovery without sending audio', (
    tester,
  ) async {
    final api = FakeLearningApi();
    await tester.pumpWidget(
      MaterialApp(
        home: SpeakingScreen(
          api: api,
          card: FakeLearningApi.card,
          recorder: FakeRecorder(denied: true),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Thu âm'));
    await tester.pumpAndSettle();
    expect(find.text('Chưa có quyền microphone.'), findsOneWidget);
    expect(find.text('Gửi bản thu'), findsNothing);
    expect(api.requests, isEmpty);
  });
  testWidgets('learning entry shows available decks and two learning modes', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(home: LearningScreen(api: FakeLearningApi())),
    );
    await tester.pumpAndSettle();
    expect(find.text('Unit 1'), findsOneWidget);
    expect(find.text('Luyện nói'), findsOneWidget);
  });
  testWidgets(
    'stop recording automatically submits and retry retains request identity',
    (tester) async {
      final api = FakeLearningApi();
      await tester.pumpWidget(
        MaterialApp(
          home: SpeakingScreen(
            api: api,
            card: Flashcard.fromJson({
              'id': 'card',
              'deck_id': 'deck',
              'word': 'hobby',
              'meaning': 'sở thích',
            }),
            recorder: FakeRecorder(),
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text('Thu âm'));
      await tester.pump();
      await tester.pump(const Duration(seconds: 16));
      await tester.pumpAndSettle();
      expect(api.requests.length, 1);
      await tester.tap(find.text('Gửi bản thu'));
      await tester.pumpAndSettle();
      expect(api.requests.length, 2);
      expect(api.requests.first, api.requests.last);
      expect(find.textContaining('100%'), findsOneWidget);
      expect(find.textContaining('không phải điểm phát âm'), findsOneWidget);
    },
  );
  testWidgets(
    'review screen shows audio speaker button and plays audio via tts',
    (tester) async {
      final api = FakeLearningApi();
      final recorder = FakeRecorder();
      final tts = FakeTtsService();
      await tester.pumpWidget(
        MaterialApp(
          home: ReviewScreen(
            api: api,
            deck: const FlashcardDeck(
              id: 'deck',
              name: 'Unit 1',
              kind: 'textbook',
              cardCount: 1,
            ),
            audioPlayer: recorder,
            ttsService: tts,
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.byIcon(Icons.volume_up), findsOneWidget);
      await tester.tap(find.byIcon(Icons.volume_up));
      await tester.pumpAndSettle();
      expect(tts.spoken.length, 1);
      expect(tts.spoken[0].text, 'hobby');
      expect(tts.spoken[0].language, 'en-GB');
      expect(api.cardAudioCalls, 0);
    },
  );
  testWidgets(
    'review screen falls back to backend audio when tts fails',
    (tester) async {
      final api = FakeLearningApi();
      final recorder = FakeRecorder();
      final tts = FakeTtsService()..error = Exception('TTS error');
      await tester.pumpWidget(
        MaterialApp(
          home: ReviewScreen(
            api: api,
            deck: const FlashcardDeck(
              id: 'deck',
              name: 'Unit 1',
              kind: 'textbook',
              cardCount: 1,
            ),
            audioPlayer: recorder,
            ttsService: tts,
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byIcon(Icons.volume_up));
      await tester.pumpAndSettle();
      expect(api.cardAudioCalls, 1);
      expect(recorder.plays, 1);
    },
  );
  testWidgets(
    'swiping flashcard horizontally past threshold rates and transitions',
    (tester) async {
      final api = FakeLearningApi();
      await tester.pumpWidget(
        MaterialApp(
          home: ReviewScreen(
            api: api,
            deck: const FlashcardDeck(
              id: 'deck',
              name: 'Unit 1',
              kind: 'textbook',
              cardCount: 1,
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('hobby'), findsOneWidget);
      // Swipe card to the right past threshold (> 110px)
      await tester.drag(find.text('hobby'), const Offset(160, 0));
      await tester.pumpAndSettle();
      expect(api.reviews.isNotEmpty, isTrue);
      expect(api.reviews.first.rating, 'good');
    },
  );
  testWidgets(
    'speaking screen plays sample audio via tts with fallback to backend',
    (tester) async {
      final api = FakeLearningApi();
      final recorder = FakeRecorder();
      final tts = FakeTtsService();
      await tester.pumpWidget(
        MaterialApp(
          home: SpeakingScreen(
            api: api,
            card: FakeLearningApi.card,
            recorder: recorder,
            ttsService: tts,
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(
        find.text('Chưa có audio tiếng Anh đã kiểm duyệt cho từ này.'),
        findsNothing,
      );
      expect(find.text('Nghe mẫu tiếng Anh'), findsOneWidget);
      await tester.tap(find.text('Nghe mẫu tiếng Anh'));
      await tester.pumpAndSettle();
      expect(tts.spoken.length, 1);
      expect(tts.spoken[0].text, 'hobby');
      expect(tts.spoken[0].language, 'en-GB');
      expect(api.cardAudioCalls, 0);
    },
  );
  testWidgets(
    'deck screen in flashcard mode plays pronunciation audio via tts',
    (tester) async {
      final api = FakeLearningApi();
      final player = FakeRecorder();
      final tts = FakeTtsService();
      await tester.pumpWidget(
        MaterialApp(
          home: DeckScreen(
            api: api,
            deck: const FlashcardDeck(
              id: 'deck',
              name: 'Unit 1',
              kind: 'textbook',
              cardCount: 1,
            ),
            speaking: false,
            audioPlayer: player,
            ttsService: tts,
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Nghe phát âm tiếng Anh'), findsOneWidget);
      expect(find.text('Luyện nói từ này'), findsNothing);

      await tester.tap(find.text('Nghe phát âm tiếng Anh'));
      await tester.pumpAndSettle();

      expect(tts.spoken.length, 1);
      expect(tts.spoken[0].text, 'hobby');
      expect(tts.spoken[0].language, 'en-GB');
      expect(api.cardAudioCalls, 0);
    },
  );
  testWidgets(
    'deck screen falls back to backend audio when tts fails',
    (tester) async {
      final api = FakeLearningApi();
      final player = FakeRecorder();
      final tts = FakeTtsService()..error = Exception('TTS unavailable');
      await tester.pumpWidget(
        MaterialApp(
          home: DeckScreen(
            api: api,
            deck: const FlashcardDeck(
              id: 'deck',
              name: 'Unit 1',
              kind: 'textbook',
              cardCount: 1,
            ),
            speaking: false,
            audioPlayer: player,
            ttsService: tts,
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Nghe phát âm tiếng Anh'));
      await tester.pumpAndSettle();

      expect(api.cardAudioCalls, 1);
      expect(player.plays, 1);
    },
  );
  testWidgets(
    'deck screen in speaking mode offers speaking screen navigation',
    (tester) async {
      final api = FakeLearningApi();
      await tester.pumpWidget(
        MaterialApp(
          home: DeckScreen(
            api: api,
            deck: const FlashcardDeck(
              id: 'deck',
              name: 'Unit 1',
              kind: 'textbook',
              cardCount: 1,
            ),
            speaking: true,
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Ôn luyện nói cả câu'), findsOneWidget);
      expect(find.text('Luyện nói từ này'), findsOneWidget);
      expect(find.text('Nghe phát âm tiếng Anh'), findsNothing);
    },
  );
  testWidgets(
    'deck screen audio failure shows snackbar error message',
    (tester) async {
      final api = FakeLearningApi()..cardAudioError = Exception('Network error');
      final player = FakeRecorder();
      final tts = FakeTtsService()..error = Exception('TTS unavailable');
      await tester.pumpWidget(
        MaterialApp(
          home: DeckScreen(
            api: api,
            deck: const FlashcardDeck(
              id: 'deck',
              name: 'Unit 1',
              kind: 'textbook',
              cardCount: 1,
            ),
            speaking: false,
            audioPlayer: player,
            ttsService: tts,
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Nghe phát âm tiếng Anh'));
      await tester.pumpAndSettle();

      expect(find.textContaining('Tạm thời chưa phát được âm thanh'), findsOneWidget);
      expect(player.plays, 0);
    },
  );
  testWidgets(
    'deck screen late audio response cannot play after leaving screen',
    (tester) async {
      final api = FakeLearningApi()..cardAudioCompleter = Completer<Uint8List>();
      final player = FakeRecorder();
      final tts = FakeTtsService()..error = Exception('TTS unavailable');
      await tester.pumpWidget(
        MaterialApp(
          home: Navigator(
            onGenerateRoute: (settings) => MaterialPageRoute<void>(
              builder: (context) => DeckScreen(
                api: api,
                deck: const FlashcardDeck(
                  id: 'deck',
                  name: 'Unit 1',
                  kind: 'textbook',
                  cardCount: 1,
                ),
                speaking: false,
                audioPlayer: player,
                ttsService: tts,
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Nghe phát âm tiếng Anh'));
      await tester.pump();

      await tester.pumpWidget(
        const MaterialApp(home: Scaffold(body: Text('Trang khác'))),
      );
      await tester.pumpAndSettle();

      api.cardAudioCompleter!.complete(Uint8List.fromList([1, 2, 3]));
      await tester.pumpAndSettle();

      expect(player.plays, 0);
    },
  );
  testWidgets(
    'sentence practice screen renders sentence chips and handles auto-advance on pass',
    (tester) async {
      final api = FakeLearningApi()
        ..failFirstSpeakingRequest = false
        ..mockMatchPercent = 90;
      final recorder = FakeRecorder();
      final tts = FakeTtsService();
      await tester.pumpWidget(
        MaterialApp(
          home: SentencePracticeScreen(
            api: api,
            deck: const FlashcardDeck(
              id: 'deck',
              name: 'Unit 1',
              kind: 'textbook',
              cardCount: 1,
            ),
            recorder: recorder,
            ttsService: tts,
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.textContaining('Câu 1 / 1'), findsOneWidget);
      expect(find.text('Nghe mẫu (1.0x)'), findsOneWidget);
      expect(find.text('Thu âm'), findsOneWidget);
      expect(find.text('Bỏ qua'), findsOneWidget);

      await tester.tap(find.text('Nghe mẫu (1.0x)'));
      await tester.pumpAndSettle();
      expect(tts.spoken.isNotEmpty, isTrue);

      await tester.tap(find.text('Thu âm'));
      await tester.pump();
      expect(find.text('Dừng thu & Chấm điểm'), findsOneWidget);

      await tester.tap(find.text('Dừng thu & Chấm điểm'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      expect(find.textContaining('Xuất sắc!'), findsOneWidget);
      expect(api.requests.isNotEmpty, isTrue);

      // Wait for auto-advance timer (1.8s) to transition to summary
      await tester.pumpAndSettle();

      expect(find.text('🎉 Hoàn thành bài luyện nói!'), findsOneWidget);
      expect(find.text('Luyện tập lại từ đầu'), findsOneWidget);
    },
  );
  testWidgets(
    'sentence practice screen allows skip when score is below 80 percent',
    (tester) async {
      final api = FakeLearningApi()
        ..failFirstSpeakingRequest = false
        ..mockMatchPercent = 60;
      final recorder = FakeRecorder();
      final tts = FakeTtsService();
      await tester.pumpWidget(
        MaterialApp(
          home: SentencePracticeScreen(
            api: api,
            deck: const FlashcardDeck(
              id: 'deck',
              name: 'Unit 1',
              kind: 'textbook',
              cardCount: 1,
            ),
            recorder: recorder,
            ttsService: tts,
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Thu âm'));
      await tester.pump();
      await tester.tap(find.text('Dừng thu & Chấm điểm'));
      await tester.pumpAndSettle();

      expect(find.textContaining('Cần đạt ≥ 80%'), findsOneWidget);
      expect(find.text('Thử lại ↻'), findsOneWidget);
      expect(find.text('Bỏ qua'), findsOneWidget);

      // Tap skip
      await tester.tap(find.text('Bỏ qua'));
      await tester.pumpAndSettle();

      // Advancing past the only card reaches summary
      expect(find.text('🎉 Hoàn thành bài luyện nói!'), findsOneWidget);
    },
  );
  testWidgets(
    'flashcard review back card does not render example sentence',
    (tester) async {
      final api = FakeLearningApi();
      await tester.pumpWidget(
        MaterialApp(
          home: ReviewScreen(
            api: api,
            deck: const FlashcardDeck(
              id: 'deck',
              name: 'Unit 1',
              kind: 'textbook',
              cardCount: 1,
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      // Tap card to flip to back
      await tester.tap(find.text('hobby'));
      await tester.pumpAndSettle();

      // Back shows Vietnamese meaning
      expect(find.text('sở thích'), findsOneWidget);
      // Example sentence is not present
      expect(find.textContaining('My favourite'), findsNothing);
    },
  );
}


