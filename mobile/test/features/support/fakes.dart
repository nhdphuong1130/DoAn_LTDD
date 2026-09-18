import 'package:english7_mobile/app/student_api.dart';
import 'package:english7_mobile/features/tutor/image_selector.dart';

class FakeStudentApi implements StudentApi {
  bool refuseTutor = false;

  @override
  Future<void> login(String email, String password) async {}

  @override
  Future<List<LessonSummary>> loadLessons() async => const [
    LessonSummary(1, 'Hobbies', 'Getting Started'),
    LessonSummary(2, 'Healthy Living', 'A Closer Look'),
  ];

  @override
  Future<TutorResult> askTutor(TutorQuery query) async {
    if (refuseTutor) throw const TutorRefusal('out_of_scope');
    return TutorResult(
      query.language == TutorLanguage.vietnamese
          ? 'Tập thể dục mỗi ngày.'
          : 'Exercise every day.',
      const [SourceReference('fragment-1', 22, 20)],
    );
  }

  @override
  Future<QuizSession> createQuiz(QuizSetup setup) async => QuizSession(
    'quiz-1',
    setup.durationMinutes,
    setup.difficulty,
    const [QuizQuestion('question-1', 'Choose a healthy habit')],
  );

  @override
  Future<QuizResult> submitQuiz(String quizId) async => const QuizResult(8, 10);
}

class FakeImageSelector implements ImageSelector {
  @override
  Future<SelectedImage?> select() async =>
      const SelectedImage('textbook-page.jpg');
}
