import 'dart:typed_data';

enum TutorLanguage { vietnamese, english }

class LessonSummary {
  final int unitNumber;
  final String title;
  final String sectionTitle;
  final String id;
  const LessonSummary(this.unitNumber, this.title, this.sectionTitle, {this.id = ''});
}

class LessonFragment {
  final String id;
  final int? printedPage;
  final int pdfPage;
  final String text;
  final String? sectionTitle;
  final String? activityNumber;
  final String? activityType;
  final String? activityInstruction;
  const LessonFragment({
    required this.id,
    this.printedPage,
    required this.pdfPage,
    required this.text,
    this.sectionTitle,
    this.activityNumber,
    this.activityType,
    this.activityInstruction,
  });
}

class LessonAudioTrack {
  final String id;
  final int trackNumber;
  final String audioUrl;
  const LessonAudioTrack({
    required this.id,
    required this.trackNumber,
    required this.audioUrl,
  });
}

class LessonActivity {
  final String id;
  final String? number;
  final String activityType;
  final String? instruction;
  final List<LessonAudioTrack> audioTracks;
  final List<LessonFragment> fragments;
  const LessonActivity({
    required this.id,
    this.number,
    required this.activityType,
    this.instruction,
    this.audioTracks = const [],
    required this.fragments,
  });
}

class LessonSection {
  final String id;
  final String title;
  final String sectionType;
  final int position;
  final List<LessonActivity> activities;
  const LessonSection({
    required this.id,
    required this.title,
    required this.sectionType,
    required this.position,
    required this.activities,
  });
}

class LessonDetail {
  final String id;
  final int unitNumber;
  final String title;
  final List<LessonSection> sections;
  const LessonDetail({
    required this.id,
    required this.unitNumber,
    required this.title,
    required this.sections,
  });
}

class SourceReference {
  final String fragmentId;
  final int pdfPage;
  final int? printedPage;
  const SourceReference(this.fragmentId, this.pdfPage, this.printedPage);
}

class TutorImage {
  final String name;
  final Uint8List bytes;
  final String mediaType;
  const TutorImage(this.name, this.bytes, this.mediaType);
}

class TutorQuery {
  final String question;
  final TutorLanguage language;
  final TutorImage? image;
  const TutorQuery(this.question, this.language, this.image);
}

class TutorResult {
  final String answer;
  final List<SourceReference> citations;
  const TutorResult(this.answer, this.citations);
}

class TutorRefusal implements Exception {
  final String code;
  const TutorRefusal(this.code);
}

class QuizSetup {
  final int durationMinutes;
  final String difficulty;
  const QuizSetup(this.durationMinutes, this.difficulty);
}

class QuizOptions {
  final List<int> presetDurations;
  final int customMinimumMinutes;
  final int customMaximumMinutes;
  final int maxAudioPlays;
  const QuizOptions(
    this.presetDurations,
    this.customMinimumMinutes,
    this.customMaximumMinutes,
    this.maxAudioPlays,
  );
}

class QuizQuestion {
  final String id;
  final String prompt;
  const QuizQuestion(this.id, this.prompt);
}

class QuizSession {
  final String id;
  final int durationMinutes;
  final String difficulty;
  final List<QuizQuestion> questions;
  const QuizSession(
    this.id,
    this.durationMinutes,
    this.difficulty,
    this.questions,
  );
}

class QuizResult {
  final int correct;
  final int total;
  const QuizResult(this.correct, this.total);
}

abstract interface class StudentApi {
  Future<void> login(String email, String password);
  Future<List<LessonSummary>> loadLessons();
  Future<List<LessonFragment>> loadFragments(String unitId);
  Future<LessonDetail> loadLessonDetail(String unitId);
  Future<QuizOptions> loadQuizOptions();
  Future<TutorResult> askTutor(TutorQuery query);
  Future<QuizSession> createQuiz(QuizSetup setup);
  Future<QuizResult> submitQuiz(String quizId);
}
