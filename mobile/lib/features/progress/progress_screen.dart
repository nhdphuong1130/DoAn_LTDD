import 'package:flutter/material.dart';

import '../../app/student_api.dart';
import '../../app/learning_api.dart';

class ProgressScreen extends StatefulWidget {
  final StudentApi api;
  final bool active;
  const ProgressScreen({super.key, required this.api, required this.active});
  @override
  State<ProgressScreen> createState() => _ProgressScreenState();
}

class _ProgressScreenState extends State<ProgressScreen> {
  StudentProgress? _progress;
  LearningProgress? _learning;
  bool _loading = false;
  bool _failed = false;
  int _request = 0;

  @override
  void initState() {
    super.initState();
    if (widget.active) _load();
  }

  @override
  void didUpdateWidget(covariant ProgressScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.active && (!oldWidget.active || oldWidget.api != widget.api)) {
      _load();
    }
  }

  Future<void> _load() async {
    final request = ++_request;
    setState(() {
      _loading = true;
      _failed = false;
    });
    // Failure of the optional learning summary must not hide quiz results.
    final learningRequest = widget.api
        .loadLearningProgress()
        .then<LearningProgress?>((value) => value, onError: (Object _) => null);
    try {
      final progress = await widget.api.loadProgress();
      final learning = await learningRequest;
      if (!mounted || request != _request) return;
      setState(() {
        _progress = progress;
        _learning = learning;
        _loading = false;
      });
    } catch (_) {
      if (!mounted || request != _request) return;
      setState(() {
        _failed = true;
        _loading = false;
      });
    }
  }

  String _date(DateTime value) {
    final date = value.toLocal();
    String pad(int n) => n.toString().padLeft(2, '0');
    return '${pad(date.day)}/${pad(date.month)}/${date.year} • ${pad(date.hour)}:${pad(date.minute)}';
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_failed) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Không thể tải tiến độ. Vui lòng thử lại.'),
            const SizedBox(height: 12),
            FilledButton(onPressed: _load, child: const Text('Thử lại')),
          ],
        ),
      );
    }
    final progress = _progress;
    if (progress == null) return const SizedBox.shrink();
    final percent = progress.total == 0
        ? 0
        : (100 * progress.correct / progress.total).round();
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  'Tiến độ học tập',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ),
              IconButton(
                onPressed: _load,
                tooltip: 'Làm mới',
                icon: const Icon(Icons.refresh),
              ),
            ],
          ),
          if (_learning case final learning?)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Từ vựng & luyện nói',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 16,
                      runSpacing: 8,
                      children: [
                        Text('${learning.reviewedCards} thẻ đã ôn'),
                        Text('${learning.dueCards} thẻ đến hạn'),
                        Text('${learning.difficultCards} thẻ khó'),
                        Text('${learning.speakingCount} lượt luyện nói'),
                      ],
                    ),
                    if (learning.recentSpeaking.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      const Text(
                        'Luyện nói gần đây · mức khớp bản chép lời, không phải điểm phát âm',
                      ),
                      for (final item in learning.recentSpeaking)
                        ListTile(
                          contentPadding: EdgeInsets.zero,
                          title: Text(item.prompt),
                          subtitle: Text(
                            '${item.transcript}\n${_date(item.createdAt)}',
                          ),
                          trailing: Text('${item.matchPercent.round()}%'),
                        ),
                    ],
                  ],
                ),
              ),
            )
          else
            const Text('Chưa tải được tiến độ từ vựng và luyện nói.'),
          if (progress.completedQuizzes == 0) ...[
            const SizedBox(height: 48),
            const Icon(Icons.insights_outlined, size: 56),
            const SizedBox(height: 16),
            const Center(child: Text('Chưa có bài kiểm tra đã nộp')),
            const SizedBox(height: 8),
            const Text(
              'Hoàn thành và nộp bài ở tab Kiểm tra để theo dõi kết quả tại đây.',
              textAlign: TextAlign.center,
            ),
          ] else ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('${progress.completedQuizzes} bài kiểm tra đã nộp'),
                    const SizedBox(height: 12),
                    Text(
                      '$percent%',
                      style: Theme.of(context).textTheme.headlineLarge,
                    ),
                    const Text('Tỷ lệ trả lời đúng'),
                    const SizedBox(height: 8),
                    LinearProgressIndicator(
                      value: progress.total == 0
                          ? 0
                          : progress.correct / progress.total,
                    ),
                    const SizedBox(height: 8),
                    Text('Đúng ${progress.correct} trên ${progress.total} câu'),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'Lịch sử làm bài',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            for (final item in progress.history)
              Card(
                child: ListTile(
                  leading: const Icon(Icons.assignment_turned_in_outlined),
                  title: Text('${item.correct}/${item.total} câu đúng'),
                  subtitle: Text(_date(item.submittedAt)),
                  trailing: Text(
                    '${item.total == 0 ? 0 : (10 * item.correct / item.total).toStringAsFixed(1)}/10',
                  ),
                ),
              ),
          ],
        ],
      ),
    );
  }
}
