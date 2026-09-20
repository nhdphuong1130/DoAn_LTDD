import 'package:english7_mobile/app/english7_app.dart';
import 'package:english7_mobile/app/student_api.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support/fakes.dart';

class FakeExerciseStudentApi extends FakeStudentApi {
  @override
  Future<LessonDetail> loadLessonDetail(String unitId) async {
    return LessonDetail(
      id: 'unit-1',
      unitNumber: 1,
      title: 'Hobbies',
      sections: [
        LessonSection(
          id: 'sec-1',
          title: 'GETTING STARTED',
          sectionType: 'lesson',
          position: 1,
          activities: [
            LessonActivity(
              id: 'act-2',
              number: '2',
              activityType: 'reading_comprehension',
              instruction: 'Read the conversation again and tick (T) True or (F) False.',
              fragments: [
                LessonFragment(
                  id: 'frag-2',
                  pdfPage: 9,
                  printedPage: 9,
                  text: "1. Trang's room is on the first floor. -> False (Trang: 'Let's go upstairs.')\n"
                      "2. Ann goes to the Riders' Club once a week. -> True (Ann: 'I go to the Riders' Club every Sunday.')",
                ),
              ],
            ),
          ],
        ),
      ],
    );
  }
}

void main() {
  testWidgets('True/False exercise renders interactively with choices and explanation', (tester) async {
    await tester.pumpWidget(
      English7App(
        api: FakeExerciseStudentApi(),
        imageSelector: FakeImageSelector(),
      ),
    );
    await tester.pumpAndSettle();

    // Login
    await tester.enterText(find.byKey(const Key('email-field')), 'student@example.com');
    await tester.enterText(find.byKey(const Key('password-field')), 'password');
    await tester.tap(find.text('Đăng nhập'));
    await tester.pumpAndSettle();

    // Open lesson
    await tester.tap(find.text('Unit 1: Hobbies'));
    await tester.pumpAndSettle();

    // Verify raw answer string is NOT shown as plain text in the prompt
    expect(find.textContaining('-> False'), findsNothing);

    // Verify question prompt is shown cleanly
    expect(find.textContaining("Trang's room is on the first floor."), findsOneWidget);

    // Verify True and False interactive buttons are present
    expect(find.text('T'), findsWidgets);
    expect(find.text('F'), findsWidgets);

    // Initially explanation is hidden before answering
    expect(find.textContaining("Let's go upstairs"), findsNothing);

    // Tap 'T' (Wrong answer for question 1)
    await tester.tap(find.widgetWithText(OutlinedButton, 'T').first);
    await tester.pumpAndSettle();

    // Should indicate incorrect and reveal the explanation
    expect(find.textContaining('Chưa chính xác'), findsOneWidget);
    expect(find.textContaining("Let's go upstairs"), findsOneWidget);

    // Now tap 'F' (Correct answer for question 1)
    await tester.tap(find.widgetWithText(OutlinedButton, 'F').first);
    await tester.pumpAndSettle();

    // Should indicate correct with checkmark
    expect(find.textContaining('Chính xác'), findsOneWidget);
  });

  testWidgets('Image matching exercise renders images and allows word bank selection', (tester) async {
    final fakeApi = FakeStudentApiWithCustomDetail(
      LessonDetail(
        id: 'unit-1',
        unitNumber: 1,
        title: 'Hobbies',
        sections: [
          LessonSection(
            id: 'sec-1',
            title: 'GETTING STARTED',
            sectionType: 'lesson',
            position: 1,
            activities: [
              LessonActivity(
                id: 'act-3',
                number: '3',
                activityType: 'vocabulary',
                instruction: 'Write the words and phrases from the box under the correct pictures.',
                fragments: [
                  LessonFragment(
                    id: 'frag-3',
                    pdfPage: 9,
                    printedPage: 9,
                    text: "Word Bank:\n"
                        "[making models] [riding a horse]\n\n"
                        "1. [image:/api/v1/media/image/unit1_act3_pic1.png] -> making models (Lắp ráp mô hình)\n"
                        "2. [image:/api/v1/media/image/unit1_act3_pic2.png] -> riding a horse (Cưỡi ngựa)",
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );

    await tester.pumpWidget(
      English7App(
        api: fakeApi,
        imageSelector: FakeImageSelector(),
      ),
    );
    await tester.pumpAndSettle();

    // Login
    await tester.enterText(find.byKey(const Key('email-field')), 'student@example.com');
    await tester.enterText(find.byKey(const Key('password-field')), 'password');
    await tester.tap(find.text('Đăng nhập'));
    await tester.pumpAndSettle();

    // Open lesson
    await tester.tap(find.text('Unit 1: Hobbies'));
    await tester.pumpAndSettle();

    // Verify raw answer string is NOT shown as plain text in the prompt
    expect(find.textContaining('-> making models'), findsNothing);

    // Verify word bank box is visible at top
    expect(find.text('making models'), findsOneWidget);
    expect(find.text('riding a horse'), findsOneWidget);

    // Verify images are rendered
    expect(find.byType(Image), findsWidgets);

    // Verify NO ActionChips with answers are pre-displayed under the question
    expect(find.byType(ActionChip), findsNothing);

    // Initially explanation is hidden
    expect(find.textContaining('Lắp ráp mô hình'), findsNothing);

    // Scroll down and enter answer into TextField for question 1
    await tester.drag(find.byType(Scrollable).first, const Offset(0, -250));
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField).first, 'making models');
    await tester.tap(find.widgetWithText(FilledButton, 'Kiểm tra').first);
    await tester.pumpAndSettle();

    // Answer should now be validated
    expect(find.textContaining('Chính xác'), findsOneWidget);
    expect(find.textContaining('Lắp ráp mô hình'), findsOneWidget);
  });

  testWidgets('Activity 4 pronunciation renders authentic table with /ə/ and /ɜː/ and guide tips', (tester) async {
    final fakeApi = FakeStudentApiWithCustomDetail(
      LessonDetail(
        id: 'unit-1',
        unitNumber: 1,
        title: 'Hobbies',
        sections: [
          LessonSection(
            id: 'sec-closerlook1',
            title: 'A CLOSER LOOK 1',
            sectionType: 'lesson',
            position: 2,
            activities: [
              LessonActivity(
                id: 'act-4',
                number: '4',
                activityType: 'pronunciation',
                instruction: 'Listen and repeat. Pay attention to the sounds /ə/ and /ɜː/.',
                fragments: [
                  LessonFragment(
                    id: 'frag-4',
                    pdfPage: 12,
                    printedPage: 11,
                    text: "Pronunciation: /ə/ and /ɜː/\n\n"
                        "| /ə/ | /ɜː/ |\n"
                        "| **a**mazing | l**ear**n |\n"
                        "| yog**a** | s**ur**f |\n"
                        "| c**o**llect | w**or**k |\n"
                        "| col**u**mn | th**ir**teen |",
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );

    await tester.pumpWidget(
      English7App(
        api: fakeApi,
        imageSelector: FakeImageSelector(),
      ),
    );
    await tester.pumpAndSettle();

    // Login
    await tester.enterText(find.byKey(const Key('email-field')), 'student@example.com');
    await tester.enterText(find.byKey(const Key('password-field')), 'password');
    await tester.tap(find.text('Đăng nhập'));
    await tester.pumpAndSettle();

    // Open lesson
    await tester.tap(find.text('Unit 1: Hobbies'));
    await tester.pumpAndSettle();

    // Verify activity header badge
    expect(find.text('HĐ 4'), findsOneWidget);

    // Verify Pronunciation Table headers /ə/ and /ɜː/
    expect(find.text('/ə/'), findsWidgets);
    expect(find.text('/ɜː/'), findsWidgets);

    // Verify words are present
    expect(find.textContaining('mazing'), findsOneWidget);
    expect(find.textContaining('earn'), findsOneWidget);

    // Verify Pronunciation Tips guide box is shown
    expect(find.textContaining('Pronunciation Tips'), findsOneWidget);
  });

  testWidgets('Activity 5 pronunciation exercise renders choice options and interactive feedback', (tester) async {
    final fakeApi = FakeStudentApiWithCustomDetail(
      LessonDetail(
        id: 'unit-1',
        unitNumber: 1,
        title: 'Hobbies',
        sections: [
          LessonSection(
            id: 'sec-closerlook1',
            title: 'A CLOSER LOOK 1',
            sectionType: 'lesson',
            position: 2,
            activities: [
              LessonActivity(
                id: 'act-5',
                number: '5',
                activityType: 'exercise',
                instruction: 'Listen to the sentences and pay attention to the underlined parts. Tick (✓) the appropriate sounds. Practise the sentences. (Track 5)',
                fragments: [
                  LessonFragment(
                    id: 'frag-5',
                    pdfPage: 12,
                    printedPage: 11,
                    text: "![Bảng bài tập tick âm](/api/v1/media/image/unit1_closerlook1_act5_table.png)\n\n"
                        "Options: [/ə/, /ɜ:/]\n\n"
                        "1. My hobby is c<u>o</u>llecting dolls. -> /ə/ (Chữ cái 'o' trong 'collecting' phát âm là /ə/ - /kəˈlektɪŋ/)\n"
                        "2. I go jogging every Th<u>ur</u>sday. -> /ɜ:/ (Nhóm chữ 'ur' trong 'Thursday' phát âm là /ɜː/ - /ˈθɜːzdeɪ/)",
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );

    await tester.pumpWidget(
      English7App(
        api: fakeApi,
        imageSelector: FakeImageSelector(),
      ),
    );
    await tester.pumpAndSettle();

    // Login
    await tester.enterText(find.byKey(const Key('email-field')), 'student@example.com');
    await tester.enterText(find.byKey(const Key('password-field')), 'password');
    await tester.tap(find.text('Đăng nhập'));
    await tester.pumpAndSettle();

    // Open lesson
    await tester.tap(find.text('Unit 1: Hobbies'));
    await tester.pumpAndSettle();

    // Verify raw answers hidden
    expect(find.textContaining('-> /ə/'), findsNothing);

    // Verify sentence prompt is shown
    expect(find.textContaining('My hobby is', findRichText: true), findsOneWidget);

    // Verify options buttons /ə/ and /ɜ:/ exist
    expect(find.widgetWithText(OutlinedButton, '/ə/'), findsWidgets);
    expect(find.widgetWithText(OutlinedButton, '/ɜ:/'), findsWidgets);

    // Scroll down to ensure exercise buttons are in view
    await tester.drag(find.byType(Scrollable).first, const Offset(0, -200));
    await tester.pumpAndSettle();

    // Select wrong choice /ɜ:/ for question 1
    await tester.tap(find.widgetWithText(OutlinedButton, '/ɜ:/').first);
    await tester.pumpAndSettle();

    // Should indicate incorrect and reveal explanation
    expect(find.textContaining('Chưa chính xác'), findsOneWidget);
    expect(find.textContaining('collecting'), findsOneWidget);

    // Now select correct choice /ə/ for question 1
    await tester.tap(find.widgetWithText(OutlinedButton, '/ə/').first);
    await tester.pumpAndSettle();

    // Should indicate correct
    expect(find.textContaining('Chính xác'), findsOneWidget);
  });

  testWidgets('Exercise with reading passage and definition list renders context cards cleanly', (tester) async {
    final fakeApi = FakeStudentApiWithCustomDetail(
      LessonDetail(
        id: 'unit-1',
        unitNumber: 1,
        title: 'Hobbies',
        sections: [
          LessonSection(
            id: 'sec-skills1',
            title: 'SKILLS 1',
            sectionType: 'lesson',
            position: 5,
            activities: [
              LessonActivity(
                id: 'act-2',
                number: '2',
                activityType: 'reading_comprehension',
                instruction: 'Read the text about gardening. Match each word with its meaning.',
                fragments: [
                  LessonFragment(
                    id: 'frag-2',
                    pdfPage: 14,
                    printedPage: 14,
                    text: "[Đoạn văn - Reading Passage: Gardening]\n"
                        "Gardening is one of the oldest outdoor activities.\n\n"
                        "[Column B: Định nghĩa / Nghĩa]\n"
                        "a. doing things with other people\n"
                        "b. plants such as carrots and potatoes\n\n"
                        "Options: [a, b]\n\n"
                        "1. vegetables -> b (vegetables: các loại rau củ)\n"
                        "2. socialise -> a (socialise: giao lưu, hòa nhập)",
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );

    await tester.pumpWidget(
      English7App(
        api: fakeApi,
        imageSelector: FakeImageSelector(),
      ),
    );
    await tester.pumpAndSettle();

    // Login
    await tester.enterText(find.byKey(const Key('email-field')), 'student@example.com');
    await tester.enterText(find.byKey(const Key('password-field')), 'password');
    await tester.tap(find.text('Đăng nhập'));
    await tester.pumpAndSettle();

    // Open lesson
    await tester.tap(find.text('Unit 1: Hobbies'));
    await tester.pumpAndSettle();

    // Verify Reading Passage card is displayed with book icon and text
    expect(find.byIcon(Icons.menu_book_rounded), findsOneWidget);
    expect(find.textContaining('Gardening is one of the oldest outdoor activities.'), findsOneWidget);

    // Verify Column B definition card is displayed with list icon and items
    expect(find.byIcon(Icons.format_list_bulleted_rounded), findsOneWidget);
    expect(find.textContaining('doing things with other people'), findsOneWidget);
    expect(find.textContaining('plants such as carrots and potatoes'), findsOneWidget);

    // Verify interactive exercise questions render
    expect(find.textContaining('vegetables'), findsWidgets);
    expect(find.widgetWithText(OutlinedButton, 'a'), findsWidgets);
    expect(find.widgetWithText(OutlinedButton, 'b'), findsWidgets);

    // Scroll down to bring exercise buttons into view
    await tester.drag(find.byType(Scrollable).first, const Offset(0, -300));
    await tester.pumpAndSettle();

    // Test answering question 1: tap option 'b'
    await tester.tap(find.widgetWithText(OutlinedButton, 'b').first);
    await tester.pumpAndSettle();

    // Verify correct feedback
    expect(find.textContaining('Chính xác'), findsOneWidget);
    expect(find.textContaining('vegetables: các loại rau củ'), findsOneWidget);
  });
}




class FakeStudentApiWithCustomDetail extends FakeStudentApi {
  final LessonDetail detail;
  FakeStudentApiWithCustomDetail(this.detail);

  @override
  Future<LessonDetail> loadLessonDetail(String unitId) async => detail;
}

