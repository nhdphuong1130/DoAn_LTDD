import 'dart:math';
import 'dart:typed_data';

/// A fresh UUID for an action. Keep it unchanged while retrying that action.
String learningRequestId() {
  final random = Random.secure();
  final bytes = List<int>.generate(16, (_) => random.nextInt(256));
  bytes[6] = (bytes[6] & 15) | 64;
  bytes[8] = (bytes[8] & 63) | 128;
  final hex = bytes.map((v) => v.toRadixString(16).padLeft(2, '0')).join();
  return '${hex.substring(0, 8)}-${hex.substring(8, 12)}-${hex.substring(12, 16)}-${hex.substring(16, 20)}-${hex.substring(20)}';
}

class FlashcardDeck {
  final String id, name, kind;
  final int? unitNumber;
  final int cardCount;
  const FlashcardDeck({
    required this.id,
    required this.name,
    required this.kind,
    this.unitNumber,
    required this.cardCount,
  });
  bool get isPersonal => kind == 'personal';
  factory FlashcardDeck.fromJson(Map<String, dynamic> j) => FlashcardDeck(
    id: j['id'] as String,
    name: j['name'] as String,
    kind: j['kind'] as String,
    unitNumber: j['unit_number'] as int?,
    cardCount: j['card_count'] as int? ?? 0,
  );
}

class Flashcard {
  final String id, deckId, word, meaning, example, notes;
  final String? imageUrl, ipa, pos, sourceLabel, sourceFragmentId, audioUrl;
  final int? unitNumber, page;
  final bool difficult;
  final DateTime? dueAt;
  final int reviewCount;
  const Flashcard({
    required this.id,
    required this.deckId,
    required this.word,
    required this.meaning,
    this.example = '',
    this.notes = '',
    this.imageUrl,
    this.ipa,
    this.pos,
    this.sourceLabel,
    this.sourceFragmentId,
    this.audioUrl,
    this.unitNumber,
    this.page,
    this.difficult = false,
    this.dueAt,
    this.reviewCount = 0,
  });
  factory Flashcard.fromJson(Map<String, dynamic> j) => Flashcard(
    id: j['id'] as String,
    deckId: j['deck_id'] as String,
    word: j['word'] as String,
    meaning: j['meaning'] as String,
    example: j['example'] as String? ?? '',
    notes: j['notes'] as String? ?? '',
    imageUrl: j['image_url'] as String?,
    ipa: j['ipa'] as String?,
    pos: j['pos'] as String?,
    sourceLabel: j['source_label'] as String?,
    sourceFragmentId: j['source_fragment_id'] as String?,
    audioUrl: j['audio_url'] as String?,
    unitNumber: j['unit_number'] as int?,
    page: j['page'] as int?,
    difficult: j['difficult'] as bool? ?? false,
    dueAt: DateTime.tryParse(j['due_at'] as String? ?? ''),
    reviewCount: j['review_count'] as int? ?? 0,
  );
}

class FlashcardReviewResult {
  final bool correct;
  final String meaning;
  final DateTime dueAt;
  const FlashcardReviewResult({
    required this.correct,
    required this.meaning,
    required this.dueAt,
  });
  factory FlashcardReviewResult.fromJson(Map<String, dynamic> j) =>
      FlashcardReviewResult(
        correct: j['correct'] as bool,
        meaning: j['meaning'] as String,
        dueAt: DateTime.parse(j['due_at'] as String),
      );
}

class SpeakingVoice {
  final String id, name;
  const SpeakingVoice({required this.id, required this.name});
  factory SpeakingVoice.fromJson(Map<String, dynamic> j) =>
      SpeakingVoice(id: j['id'] as String, name: j['name'] as String);
}

class SpeakingVoices {
  final List<SpeakingVoice> items;
  final String? selectedVoice;
  final bool available;
  const SpeakingVoices({
    required this.items,
    required this.selectedVoice,
    required this.available,
  });
  factory SpeakingVoices.fromJson(Map<String, dynamic> j) => SpeakingVoices(
    items: (j['items'] as List)
        .map((v) => SpeakingVoice.fromJson(v as Map<String, dynamic>))
        .toList(),
    selectedVoice: j['selected_voice'] as String?,
    available: j['available'] as bool,
  );
}

