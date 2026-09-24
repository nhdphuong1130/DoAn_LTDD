import 'package:flutter/material.dart';

class LimitedAudioPlayer extends StatelessWidget {
  final int remainingPlays;
  final VoidCallback? onPlay;
  final VoidCallback? onPause;
  final String? title;
  final bool isPlaying;

  const LimitedAudioPlayer({
    super.key,
    required this.remainingPlays,
    required this.onPlay,
    this.onPause,
    this.title,
    this.isPlaying = false,
  });

  @override
  Widget build(BuildContext context) => Card(
    elevation: 2,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          if (title != null && title!.isNotEmpty) ...[
            Row(
              children: [
                Icon(
                  Icons.headphones,
                  size: 20,
                  color: Theme.of(context).colorScheme.primary,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    title!,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
          ],
          Row(
            children: [
              IconButton(
                key: const Key('play-audio'),
                onPressed: isPlaying
                    ? onPause
                    : (remainingPlays > 0 ? onPlay : null),
                icon: Icon(
                  isPlaying ? Icons.pause_circle_filled : Icons.play_arrow,
                ),
                color: Theme.of(context).colorScheme.primary,
              ),
              Text(
                'Lượt nghe còn lại: $remainingPlays',
                style: const TextStyle(fontWeight: FontWeight.w500),
              ),
              const Spacer(),
              const Icon(Icons.lock_outline, size: 18, color: Colors.grey),
              const SizedBox(width: 4),
              const Text(
                'Không tua',
                style: TextStyle(color: Colors.grey, fontSize: 13),
              ),
            ],
          ),
        ],
      ),
    ),
  );
}
