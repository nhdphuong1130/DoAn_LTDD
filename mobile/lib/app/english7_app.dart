import 'package:flutter/material.dart';

import '../features/auth/login_screen.dart';
import '../features/lessons/lesson_screen.dart';
import '../features/progress/progress_screen.dart';
import '../features/quizzes/quiz_screen.dart';
import '../features/tutor/image_selector.dart';
import '../features/tutor/tutor_screen.dart';
import 'student_api.dart';

class English7App extends StatefulWidget {
  final StudentApi api;
  final ImageSelector imageSelector;

  const English7App({
    super.key,
    required this.api,
    required this.imageSelector,
  });

  @override
  State<English7App> createState() => _English7AppState();
}

class _English7AppState extends State<English7App> {
  bool _authenticated = false;

  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'English 7',
    debugShowCheckedModeBanner: false,
    theme: ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xff2563eb)),
      useMaterial3: true,
      inputDecorationTheme: const InputDecorationTheme(
        border: OutlineInputBorder(),
      ),
    ),
    home: _authenticated
        ? StudentShell(api: widget.api, imageSelector: widget.imageSelector)
        : LoginScreen(
            api: widget.api,
            onAuthenticated: () => setState(() => _authenticated = true),
          ),
  );
}

class StudentShell extends StatefulWidget {
  final StudentApi api;
  final ImageSelector imageSelector;
  const StudentShell({
    super.key,
    required this.api,
    required this.imageSelector,
  });

  @override
  State<StudentShell> createState() => _StudentShellState();
}

class _StudentShellState extends State<StudentShell> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final pages = [
      LessonScreen(api: widget.api),
      TutorScreen(api: widget.api, imageSelector: widget.imageSelector),
      QuizScreen(api: widget.api),
      const ProgressScreen(),
    ];
    return Scaffold(
      appBar: AppBar(title: const Text('English 7 Global Success')),
      body: IndexedStack(index: _index, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (value) => setState(() => _index = value),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.menu_book_outlined),
            label: 'Bài học',
          ),
          NavigationDestination(
            icon: Icon(Icons.chat_bubble_outline),
            label: 'Tutor',
          ),
          NavigationDestination(
            icon: Icon(Icons.quiz_outlined),
            label: 'Kiểm tra',
          ),
          NavigationDestination(
            icon: Icon(Icons.insights_outlined),
            label: 'Tiến độ',
          ),
        ],
      ),
    );
  }
}