class WordEvaluation {
  final String word;
  final String status; // 'correct', 'near', 'missing'
  final double score;
  final String? heard;
  const WordEvaluation({
    required this.word,
    required this.status,
    required this.score,
    this.heard,
  });
  factory WordEvaluation.fromJson(Map<String, dynamic> j) => WordEvaluation(
    word: j['word'] as String? ?? '',
    status: j['status'] as String? ?? 'missing',
    score: (j['score'] as num?)?.toDouble() ?? 0.0,
    heard: j['heard'] as String?,
  );
}

class SpeakingResult {
  final String id, cardId, prompt, transcript, feedback;
  final String? sourceLabel;
  final double matchPercent;
  final DateTime createdAt;
  final List<String> missingWords, extraWords;
  final List<WordEvaluation> wordEvaluations;
  const SpeakingResult({
    required this.id,
    required this.cardId,
    required this.prompt,
    required this.transcript,
    required this.feedback,
    this.sourceLabel,
    required this.matchPercent,
    required this.createdAt,
    required this.missingWords,
    required this.extraWords,
    this.wordEvaluations = const [],
  });
  factory SpeakingResult.fromJson(Map<String, dynamic> j) => SpeakingResult(
    id: j['id'] as String,
    cardId: j['card_id'] as String,
    prompt: j['prompt'] as String,
    transcript: j['transcript'] as String,
    feedback: j['feedback'] as String,
    sourceLabel: j['source_label'] as String?,
    matchPercent: (j['match_percent'] as num).toDouble(),
    createdAt: DateTime.parse(j['created_at'] as String),
    missingWords: List<String>.from(j['missing_words'] as List? ?? []),
    extraWords: List<String>.from(j['extra_words'] as List? ?? []),
    wordEvaluations: (j['word_evaluations'] as List? ?? [])
        .map((e) => WordEvaluation.fromJson(e as Map<String, dynamic>))
        .toList(),
  );
}

class LearningProgress {
  final int reviewedCards, dueCards, difficultCards, speakingCount;
  final List<SpeakingResult> recentSpeaking;
  const LearningProgress({
    required this.reviewedCards,
    required this.dueCards,
    required this.difficultCards,
    required this.speakingCount,
    required this.recentSpeaking,
  });
  factory LearningProgress.fromJson(Map<String, dynamic> j) => LearningProgress(
    reviewedCards: j['reviewed_cards'] as int,
    dueCards: j['due_cards'] as int,
    difficultCards: j['difficult_cards'] as int,
    speakingCount: j['speaking_count'] as int,
    recentSpeaking: (j['recent_speaking'] as List)
        .map((v) => SpeakingResult.fromJson(v as Map<String, dynamic>))
        .toList(),
  );
}

abstract interface class LearningApi {
  Future<List<FlashcardDeck>> loadDecks();
  Future<FlashcardDeck> createDeck(String name);
  Future<FlashcardDeck> renameDeck(String id, String name);
  Future<void> deleteDeck(String id);
  Future<List<Flashcard>> loadCards(String deckId);
  Future<Flashcard> createCard(String deckId, Map<String, Object?> fields);
  Future<Flashcard> updateCard(String id, Map<String, Object?> fields);
  Future<void> deleteCard(String id);
  Future<List<Flashcard>> loadReviewCards(String deckId);
  Future<FlashcardReviewResult> reviewCard(
    String id, {
    required String requestId,
    required String answer,
    required String rating,
  });
  Future<Flashcard> flagCard(String id, bool difficult);
  Future<LearningProgress> loadLearningProgress();
  Future<SpeakingVoices> loadVoices();
  Future<void> selectVoice(String id);
  Future<Uint8List> previewVoice(String id);
  Future<SpeakingResult> submitSpeaking({
    required String requestId,
    required String cardId,
    required String voiceId,
    required Uint8List audio,
    String? prompt,
  });
  Future<List<SpeakingResult>> loadSpeakingHistory();
  Future<Uint8List> loadSpeakingAudio(String id);
  Future<Uint8List> loadSampleAudio(String url);
  Future<Uint8List> loadCardAudio(String cardId);
}
