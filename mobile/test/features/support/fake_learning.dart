import 'dart:typed_data';
import 'package:english7_mobile/app/learning_api.dart';

mixin EmptyLearning implements LearningApi {
  @override
  Future<List<FlashcardDeck>> loadDecks() async => [];
  @override
  Future<LearningProgress> loadLearningProgress() async => const LearningProgress(reviewedCards: 0, dueCards: 0, difficultCards: 0, speakingCount: 0, recentSpeaking: []);
  @override
  Future<SpeakingVoices> loadVoices() async => const SpeakingVoices(items: [], selectedVoice: null, available: false);
  @override
  Future<List<SpeakingResult>> loadSpeakingHistory() async => [];
  @override
  Future<List<Flashcard>> loadCards(String deckId) async => [];
  @override
  Future<List<Flashcard>> loadReviewCards(String deckId) async => [];
  @override
  Future<FlashcardDeck> createDeck(String name) async => throw UnimplementedError();
  @override
  Future<FlashcardDeck> renameDeck(String id, String name) async => throw UnimplementedError();
  @override
  Future<void> deleteDeck(String id) async => throw UnimplementedError();
  @override
  Future<Flashcard> createCard(String deckId, Map<String, Object?> fields) async => throw UnimplementedError();
  @override
  Future<Flashcard> updateCard(String id, Map<String, Object?> fields) async => throw UnimplementedError();
  @override
  Future<void> deleteCard(String id) async => throw UnimplementedError();
  @override
  Future<FlashcardReviewResult> reviewCard(String id, {required String requestId, required String answer, required String rating}) async => throw UnimplementedError();
  @override
  Future<Flashcard> flagCard(String id, bool difficult) async => throw UnimplementedError();
  @override
  Future<void> selectVoice(String id) async => throw UnimplementedError();
  @override
  Future<Uint8List> previewVoice(String id) async => throw UnimplementedError();
  @override
  Future<SpeakingResult> submitSpeaking({required String requestId, required String cardId, required String voiceId, required Uint8List audio, String? prompt}) async => throw UnimplementedError();
  @override
  Future<Uint8List> loadSpeakingAudio(String id) async => throw UnimplementedError();
  @override
  Future<Uint8List> loadSampleAudio(String url) async => throw UnimplementedError();
  @override
  Future<Uint8List> loadCardAudio(String cardId) async => throw UnimplementedError();
}
