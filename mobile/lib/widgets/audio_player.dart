import 'package:flutter/material.dart';

class LimitedAudioPlayer extends StatelessWidget {
  final int remainingPlays;
  final VoidCallback? onPlay;

  const LimitedAudioPlayer({
    super.key,
    required this.remainingPlays,
    required this.onPlay,
  });

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: Row(
        children: [
          IconButton(
            key: const Key('play-audio'),
            onPressed: remainingPlays > 0 ? onPlay : null,
            icon: const Icon(Icons.play_arrow),
          ),
          Text('Lượt nghe còn lại: $remainingPlays'),
          const Spacer(),
          const Icon(Icons.lock_outline, size: 18),
          const SizedBox(width: 4),
          const Text('Không tua'),
        ],
      ),
    ),
  );
}
