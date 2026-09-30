import 'dart:typed_data';

import '../api/api_client.dart';
import 'learning_api.dart';

mixin ApiLearning on Object implements LearningApi {
  ApiClient get learningClient;
  Map<String, dynamic> _json(Map<String, Object?> body) =>
      Map<String, dynamic>.from(body);
  List<T> _items<T>(
    Map<String, Object?> body,
    T Function(Map<String, dynamic>) parse,
  ) => (body['items'] as List)
      .map((v) => parse(Map<String, dynamic>.from(v as Map)))
      .toList();

  @override
  Future<List<FlashcardDeck>> loadDecks() async => _items(
    (await learningClient.getJson('/api/v1/flashcards/decks')).body,
    FlashcardDeck.fromJson,
  );
  @override
  Future<FlashcardDeck> createDeck(String name) async => FlashcardDeck.fromJson(
    _json(
      (await learningClient.postJson('/api/v1/flashcards/decks', {
        'name': name,
      })).body,
    ),
  );
  @override
  Future<FlashcardDeck> renameDeck(String id, String name) async =>
      FlashcardDeck.fromJson(
        _json(
          (await learningClient.patchJson('/api/v1/flashcards/decks/$id', {
            'name': name,
          })).body,
        ),
      );
  @override
  Future<void> deleteDeck(String id) =>
      learningClient.delete('/api/v1/flashcards/decks/$id');
  @override
  Future<List<Flashcard>> loadCards(String deckId) async => _items(
    (await learningClient.getJson('/api/v1/flashcards/decks/$deckId/cards'))
        .body,
    Flashcard.fromJson,
  );
  @override
  Future<Flashcard> createCard(
    String deckId,
    Map<String, Object?> fields,
  ) async => Flashcard.fromJson(
    _json(
      (await learningClient.postJson(
        '/api/v1/flashcards/decks/$deckId/cards',
        fields,
      )).body,
    ),
  );
  @override
  Future<Flashcard> updateCard(String id, Map<String, Object?> fields) async =>
      Flashcard.fromJson(
        _json(
          (await learningClient.patchJson(
            '/api/v1/flashcards/cards/$id',
            fields,
          )).body,
        ),
      );
  @override
  Future<void> deleteCard(String id) =>
      learningClient.delete('/api/v1/flashcards/cards/$id');
  @override
  Future<List<Flashcard>> loadReviewCards(String deckId) async => _items(
    (await learningClient.getJson(
      '/api/v1/flashcards/review?deck_id=${Uri.encodeQueryComponent(deckId)}',
    )).body,
    Flashcard.fromJson,
  );
  @override
  Future<FlashcardReviewResult> reviewCard(
    String id, {
    required String requestId,
    required String answer,
    required String rating,
  }) async => FlashcardReviewResult.fromJson(
    _json(
      (await learningClient.postJson('/api/v1/flashcards/cards/$id/review', {
        'request_id': requestId,
        'answer': answer,
        'rating': rating,
      })).body,
    ),
  );
  @override
  Future<Flashcard> flagCard(String id, bool difficult) async =>
      Flashcard.fromJson(
        _json(
          (await learningClient.patchJson('/api/v1/flashcards/cards/$id/flag', {
            'difficult': difficult,
          })).body,
        ),
      );
  @override
  Future<LearningProgress> loadLearningProgress() async =>
      LearningProgress.fromJson(
        _json((await learningClient.getJson('/api/v1/learning/progress')).body),
      );
  @override
  Future<SpeakingVoices> loadVoices() async => SpeakingVoices.fromJson(
    _json((await learningClient.getJson('/api/v1/speaking/voices')).body),
  );
  @override
  Future<void> selectVoice(String id) async {
    await learningClient.putJson('/api/v1/speaking/voice', {'voice_id': id});
  }

  @override
  Future<Uint8List> previewVoice(String id) => learningClient.audioBytes(
    '/api/v1/speaking/preview',
    payload: {'voice_id': id},
  );
  @override
  Future<SpeakingResult> submitSpeaking({
    required String requestId,
    required String cardId,
    required String voiceId,
    required Uint8List audio,
  }) async {
    final query = Uri(queryParameters: {'card_id': cardId, 'voice_id': voiceId})
        .query;
    final response = await learningClient.postMultipart(
      '/api/v1/speaking/attempts/$requestId?$query',
      fieldName: 'audio',
      filename: 'recording.wav',
      mediaType: 'audio/wav',
      bytes: audio,
    );
    return SpeakingResult.fromJson(_json(response.body));
  }

  @override
  Future<List<SpeakingResult>> loadSpeakingHistory() async => _items(
    (await learningClient.getJson('/api/v1/speaking/history')).body,
    SpeakingResult.fromJson,
  );
  @override
  Future<Uint8List> loadSpeakingAudio(String id) => learningClient.audioBytes(
    '/api/v1/speaking/attempts/$id/audio',
    payload: {},
  );
  @override
  Future<Uint8List> loadSampleAudio(String url) =>
      learningClient.audioBytes(url);
}
