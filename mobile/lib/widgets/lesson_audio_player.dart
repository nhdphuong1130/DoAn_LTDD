import 'dart:async';
import 'package:flutter/material.dart';
import '../services/native_audio_player.dart';

class LessonAudioPlayerWidget extends StatefulWidget {
  final int trackNumber;
  final String title;
  final String audioUrl;
  final String? baseUrl;

  const LessonAudioPlayerWidget({
    super.key,
    required this.trackNumber,
    required this.title,
    required this.audioUrl,
    this.baseUrl,
  });

  @override
  State<LessonAudioPlayerWidget> createState() => _LessonAudioPlayerWidgetState();
}

class _LessonAudioPlayerWidgetState extends State<LessonAudioPlayerWidget> {
  bool _isPlaying = false;
  bool _isLoading = false;
  int _positionMs = 0;
  int _durationMs = 0;
  double _speed = 1.0;
  Timer? _pollTimer;

  String get _resolvedUrl {
    if (widget.audioUrl.startsWith('http://') || widget.audioUrl.startsWith('https://')) {
      return widget.audioUrl;
    }
    const defaultBase = String.fromEnvironment('API_BASE_URL', defaultValue: 'http://10.0.2.2:8000');
    final base = (widget.baseUrl ?? defaultBase).replaceAll(RegExp(r'/+$'), '');
    final path = widget.audioUrl.startsWith('/') ? widget.audioUrl : '/${widget.audioUrl}';
    return '$base$path';
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    if (_isPlaying) {
      NativeAudioPlayer.stop();
    }
    super.dispose();
  }

  void _startPolling() {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(milliseconds: 500), (_) async {
      final status = await NativeAudioPlayer.getStatus();
      if (!mounted) return;
      final isPlaying = status['isPlaying'] as bool? ?? false;
      final position = status['position'] as int? ?? 0;
      final duration = status['duration'] as int? ?? 0;

      setState(() {
        _isPlaying = isPlaying;
        _positionMs = position;
        if (duration > 0) _durationMs = duration;
        if (!isPlaying && position >= _durationMs && _durationMs > 0) {
          _isPlaying = false;
          _pollTimer?.cancel();
        }
      });
    });
  }

  Future<void> _togglePlayPause() async {
    if (_isPlaying) {
      await NativeAudioPlayer.pause();
      setState(() => _isPlaying = false);
      _pollTimer?.cancel();
    } else {
      setState(() => _isLoading = true);
      final success = await NativeAudioPlayer.play(_resolvedUrl);
      if (!mounted) return;
      setState(() {
        _isLoading = false;
        _isPlaying = success;
      });
      if (success) {
        _startPolling();
      }
    }
  }

  Future<void> _seek(int positionMs) async {
    await NativeAudioPlayer.seek(positionMs);
    setState(() => _positionMs = positionMs);
  }

  Future<void> _skip(int deltaMs) async {
    final newPos = (_positionMs + deltaMs).clamp(0, _durationMs > 0 ? _durationMs : 180000);
    await _seek(newPos);
  }

  String _formatTime(int ms) {
    final totalSeconds = (ms / 1000).floor();
    final minutes = totalSeconds ~/ 60;
    final seconds = totalSeconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final primaryColor = theme.colorScheme.primary;

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _isPlaying ? Colors.blue.shade50 : Colors.indigo.shade50.withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: _isPlaying ? primaryColor : Colors.indigo.shade200,
          width: _isPlaying ? 1.5 : 1.0,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Track Header Row
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: _isPlaying ? primaryColor : Colors.indigo.shade700,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      _isPlaying ? Icons.volume_up : Icons.headphones,
                      size: 14,
                      color: Colors.white,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      'Track ${widget.trackNumber}',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  widget.title.isNotEmpty ? widget.title : 'Nghe bài học (Track ${widget.trackNumber})',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: Colors.grey.shade800,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              // Speed toggle
              InkWell(
                onTap: () {
                  setState(() {
                    if (_speed == 1.0) {
                      _speed = 0.8;
                    } else if (_speed == 0.8) {
                      _speed = 1.2;
                    } else {
                      _speed = 1.0;
                    }
                  });
                },
                borderRadius: BorderRadius.circular(8),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: Colors.grey.shade300),
                  ),
                  child: Text(
                    '${_speed}x',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: _speed != 1.0 ? primaryColor : Colors.grey.shade700,
                    ),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),

          // Player controls and timeline
          Row(
            children: [
              // Replay 5s
              IconButton(
                key: const Key('lesson-audio-replay-5'),
                icon: const Icon(Icons.replay_5, size: 20),
                visualDensity: VisualDensity.compact,
                tooltip: 'Lùi 5 giây',
                onPressed: () => _skip(-5000),
              ),

              // Play / Pause Button
              _isLoading
                  ? const SizedBox(
                      width: 40,
                      height: 40,
                      child: Padding(
                        padding: EdgeInsets.all(8.0),
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    )
                  : IconButton(
                      key: const Key('lesson-audio-play-button'),
                      iconSize: 36,
                      color: primaryColor,
                      icon: Icon(_isPlaying ? Icons.pause_circle_filled : Icons.play_circle_filled),
                      onPressed: _togglePlayPause,
                      tooltip: _isPlaying ? 'Tạm dừng' : 'Nghe audio',
                    ),

              // Forward 5s
              IconButton(
                key: const Key('lesson-audio-forward-5'),
                icon: const Icon(Icons.forward_5, size: 20),
                visualDensity: VisualDensity.compact,
                tooltip: 'Tua 5 giây',
                onPressed: () => _skip(5000),
              ),

              // Timeline slider
              Expanded(
                child: Column(
                  children: [
                    SliderTheme(
                      data: SliderTheme.of(context).copyWith(
                        trackHeight: 4,
                        thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6),
                        overlayShape: const RoundSliderOverlayShape(overlayRadius: 12),
                      ),
                      child: Slider(
                        key: const Key('lesson-audio-slider'),
                        min: 0,
                        max: (_durationMs > 0 ? _durationMs : 1000).toDouble(),
                        value: _positionMs.clamp(0, _durationMs > 0 ? _durationMs : 1000).toDouble(),
                        onChanged: (value) {
                          _seek(value.toInt());
                        },
                      ),
                    ),
                  ],
                ),
              ),

              // Time Indicator
              Padding(
                padding: const EdgeInsets.only(right: 4),
                child: Text(
                  '${_formatTime(_positionMs)} / ${_formatTime(_durationMs)}',
                  style: TextStyle(
                    fontSize: 11,
                    fontFamily: 'monospace',
                    color: Colors.grey.shade700,
                  ),
                ),
              ),
            ],
          ),

          // Status subtitle
          if (_isPlaying)
            Padding(
              padding: const EdgeInsets.only(left: 8, top: 2),
              child: Row(
                children: [
                  Icon(Icons.graphic_eq, size: 14, color: primaryColor),
                  const SizedBox(width: 4),
                  Text(
                    'Đang phát bản ghi âm chuẩn SGK Tiếng Anh 7...',
                    style: TextStyle(
                      fontSize: 11,
                      color: primaryColor,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
