import 'dart:async';

import 'package:flutter/material.dart';

import '../../app/student_api.dart';
import '../../widgets/audio_player.dart';

class QuizScreen extends StatefulWidget {
  final StudentApi api;
  const QuizScreen({super.key, required this.api});

  @override
  State<QuizScreen> createState() => _QuizScreenState();
}

class _QuizScreenState extends State<QuizScreen> {
  int _duration = 15;
  String _difficulty = 'adaptive';
  QuizSession? _session;
  QuizResult? _result;
  int _remainingSeconds = 0;
  int _remainingPlays = 2;
  Timer? _timer;

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _start() async {
    final session = await widget.api.createQuiz(
      QuizSetup(_duration, _difficulty),
    );
    if (!mounted) return;
    setState(() {
      _session = session;
      _remainingSeconds = session.durationMinutes * 60;
      _remainingPlays = 2;
      _result = null;
    });
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted || _remainingSeconds <= 1) {
        timer.cancel();
        if (mounted) setState(() => _remainingSeconds = 0);
      } else {
        setState(() => _remainingSeconds--);
      }
    });
  }

  Future<void> _submit() async {
    _timer?.cancel();
    final result = await widget.api.submitQuiz(_session!.id);
    if (mounted) setState(() => _result = result);
  }

  String get _clock {
    final minutes = _remainingSeconds ~/ 60;
    final seconds = _remainingSeconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    if (_result != null) {
      return Center(
        child: Text(
          'Kết quả: ${_result!.correct}/${_result!.total}',
          style: Theme.of(context).textTheme.headlineMedium,
        ),
      );
    }
    if (_session != null) {
      return ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Center(
            child: Text(
              _clock,
              style: Theme.of(context).textTheme.displaySmall,
            ),
          ),
          const SizedBox(height: 16),
          LimitedAudioPlayer(
            remainingPlays: _remainingPlays,
            onPlay: () => setState(() => _remainingPlays--),
          ),
          const SizedBox(height: 16),
          for (final question in _session!.questions)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Text(question.prompt),
              ),
            ),
          const SizedBox(height: 20),
          FilledButton(onPressed: _submit, child: const Text('Nộp bài')),
        ],
      );
    }
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(
          'Tạo bài kiểm tra',
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        const SizedBox(height: 16),
        Wrap(
          spacing: 8,
          children: [
            for (final duration in const [15, 45, 60])
              ChoiceChip(
                label: Text('$duration phút'),
                selected: _duration == duration,
                onSelected: (_) => setState(() => _duration = duration),
              ),
          ],
        ),
        const SizedBox(height: 16),
        DropdownButtonFormField<String>(
          initialValue: _difficulty,
          decoration: const InputDecoration(labelText: 'Độ khó'),
          items: const [
            DropdownMenuItem(value: 'adaptive', child: Text('Thích ứng')),
            DropdownMenuItem(value: 'easy', child: Text('Dễ')),
            DropdownMenuItem(value: 'medium', child: Text('Trung bình')),
            DropdownMenuItem(value: 'hard', child: Text('Khó')),
          ],
          onChanged: (value) => setState(() => _difficulty = value!),
        ),
        const SizedBox(height: 24),
        FilledButton(onPressed: _start, child: const Text('Bắt đầu')),
      ],
    );
  }
}
