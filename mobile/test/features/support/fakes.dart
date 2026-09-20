import 'dart:typed_data';

import 'package:english7_mobile/app/student_api.dart';
import 'package:english7_mobile/features/tutor/image_selector.dart';

class FakeStudentApi implements StudentApi {
  static const defaultProfile = StudentProfile(
    id: 'user-1',
    email: 'student@example.com',
    role: 'student',
  );

  bool refuseTutor = false;
  final tutorQueries = <TutorQuery>[];
  StudentProfile profile = defaultProfile;
  StudentProfile? restoredProfile;
  Object? restoreError;
  Object? profileUpdateError;
  int restoreCalls = 0;
  int updateProfileCalls = 0;
  bool logoutCalled = false;
  List<String>? passwordArguments;

  @override
  Future<void> login(String email, String password) async {}

  @override
  Future<StudentProfile?> restoreSession() async {
    restoreCalls += 1;
    if (restoreError != null) throw restoreError!;
    return restoredProfile;
  }

  @override
  Future<StudentProfile> loadProfile() async => profile;

  @override
  Future<StudentProfile> updateProfile(ProfileUpdate update) async {
    updateProfileCalls += 1;
    if (profileUpdateError != null) throw profileUpdateError!;
    profile = StudentProfile(
      id: profile.id,
      email: profile.email,
      role: profile.role,
      fullName: update.fullName,
      dateOfBirth: update.dateOfBirth,
      gender: update.gender,
      schoolName: update.schoolName,
      className: update.className,
    );
    return profile;
  }

  @override
  Future<void> changePassword(
    String currentPassword,
    String newPassword,
    String confirmation,
  ) async {
    passwordArguments = [currentPassword, newPassword, confirmation];
  }

  @override
  Future<void> logout() async {
    logoutCalled = true;
    restoredProfile = null;
  }

  @override
  Future<QuizOptions> loadQuizOptions() async =>
      const QuizOptions([15, 45, 60], 10, 90, 2);

  @override
  Future<List<LessonSummary>> loadLessons() async => const [
    LessonSummary(1, 'Hobbies', 'Getting Started', id: 'unit-1'),
    LessonSummary(2, 'Healthy Living', 'A Closer Look', id: 'unit-2'),
  ];

  @override
  Future<List<LessonFragment>> loadFragments(String unitId) async => const [
    LessonFragment(
      id: 'frag-1',
      pdfPage: 8,
      printedPage: 8,
      text: 'Ann: Your house is very nice, Trang.\nTrang: Thanks! Let\'s go upstairs. I\'ll show you my room.',
      sectionTitle: 'GETTING STARTED - My favourite hobby',
      activityNumber: '1',
      activityType: 'reading_dialogue',
      activityInstruction: 'Listen and read.',
    ),
  ];

  LessonDetail? customDetail;

  @override
  Future<LessonDetail> loadLessonDetail(String unitId) async => customDetail ?? const LessonDetail(
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
          LessonActivity(
            id: 'act-1',
            number: '1',
            activityType: 'reading_dialogue',
            instruction: 'Listen and read the conversation between Ann and Trang.',
            fragments: [
              LessonFragment(
                id: 'frag-1',
                pdfPage: 8,
                printedPage: 8,
                text: 'Ann: Your house is very nice, Trang.\nTrang: Thanks! Let\'s go upstairs. I\'ll show you my room.\nAnn: I love your dollhouse. It\'s amazing. Did you make it yourself?\nTrang: Yes. I like building dollhouses very much.\nAnn: Really? Is it hard to build one?\nTrang: Not really. All you need is some cardboard and glue. Then just use a bit of creativity. What do you do in your free time?\nAnn: I like horse riding.\nTrang: That\'s rather unusual. Not many people do that.\nAnn: Actually, it\'s more common than you think. There are some horse riding clubs in Ha Noi now. I go to the Riders\' Club every Sunday.\nTrang: I\'d love to go to your club this Sunday. I want to learn how to ride.\nAnn: Sure. My lesson starts at 8 a.m.',
                sectionTitle: 'GETTING STARTED - My favourite hobby',
                activityNumber: '1',
                activityType: 'reading_dialogue',
                activityInstruction: 'Listen and read.',
              ),
            ],
          ),
        ],
      ),
    ],
  );

  @override
  Future<TutorResult> askTutor(TutorQuery query) async {
    tutorQueries.add(query);
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
  Future<SelectedImage?> select() async => SelectedImage(
    'textbook-page.jpg',
    Uint8List.fromList([1, 2, 3]),
    'image/jpeg',
  );
}
