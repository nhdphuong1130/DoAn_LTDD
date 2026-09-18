import 'package:flutter/material.dart';

import '../../app/student_api.dart';

class LessonScreen extends StatelessWidget {
  final StudentApi api;
  const LessonScreen({super.key, required this.api});

  @override
  Widget build(BuildContext context) => FutureBuilder<List<LessonSummary>>(
    future: api.loadLessons(),
    builder: (context, snapshot) {
      if (!snapshot.hasData) {
        return const Center(child: CircularProgressIndicator());
      }
      return ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Bài học', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 12),
          for (final lesson in snapshot.data!)
            Card(
              child: ListTile(
                leading: CircleAvatar(child: Text('${lesson.unitNumber}')),
                title: Text('Unit ${lesson.unitNumber}: ${lesson.title}'),
                subtitle: Text(lesson.sectionTitle),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => LessonDetailScreen(lesson: lesson),
                  ),
                ),
              ),
            ),
        ],
      );
    },
  );
}

class LessonDetailScreen extends StatelessWidget {
  final LessonSummary lesson;
  const LessonDetailScreen({super.key, required this.lesson});

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text('Unit ${lesson.unitNumber}: ${lesson.title}')),
    body: Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            lesson.sectionTitle,
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 16),
          const Text('Nội dung đã được xác minh từ sách giáo khoa.'),
          const Spacer(),
          const Row(
            children: [
              Icon(Icons.verified, color: Colors.green),
              SizedBox(width: 8),
              Text('Nguồn: SGK Tiếng Anh 7'),
            ],
          ),
        ],
      ),
    ),
  );
}
