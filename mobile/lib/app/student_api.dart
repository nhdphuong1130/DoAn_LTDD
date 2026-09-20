import 'dart:typed_data';

enum TutorLanguage { vietnamese, english }

enum ProfileGender { male, female, other, preferNotToSay }

class StudentProfile {
  final String id;
  final String email;
  final String role;
  final String? fullName;
  final DateTime? dateOfBirth;
  final ProfileGender? gender;
  final String? schoolName;
  final String? className;

  const StudentProfile({
    required this.id,
    required this.email,
    required this.role,
    this.fullName,
    this.dateOfBirth,
    this.gender,
    this.schoolName,
    this.className,
  });
}

class ProfileUpdate {
  final String? fullName;
  final DateTime? dateOfBirth;
  final ProfileGender? gender;
  final String? schoolName;
  final String? className;

  const ProfileUpdate({
    this.fullName,
    this.dateOfBirth,
    this.gender,
    this.schoolName,
    this.className,
  });
}

class LessonSummary {
  final int unitNumber;
  final String title;
  final String sectionTitle;
  const LessonSummary(this.unitNumber, this.title, this.sectionTitle);
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
  Future<StudentProfile?> restoreSession();
  Future<StudentProfile> loadProfile();
  Future<StudentProfile> updateProfile(ProfileUpdate update);
  Future<void> changePassword(
    String currentPassword,
    String newPassword,
    String confirmation,
  );
  Future<void> logout();
  Future<List<LessonSummary>> loadLessons();
  Future<QuizOptions> loadQuizOptions();
  Future<TutorResult> askTutor(TutorQuery query);
  Future<QuizSession> createQuiz(QuizSetup setup);
  Future<QuizResult> submitQuiz(String quizId);
}
